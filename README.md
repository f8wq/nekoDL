# nekoDL

Simple desktop app to download catgirl images from `nekos.moe`.

## Features
- Choose how many images to download.
- NSFW mode selection:
  - `mixed`
  - `only nsfw`
  - `only sfw`
- Pick a target folder.
- Toggle dark mode on/off from the top bar.
- Duplicate prevention using:
  - image IDs
  - original hashes (when available)
  - existing files in target folder
- Stores download history in `.nekodl_manifest.json` inside your target folder.

## Notes
- Uses `https://nekos.moe/api/v1/random/image` for discovery.
- Downloads image content from `https://nekos.moe/image/{id}`.
