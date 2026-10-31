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

**Download** saves SoundCloud's stream copy (about 128-160 kbps).

**Find download links** scans the same links without downloading audio and lists the best full-quality source for each track:

- `gate`: a Hypeddit, ToneDen, Dropbox or similar link from the track's buy button or description. These usually have the 320 kbps or WAV file. Use **Open next gate link** to step through them and complete each gate yourself.
- `soundcloud button`: the artist turned on SoundCloud's own download button. Download it from the track page while logged in.
- `creative commons`, `buy` (Bandcamp, Beatport...), `other link`, or `stream only`.
