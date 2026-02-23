import json
import os
import queue
import threading
import traceback
import urllib.parse
import urllib.request
import ctypes
import sys
import webbrowser
from tkinter import (
    Tk,
    StringVar,
    BooleanVar,
    Text,
    END,
    DISABLED,
    NORMAL,
    PhotoImage,
    filedialog,
    messagebox,
)
from tkinter import ttk

API_RANDOM = "https://nekos.moe/api/v1/random/image"
API_IMAGE_BASE = "https://nekos.moe/image/"
USER_AGENT = "nekoDL/1.0 (+https://nekos.moe)"
MANIFEST_NAME = ".nekodl_manifest.json"
DEFAULT_ICON_NAME = "app.ico"
ASSETS_DIR = "assets"
GITHUB_URL = "https://github.com/f8wq"
DISCORD_URL = "https://discord.com/users/1000408727784018032"
LIGHT_THEME = {
    "bg": "#f2f3f5",
    "panel_bg": "#f2f3f5",
    "text": "#1e1f22",
    "muted_text": "#2b2d31",
    "entry_bg": "#ffffff",
    "button_bg": "#e7e8ea",
    "button_active": "#d9dbdf",
    "accent": "#3b82f6",
    "accent_text": "#ffffff",
    "log_bg": "#ffffff",
    "log_fg": "#1e1f22",
}
DARK_THEME = {
    "bg": "#121418",
    "panel_bg": "#121418",
    "text": "#eceff4",
    "muted_text": "#d8dee9",
    "entry_bg": "#1b1f27",
    "button_bg": "#252a34",
    "button_active": "#323a49",
    "accent": "#4f8cff",
    "accent_text": "#ffffff",
    "log_bg": "#0f131a",
    "log_fg": "#e5e9f0",
}


def resource_path(*parts: str) -> str:
    base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, *parts)


def ext_from_content_type(content_type: str) -> str:
    if not content_type:
        return "jpg"
    clean = content_type.split(";", 1)[0].strip().lower()
    return {
        "image/jpeg": "jpg",
        "image/jpg": "jpg",
        "image/png": "png",
        "image/gif": "gif",
        "image/webp": "webp",
        "image/bmp": "bmp",
    }.get(clean, "jpg")


def fetch_random_images(count: int, mode: str):
    params = {"count": str(count)}
    if mode == "only nsfw":
        params["nsfw"] = "true"
    elif mode == "only sfw":
        params["nsfw"] = "false"

    url = f"{API_RANDOM}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload.get("images", [])


def download_image_bytes(image_id: str):
    url = f"{API_IMAGE_BASE}{image_id}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as response:
        data = response.read()
        content_type = response.headers.get("Content-Type", "")
    return data, content_type


def load_manifest(target_dir: str):
    manifest_path = os.path.join(target_dir, MANIFEST_NAME)
    if not os.path.isfile(manifest_path):
        return {"ids": [], "hashes": []}

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {"ids": [], "hashes": []}
            ids = data.get("ids", [])
            hashes = data.get("hashes", [])
            if not isinstance(ids, list):
                ids = []
            if not isinstance(hashes, list):
                hashes = []
            return {"ids": ids, "hashes": hashes}
    except Exception:
        return {"ids": [], "hashes": []}


def save_manifest(target_dir: str, ids_set, hashes_set):
    manifest_path = os.path.join(target_dir, MANIFEST_NAME)
    temp_path = manifest_path + ".tmp"
    payload = {
        "ids": sorted(ids_set),
        "hashes": sorted(hashes_set),
    }
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    os.replace(temp_path, manifest_path)


def apply_window_icon(root: Tk):
    icon_path = resource_path(DEFAULT_ICON_NAME)
    if os.name == "nt":
        try:
            # Ensures Windows taskbar groups this process under our custom app identity.
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("nekoDL.app")
        except Exception:
            pass
    if not os.path.isfile(icon_path):
        return
    try:
        root.iconbitmap(default=icon_path)
    except Exception:
        # If icon loading fails, keep default Tk icon.
        pass


