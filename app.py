import os
import re
import shutil
import tempfile

from flask import Flask, after_this_request, jsonify, render_template, request, send_file
import yt_dlp

app = Flask(__name__)

YOUTUBE_URL_RE = re.compile(
    r"^(https?://)?(www\.|m\.)?(youtube\.com|youtu\.be)/.+$", re.IGNORECASE
)

QUALITY_PRESETS = {
    "best": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
    "2160": "bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/best[height<=2160]",
    "1440": "bestvideo[height<=1440][ext=mp4]+bestaudio[ext=m4a]/best[height<=1440]",
    "1080": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]",
    "720": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]",
    "480": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]",
    "360": "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360]",
    "audio": "bestaudio/best",
}

QUALITY_LABELS = {
    "2160": "2160p · 4K",
    "1440": "1440p · 2K",
    "1080": "1080p",
    "720": "720p",
    "480": "480p",
    "360": "360p",
    "audio": "Audio only · MP3",
}


def is_valid_youtube_url(url: str) -> bool:
    return bool(url) and bool(YOUTUBE_URL_RE.match(url.strip()))


def format_duration(seconds: int) -> str:
    minutes, seconds = divmod(int(seconds or 0), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:d}:{seconds:02d}"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/info", methods=["POST"])
def info():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()

    if not is_valid_youtube_url(url):
        return jsonify({"error": "Please enter a valid YouTube URL."}), 400

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            meta = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as exc:
        return jsonify({"error": f"Could not fetch video info: {exc}"}), 400

    heights = {f.get("height") for f in meta.get("formats", []) if f.get("height")}
    qualities = [q for q in ("2160", "1440", "1080", "720", "480", "360") if int(q) in heights]
    if not qualities:
        qualities = ["1080", "720", "480"]
    qualities.append("audio")

    return jsonify(
        {
            "title": meta.get("title"),
            "uploader": meta.get("uploader"),
            "thumbnail": meta.get("thumbnail"),
            "duration": format_duration(meta.get("duration")),
            "qualities": [{"value": q, "label": QUALITY_LABELS[q]} for q in qualities],
        }
    )


@app.route("/api/download")
def download():
    url = (request.args.get("url") or "").strip()
    quality = (request.args.get("quality") or "best").strip()

    if not is_valid_youtube_url(url):
        return jsonify({"error": "Please enter a valid YouTube URL."}), 400

    format_selector = QUALITY_PRESETS.get(quality, QUALITY_PRESETS["best"])
    tmp_dir = tempfile.mkdtemp(prefix="ytdl_")

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "format": format_selector,
        "outtmpl": os.path.join(tmp_dir, "%(title).100s.%(ext)s"),
    }

    if quality == "audio":
        ydl_opts["postprocessors"] = [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
        ]
    else:
        ydl_opts["merge_output_format"] = "mp4"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)
    except yt_dlp.utils.DownloadError as exc:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return jsonify({"error": f"Download failed: {exc}"}), 400

    files = os.listdir(tmp_dir)
    if not files:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return jsonify({"error": "Download failed: no output file was produced."}), 500

    file_path = os.path.join(tmp_dir, files[0])

    @after_this_request
    def cleanup(response):
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return response

    return send_file(file_path, as_attachment=True, download_name=files[0])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
