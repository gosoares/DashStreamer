import json
import subprocess
from pathlib import Path
from fractions import Fraction
from ffmpeg_streaming import Formats, Bitrate, Representation, Size
import ffmpeg_streaming


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
            Representation(Size(width, height), Bitrate(video_bitrate * 1000, audio_bitrate * 1000))
        )

    return representations


def preprocess_video_if_needed(input_path: Path, temp_dir: Path = None, debug: bool = False) -> Path:
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

        # For debug mode, save to the same directory as the original
        if debug:
            clean_path = input_path.parent / f"debug_preprocessed_{input_path.name}"
        else:
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


def create_dash_stream(input_path: Path, output_dir: Path, log_path: Path = None, debug: bool = False):
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
        processed_input = preprocess_video_if_needed(input_path, debug=debug)

        # Get video properties
        video_props = get_video_properties(processed_input)

        # Generate representations that maintain the source aspect ratio
        representations = generate_representations(
            video_props["width"], video_props["height"], video_props["aspect_ratio"]
        )

        # Create DASH stream from the (possibly cleaned) input
        if log_path:
            with open(log_path, "a") as logf:
                logf.write(f"\nStarting DASH conversion...\n")
                logf.write(f"Input: {processed_input}\n")
                logf.write(f"Video properties: {video_props}\n")
        
        video = ffmpeg_streaming.input(str(processed_input))
        dash = video.dash(Formats.h264())
        dash.representations(*representations)

        output_file = str(output_dir / "video.mpd")
        
        if log_path:
            with open(log_path, "a") as logf:
                logf.write(f"DASH output file: {output_file}\n")
                logf.write("Starting DASH processing...\n")
        
        # Add progress monitoring if possible
        try:
            dash.output(output_file)
            if log_path:
                with open(log_path, "a") as logf:
                    logf.write("DASH conversion completed successfully\n")
        except Exception as dash_error:
            if log_path:
                with open(log_path, "a") as logf:
                    logf.write(f"DASH conversion failed: {dash_error}\n")
            raise

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

        # Clean up temporary files if we created them (but not debug files)
        if processed_input != input_path and "debug_preprocessed" not in str(processed_input):
            try:
                processed_input.unlink()
                # Also clean up parent temp directory if it's empty
                if processed_input.parent.name == "temp":
                    try:
                        processed_input.parent.rmdir()
                    except OSError:
                        pass  # Directory not empty
            except Exception:
                pass  # Ignore cleanup errors

    except Exception as e:
        if log_path:
            with open(log_path, "a") as logf:
                logf.write(f"\nError during DASH conversion: {e}\n")
        raise


def extract_thumbnail(video_path: Path, output_path: Path, timestamp: str = "00:00:01"):
    """
    Extract a thumbnail from a video at the specified timestamp.

    Args:
        video_path: Path to the input video file
        output_path: Path where the thumbnail should be saved
        timestamp: Timestamp in format HH:MM:SS (default: 00:00:01)
    """
    thumb_cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-ss",
        timestamp,
        "-vframes",
        "1",
        str(output_path),
    ]
    subprocess.run(thumb_cmd, check=True, capture_output=True, text=True)


def create_manual_dash(input_path: Path, output_dir: Path, log_path: Path = None):
    """
    Create DASH files using direct ffmpeg commands for debugging.
    This bypasses the ffmpeg-streaming library to test raw ffmpeg DASH generation.
    
    Args:
        input_path: Path to input video file
        output_dir: Directory to save DASH files
        log_path: Optional path to log file
    """
    try:
        # Preprocess the video if needed
        processed_input = preprocess_video_if_needed(input_path, debug=True)
        
        # Get video properties
        video_props = get_video_properties(processed_input)
        
        if log_path:
            with open(log_path, "a") as logf:
                logf.write(f"\nStarting manual DASH conversion...\n")
                logf.write(f"Input: {processed_input}\n")
                logf.write(f"Video properties: {video_props}\n")
        
        # Generate representations
        representations = generate_representations(
            video_props["width"], video_props["height"], video_props["aspect_ratio"]
        )
        
        # Create DASH files using direct ffmpeg
        output_file = str(output_dir / "manual_video.mpd")
        
        # Build ffmpeg command for DASH
        cmd = [
            "ffmpeg", "-y",
            "-i", str(processed_input)
        ]
        
        # Add video streams for each representation
        for i, rep in enumerate(representations):
            cmd.extend([
                "-map", "0:v:0",
                f"-c:v:{i}", "libx264",
                f"-b:v:{i}", f"{rep.bitrate.video}k",
                f"-s:v:{i}", f"{rep.size.width}x{rep.size.height}",
                f"-profile:v:{i}", "high",
                f"-level:v:{i}", "4.0"
            ])
        
        # Add audio stream
        cmd.extend([
            "-map", "0:a:0",
            "-c:a", "aac",
            "-b:a", "128k"
        ])
        
        # DASH-specific options
        cmd.extend([
            "-f", "dash",
            "-seg_duration", "4",
            "-use_template", "1",
            "-use_timeline", "1",
            "-init_seg_name", "init-$RepresentationID$.$ext$",
            "-media_seg_name", "chunk-$RepresentationID$-$Number%05d$.$ext$",
            output_file
        ])
        
        if log_path:
            with open(log_path, "a") as logf:
                logf.write(f"Manual DASH command: {' '.join(cmd)}\n")
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        if log_path:
            with open(log_path, "a") as logf:
                logf.write("Manual DASH conversion completed successfully\n")
                if result.stderr:
                    logf.write(f"FFmpeg stderr: {result.stderr}\n")
                
    except Exception as e:
        if log_path:
            with open(log_path, "a") as logf:
                logf.write(f"\nError during manual DASH conversion: {e}\n")
        raise


def create_debug_mp4(input_path: Path, output_path: Path, log_path: Path = None):
    """
    Create a simple MP4 conversion for debugging purposes.
    This uses the same preprocessing as DASH but outputs a regular MP4.
    
    Args:
        input_path: Path to input video file
        output_path: Path for output MP4 file
        log_path: Optional path to log file
    """
    try:
        # Preprocess the video if needed
        processed_input = preprocess_video_if_needed(input_path, debug=True)
        
        # Get video properties
        video_props = get_video_properties(processed_input)
        
        # Create a simple MP4 conversion with moderate quality
        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(processed_input),
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            str(output_path)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        if log_path:
            with open(log_path, "a") as logf:
                logf.write(f"\nDebug MP4 created from {input_path}:\n")
                logf.write(f"Source: {video_props['width']}x{video_props['height']} (AR: {video_props['aspect_ratio']})\n")
                logf.write(f"Output: {output_path}\n")
                logf.write(f"Preprocessed input: {processed_input}\n")
                
    except Exception as e:
        if log_path:
            with open(log_path, "a") as logf:
                logf.write(f"\nError during debug MP4 conversion: {e}\n")
        raise


def is_file_allowed(filename: str) -> bool:
    """
    Check if the file has an allowed video extension.

    Args:
        filename: Name of the file to check

    Returns:
        bool: True if file extension is allowed, False otherwise
    """
    return Path(filename).suffix.lower() in {".mov", ".mp4", ".mkv"}