class NekoDLApp:
    def __init__(self, root: Tk):
        self.root = root
        self.root.title("nekoDL")
        self.root.geometry("700x480")

        self.amount_var = StringVar(value="10")
        self.mode_var = StringVar(value="mixed")
        self.path_var = StringVar(value=os.path.join(os.getcwd(), "downloads"))
        self.dark_mode_var = BooleanVar(value=True)

        self.log_queue = queue.Queue()
        self.github_logo = None
        self.discord_logo = None
        self.style = ttk.Style(self.root)

        self._build_ui()
        self._apply_theme()
        self.root.after(100, self._drain_log_queue)

    def _build_ui(self):
        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill="both", expand=True)

        links_row = ttk.Frame(frame)
        links_row.grid(row=0, column=0, columnspan=3, sticky="e", pady=(0, 8))

        self.github_logo = self._load_logo("github.png")
        self.discord_logo = self._load_logo("discord.png")

        self._make_link_button(links_row, "GitHub", GITHUB_URL, self.github_logo).grid(
            row=0, column=0, padx=(0, 8)
        )
        self._make_link_button(links_row, "Discord", DISCORD_URL, self.discord_logo).grid(
            row=0, column=1
        )
        ttk.Checkbutton(
            links_row,
            text="Dark mode",
            variable=self.dark_mode_var,
            command=self._apply_theme,
        ).grid(row=0, column=2, padx=(12, 0))

        ttk.Label(frame, text="Amount:").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        self.amount_entry = ttk.Entry(frame, textvariable=self.amount_var, width=12)
        self.amount_entry.grid(row=1, column=1, sticky="w", pady=(0, 8))

        ttk.Label(frame, text="Mode:").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        self.mode_combo = ttk.Combobox(
            frame,
            textvariable=self.mode_var,
            values=["mixed", "only nsfw", "only sfw"],
            state="readonly",
            width=18,
        )
        self.mode_combo.grid(row=2, column=1, sticky="w", pady=(0, 8))

        ttk.Label(frame, text="Target path:").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        self.path_entry = ttk.Entry(frame, textvariable=self.path_var, width=58)
        self.path_entry.grid(row=3, column=1, sticky="we", pady=(0, 8))

        self.browse_button = ttk.Button(frame, text="Browse", command=self._choose_path)
        self.browse_button.grid(row=3, column=2, sticky="w", padx=(8, 0), pady=(0, 8))

        self.start_button = ttk.Button(frame, text="Start Download", command=self._start_download)
        self.start_button.grid(row=4, column=0, columnspan=3, sticky="we", pady=(4, 12))

        self.log = Text(frame, height=20, state=DISABLED)
        self.log.grid(row=5, column=0, columnspan=3, sticky="nsew")

        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(5, weight=1)

    def _load_logo(self, filename: str):
        logo_path = resource_path(ASSETS_DIR, filename)
        if not os.path.isfile(logo_path):
            return None
        try:
            logo = PhotoImage(file=logo_path)
        except Exception:
            return None

        # Keep logos compact for top bar.
        shrink_x = max(1, logo.width() // 20)
        shrink_y = max(1, logo.height() // 20)
        return logo.subsample(shrink_x, shrink_y)

    def _make_link_button(self, parent, label: str, url: str, logo):
        kwargs = {"text": label, "command": lambda target=url: webbrowser.open_new_tab(target)}
        if logo is not None:
            kwargs["image"] = logo
            kwargs["compound"] = "left"
        button = ttk.Button(parent, **kwargs)
        button.configure(cursor="hand2")
        return button

    def _apply_theme(self):
        theme = DARK_THEME if self.dark_mode_var.get() else LIGHT_THEME
        self.style.theme_use("clam")

        self.root.configure(bg=theme["bg"])
        self.style.configure("TFrame", background=theme["panel_bg"])
        self.style.configure("TLabel", background=theme["panel_bg"], foreground=theme["text"])
        self.style.configure(
            "TButton",
            background=theme["button_bg"],
            foreground=theme["text"],
            borderwidth=0,
            focusthickness=1,
            focuscolor=theme["accent"],
            padding=(10, 6),
        )
        self.style.map("TButton", background=[("active", theme["button_active"])])
        self.style.configure(
            "TCheckbutton",
            background=theme["panel_bg"],
            foreground=theme["muted_text"],
        )
        self.style.map("TCheckbutton", foreground=[("active", theme["text"])])
        self.style.configure(
            "TEntry",
            fieldbackground=theme["entry_bg"],
            foreground=theme["text"],
        )
        self.style.configure(
            "TCombobox",
            fieldbackground=theme["entry_bg"],
            background=theme["entry_bg"],
            foreground=theme["text"],
            arrowcolor=theme["text"],
        )
        self.style.map(
            "TCombobox",
            fieldbackground=[("readonly", theme["entry_bg"])],
            foreground=[("readonly", theme["text"])],
            selectbackground=[("readonly", theme["accent"])],
            selectforeground=[("readonly", theme["accent_text"])],
        )

        if hasattr(self, "log"):
            self.log.config(
                bg=theme["log_bg"],
                fg=theme["log_fg"],
                insertbackground=theme["log_fg"],
                selectbackground=theme["accent"],
                selectforeground=theme["accent_text"],
                relief="flat",
                highlightthickness=1,
                highlightbackground=theme["button_bg"],
                highlightcolor=theme["accent"],
            )

    def _choose_path(self):
        folder = filedialog.askdirectory(initialdir=self.path_var.get() or os.getcwd())
        if folder:
            self.path_var.set(folder)

    def _append_log(self, msg: str):
        self.log_queue.put(msg)

    def _drain_log_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.log.config(state=NORMAL)
                self.log.insert(END, msg + "\n")
                self.log.see(END)
                self.log.config(state=DISABLED)
        except queue.Empty:
            pass
        self.root.after(100, self._drain_log_queue)

    def _set_busy(self, busy: bool):
        state = DISABLED if busy else NORMAL
        combo_state = DISABLED if busy else "readonly"
        self.amount_entry.config(state=state)
        self.mode_combo.config(state=combo_state)
        self.path_entry.config(state=state)
        self.browse_button.config(state=state)
        self.start_button.config(state=state)

    def _start_download(self):
        amount_text = self.amount_var.get().strip()
        target_path = self.path_var.get().strip()
        mode = self.mode_var.get().strip()

        try:
            amount = int(amount_text)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid amount", "Amount must be a positive integer.")
            return

        if mode not in {"mixed", "only nsfw", "only sfw"}:
            messagebox.showerror("Invalid mode", "Mode must be mixed, only nsfw, or only sfw.")
            return

        if not target_path:
            messagebox.showerror("Invalid path", "Target path cannot be empty.")
            return

        try:
            os.makedirs(target_path, exist_ok=True)
        except OSError as exc:
            messagebox.showerror("Path error", f"Could not create/access target path:\n{exc}")
            return

        self._append_log(f"Starting download: amount={amount}, mode={mode}, path={target_path}")
        self._set_busy(True)

        worker = threading.Thread(
            target=self._download_worker,
            args=(amount, mode, target_path),
            daemon=True,
        )
        worker.start()

    def _download_worker(self, amount: int, mode: str, target_path: str):
        downloaded = 0
        skipped_duplicates = 0
        request_rounds = 0
        max_rounds = max(20, amount * 5)

        manifest = load_manifest(target_path)
        known_ids = set(manifest.get("ids", []))
        known_hashes = set(manifest.get("hashes", []))
        seen_this_run = set()

        try:
            while downloaded < amount and request_rounds < max_rounds:
                need = amount - downloaded
                batch_count = min(50, max(1, need * 2))
                request_rounds += 1

                self._append_log(f"Requesting batch {request_rounds} (count={batch_count})...")
                images = fetch_random_images(batch_count, mode)
                if not images:
                    self._append_log("API returned no images in this batch.")
                    continue

                for image in images:
                    if downloaded >= amount:
                        break

                    image_id = image.get("id")
                    original_hash = image.get("originalHash")
                    if not image_id:
                        continue

                    if (
                        image_id in known_ids
                        or image_id in seen_this_run
                        or (original_hash and original_hash in known_hashes)
                    ):
                        skipped_duplicates += 1
                        continue

                    filename_stem = image_id
                    if any(
                        os.path.exists(os.path.join(target_path, f"{filename_stem}.{candidate_ext}"))
                        for candidate_ext in ("jpg", "jpeg", "png", "gif", "webp", "bmp")
                    ):
                        skipped_duplicates += 1
                        known_ids.add(image_id)
                        if original_hash:
                            known_hashes.add(original_hash)
                        continue

                    try:
                        file_bytes, content_type = download_image_bytes(image_id)
                    except Exception as exc:
                        self._append_log(f"Failed to fetch image {image_id}: {exc}")
                        continue

                    ext = ext_from_content_type(content_type)
                    output_name = f"{filename_stem}.{ext}"
                    output_path = os.path.join(target_path, output_name)

                    try:
                        with open(output_path, "xb") as f:
                            f.write(file_bytes)
                    except FileExistsError:
                        skipped_duplicates += 1
                        continue
                    except OSError as exc:
                        self._append_log(f"Failed to save {output_name}: {exc}")
                        continue

                    downloaded += 1
                    seen_this_run.add(image_id)
                    known_ids.add(image_id)
                    if original_hash:
                        known_hashes.add(original_hash)
                    self._append_log(f"[{downloaded}/{amount}] Saved {output_name}")

            save_manifest(target_path, known_ids, known_hashes)

            if downloaded < amount:
                self._append_log(
                    f"Completed partially: downloaded {downloaded}/{amount}. "
                    f"Skipped duplicates: {skipped_duplicates}."
                )
            else:
                self._append_log(
                    f"Completed: downloaded {downloaded}/{amount}. "
                    f"Skipped duplicates: {skipped_duplicates}."
                )
        except Exception:
            self._append_log("Unhandled error in downloader worker:")
            self._append_log(traceback.format_exc())
        finally:
            self.root.after(0, lambda: self._set_busy(False))


def main():
    root = Tk()
    apply_window_icon(root)
    root.minsize(650, 420)
    app = NekoDLApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
