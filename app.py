import json
import uuid
from datetime import datetime
from pathlib import Path
from fractions import Fraction
from flask import Flask, request, jsonify, send_from_directory, abort
from flask_cors import CORS
from ffmpeg_streaming import Formats, Bitrate, Representation, Size
import ffmpeg_streaming
import subprocess
import threading

UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes


def is_file_allowed(filename):
    return Path(filename).suffix.lower() in {".mov", ".mp4", ".mkv"}


def get_video_properties(video_path: Path):
    """
    Get video properties including width, height, and aspect ratio.

    Args:
        video_path: Path to the video file

    Returns:
        dict: Video properties including width, height, aspect_ratio
    """
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_streams",
        "-select_streams",
        "v:0",
        str(video_path),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)

        if not data.get("streams"):
            raise ValueError("No video stream found in the file")

        stream = data["streams"][0]
        width = int(stream["width"])
        height = int(stream["height"])

        # Calculate aspect ratio as a simplified fraction
        aspect_ratio = Fraction(width, height)

        return {
            "width": width,
            "height": height,
            "aspect_ratio": aspect_ratio,
            "aspect_ratio_decimal": float(aspect_ratio),
        }

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to get video properties: {e}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse ffprobe output: {e}")


def generate_representations(
    source_width: int, source_height: int, aspect_ratio: Fraction
):
    """
    Generate video representations that maintain the source aspect ratio.

    Args:
        source_width: Original video width
        source_height: Original video height
        aspect_ratio: Source aspect ratio as Fraction

    Returns:
        list: List of Representation objects
    """
    # Define target heights for different quality levels
    # We'll calculate width to maintain exact aspect ratio
    target_heights = []

    # Only include heights that are smaller than or equal to source
    if source_height >= 1080:
        target_heights.append(1080)
    if source_height >= 720:
        target_heights.append(720)
    if source_height >= 540:
        target_heights.append(540)
    if source_height >= 360:
        target_heights.append(360)

    # If source is smaller than 360p, just use the source resolution
    if not target_heights:
        target_heights.append(source_height)

    representations = []

    # Bitrate mapping based on resolution (rough estimates)
    bitrate_map = {
        1080: 3000,
        720: 1500,
        540: 800,
        360: 400,
    }

    for height in target_heights:
        # Calculate width maintaining exact aspect ratio
        width = int(height * aspect_ratio)

        # Ensure width is even (required for many codecs)
        if width % 2 != 0:
            width += 1

        # Recalculate height if width was adjusted to ensure exact aspect ratio
        height = int(width / aspect_ratio)
        if height % 2 != 0:
            height += 1
            width = int(height * aspect_ratio)
            if width % 2 != 0:
                width += 1

        # Get appropriate bitrate, or calculate based on resolution
        video_bitrate = bitrate_map.get(height, max(200, int(width * height * 0.001)))
        audio_bitrate = 128 if height >= 720 else 96

        representations.append(
            Representation(Size(width, height), Bitrate(video_bitrate, audio_bitrate))
        )

    return representations


def preprocess_video_if_needed(input_path: Path, temp_dir: Path = None) -> Path:
    """
    Preprocess video files that may have problematic metadata streams.
    Returns the path to a clean video file (either the original or a cleaned version).

    Args:
        input_path: Path to the input video file
        temp_dir: Directory for temporary files (optional)

    Returns:
        Path to the video file to use (original or cleaned)
    """
    try:
        # Get stream information
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_streams",
                str(input_path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        streams_info = json.loads(result.stdout)

        # Check if there are problematic metadata streams
        has_metadata_streams = any(
            stream.get("codec_type") == "data"
            and stream.get("codec_tag_string") == "mebx"
            for stream in streams_info["streams"]
        )

        if not has_metadata_streams:
            return input_path

        # Create a temporary cleaned file
        if temp_dir is None:
            temp_dir = input_path.parent / "temp"
        temp_dir.mkdir(exist_ok=True)

        clean_path = temp_dir / f"cleaned_{input_path.name}"

        # Copy only video and audio streams
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(input_path),
                "-map",
                "0:v:0",
                "-map",
                "0:a:0",
                "-c",
                "copy",  # Copy streams without re-encoding for speed
                str(clean_path),
            ],
            check=True,
            capture_output=True,
        )

        return clean_path

    except subprocess.CalledProcessError:
        return input_path
    except Exception:
        return input_path


def create_dash_stream(input_path: Path, output_dir: Path, log_path: Path = None):
    """
    Create DASH streaming files from input video.
    Automatically detects video aspect ratio and generates appropriate representations.

    Args:
        input_path: Path to input video file
        output_dir: Directory to save DASH files
        log_path: Optional path to log file
    """
    try:
        # Preprocess the video if needed to handle metadata streams
        processed_input = preprocess_video_if_needed(input_path)

        # Get video properties
        video_props = get_video_properties(processed_input)

        # Generate representations that maintain the source aspect ratio
        representations = generate_representations(
            video_props["width"], video_props["height"], video_props["aspect_ratio"]
        )

        # Create DASH stream from the (possibly cleaned) input
        video = ffmpeg_streaming.input(str(processed_input))
        dash = video.dash(Formats.h264())
        dash.representations(*representations)

        output_file = str(output_dir / "manifest.mpd")
        dash.output(output_file)

        if log_path:
            with open(log_path, "a") as logf:
                logf.write(f"\nDASH files generated from {input_path}:\n")
                logf.write(
                    f"Source: {video_props['width']}x{video_props['height']} (AR: {video_props['aspect_ratio']})\n"
                )
                logf.write("Representations:\n")
                for rep in representations:
                    logf.write(
                        f"  {rep.size.width}x{rep.size.height} @ {rep.bitrate.video}kbps\n"
                    )
                logf.write("Generated files:\n")
                for f in sorted(output_dir.iterdir()):
                    logf.write(f"  {f.name}\n")

        # Clean up temporary file if we created one
        if processed_input != input_path:
            try:
                processed_input.unlink()
                processed_input.parent.rmdir()  # Remove temp dir if empty
            except Exception:
                pass  # Ignore cleanup errors

    except Exception as e:
        if log_path:
            with open(log_path, "a") as logf:
                logf.write(f"\nError during DASH conversion: {e}\n")
        raise


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
            thumb_cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(original_path),
                "-ss",
                "00:00:01",
                "-vframes",
                "1",
                str(thumb_path),
            ]
            subprocess.run(thumb_cmd, check=True, capture_output=True, text=True)

            create_dash_stream(original_path, video_dir, log_path=log_path)
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
