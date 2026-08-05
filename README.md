# Monochrome — YouTube Downloader

A minimalist, black-and-white YouTube downloader. Paste a link, pick a
quality, download. Built with Flask on the backend and `yt-dlp` for the
actual extraction work.

## Setup

```bash
pip install -r requirements.txt
```

Audio-only (MP3) downloads and merging separate video/audio streams into a
single MP4 require **ffmpeg** to be installed and on your `PATH`:

- macOS: `brew install ffmpeg`
- Debian/Ubuntu: `sudo apt install ffmpeg`
- Windows: download from ffmpeg.org and add it to PATH

## Run

```bash
python app.py
```

Then open `http://localhost:5000`.

## How it works

- `POST /api/info` — takes a YouTube URL, returns the video's title,
  uploader, thumbnail, duration, and available quality options.
- `GET /api/download` — takes a URL and a quality selector, downloads the
  video with `yt-dlp` to a temporary directory, streams the file back to
  the browser, then deletes the temp files.

## Usage note

This tool is meant for downloading content you own or otherwise have the
rights to save (your own uploads, Creative Commons/public domain videos,
etc.). Downloading copyrighted videos without permission may violate
YouTube's Terms of Service and copyright law — use responsibly.
