# soundcloud-downloader

Paste SoundCloud track, playlist/set or artist links into a local web page and download them all as tagged MP3s with cover art.

Only download tracks the artist offers as free downloads or under Creative Commons.

## Setup (once)

```bash
python -m pip install yt-dlp
```

```bash
winget install -e --id Gyan.FFmpeg
```

## Run

```bash
python downloader.py
```

It opens http://127.0.0.1:8765. Files are saved to `downloads/`. The server only listens on this computer.
