# nekoDL

Simple desktop app to download catgirl images from `nekos.moe`.

## Features
- Choose how many images to download.
- NSFW mode selection:
  - `mixed`
  - `only nsfw`
  - `only sfw`
- Pick a target folder.
- Duplicate prevention using:
  - image IDs
  - original hashes (when available)
  - existing files in target folder
- Stores download history in `.nekodl_manifest.json` inside your target folder.

## Run

```powershell
python app.py
```

## Build Standalone EXE (Windows)
1. Ensure Python is installed and available as `py`.
2. From this folder, run:

```powershell
.\build_exe.bat
```

3. Your standalone app will be at:
   - `dist\nekoDL.exe`

Notes:
- The build includes `app.ico` and the `assets` folder.
- If you pin the exe and later change icons, unpin/repin to refresh taskbar cache.

## Custom App Icon
- Put your icon file at `app.ico` in the project root (same folder as `app.py`).
- The app will load it automatically on startup.
- If `app.ico` is missing or invalid, the default Tk icon is used.

## Social Links
- The top of the app includes clickable GitHub and Discord buttons.
- They open:
  - `https://github.com/f8wq`
  - `https://discord.com/users/1000408727784018032`
- Button logos are loaded from:
  - `assets/github.png`
  - `assets/discord.png`

## Notes
- Uses `https://nekos.moe/api/v1/random/image` for discovery.
- Downloads image content from `https://nekos.moe/image/{id}`.
