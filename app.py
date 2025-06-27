import json
import os
import uuid
from datetime import datetime
from pathlib import Path
import subprocess
import threading
from flask import Flask, request, jsonify, send_from_directory, abort
from flask_cors import CORS
from video_processor import create_dash_stream, extract_thumbnail, is_file_allowed, create_debug_mp4

UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

# Debug mode for video processing (saves intermediate files)
DEBUG_VIDEO_PROCESSING = os.getenv("DEBUG_VIDEO_PROCESSING", "false").lower() == "true"

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes




@app.route("/videos", methods=["POST"])
def upload_video():
    if "video" not in request.files or "title" not in request.form:
        return jsonify({"error": "Missing video file or title"}), 400
    file = request.files["video"]
    title = request.form["title"]
    if file.filename == "" or not is_file_allowed(file.filename):
        return jsonify({"error": "Invalid file"}), 400

    video_id = str(uuid.uuid4())
    video_dir = UPLOADS_DIR / video_id
    video_dir.mkdir(parents=True, exist_ok=True)

    original_path = video_dir / f"original{Path(file.filename).suffix}"
    file.save(original_path)

    meta = {
        "id": video_id,
        "title": title,
        "created": datetime.utcnow().isoformat(),
        "status": "pending",
    }
    with open(video_dir / "meta.json", "w") as f:
        json.dump(meta, f)

    def process_video():
        try:
            # Update status to processing
            meta["status"] = "processing"
            with open(video_dir / "meta.json", "w") as f:
                json.dump(meta, f)
            log_path = video_dir / "processing.log"

            # Extract thumbnail at 1 second
            thumb_path = video_dir / "thumbnail.jpg"
            extract_thumbnail(original_path, thumb_path)

            # Create debug MP4 if in debug mode
            if DEBUG_VIDEO_PROCESSING:
                debug_mp4_path = video_dir / "debug_converted.mp4"
                create_debug_mp4(original_path, debug_mp4_path, log_path=log_path)

            create_dash_stream(original_path, video_dir, log_path=log_path, debug=DEBUG_VIDEO_PROCESSING)
            meta["status"] = "done"
            meta["log"] = str(log_path.name)
            meta["thumbnail"] = "thumbnail.jpg"
        except subprocess.CalledProcessError as e:
            meta["status"] = "error"
            meta["error"] = e.stderr
        except Exception as e:
            meta["status"] = "error"
            meta["error"] = str(e)
        with open(video_dir / "meta.json", "w") as f:
            json.dump(meta, f)

    threading.Thread(target=process_video, daemon=True).start()

    return jsonify(meta), 202


@app.route("/videos", methods=["GET"])
def list_videos():
    videos = []
    for video_dir in UPLOADS_DIR.iterdir():
        meta_file = video_dir / "meta.json"
        if meta_file.exists():
            with open(meta_file) as f:
                meta = json.load(f)
                videos.append(meta)
    return jsonify(videos)


@app.route("/videos/<video_id>/info", methods=["GET"])
def video_info(video_id: str):
    meta_file = UPLOADS_DIR / video_id / "meta.json"
    if not meta_file.exists():
        abort(404)
    with open(meta_file) as f:
        meta = json.load(f)
    return jsonify(meta)


@app.route("/videos/<video_id>/log", methods=["GET"])
def get_processing_log(video_id: str):
    video_dir = UPLOADS_DIR / video_id
    log_file = video_dir / "processing.log"
    if not log_file.exists():
        return jsonify({"error": "Log not found"}), 404
    with open(log_file) as f:
        log_content = f.read()
    return jsonify({"log": log_content})


@app.route("/videos/<video_id>/thumbnail", methods=["GET"])
def get_thumbnail(video_id: str):
    video_dir = UPLOADS_DIR / video_id
    thumb_path = video_dir / "thumbnail.jpg"
    if not thumb_path.exists():
        abort(404)
    return send_from_directory(video_dir, "thumbnail.jpg", mimetype="image/jpeg")


@app.route("/videos/<video_id>/<path:filename>", methods=["GET"])
def serve_video_file(video_id: str, filename: str):
    video_dir = UPLOADS_DIR / video_id
    file_path = video_dir / filename
    if not file_path.exists():
        abort(404)
    # Set correct mimetype for manifest and segments
    if filename.endswith(".mpd"):
        mimetype = "application/dash+xml"
    elif filename.endswith(".m4s"):
        mimetype = "video/iso.segment"
    elif filename.endswith(".jpg") or filename.endswith(".jpeg"):
        mimetype = "image/jpeg"
    else:
        mimetype = None
    return send_from_directory(video_dir, filename, mimetype=mimetype)


if __name__ == "__main__":
    app.run(debug=True)
