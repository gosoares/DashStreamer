import json
import subprocess
from pathlib import Path
from fractions import Fraction
from ffmpeg_streaming import Formats, Bitrate, Representation, Size
import ffmpeg_streaming


def get_video_properties(video_path: Path):
    """
    Get video properties including width, height, aspect ratio, and rotation.

    Args:
        video_path: Path to the video file

    Returns:
        dict: Video properties including width, height, aspect_ratio, rotation
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

        # Check for rotation metadata
        rotation = 0
        if "side_data_list" in stream:
            for side_data in stream["side_data_list"]:
                if side_data.get("side_data_type") == "Display Matrix":
                    rotation = side_data.get("rotation", 0)
                    break

        # Apply rotation to dimensions for display aspect ratio
        if abs(rotation) == 90 or abs(rotation) == 270:
            # Portrait orientation - swap dimensions for aspect ratio calculation
            display_width = height
            display_height = width
        else:
            # Landscape orientation - use original dimensions
            display_width = width
            display_height = height

        # Calculate aspect ratio based on display orientation
        aspect_ratio = Fraction(display_width, display_height)

        return {
            "width": width,
            "height": height,
            "display_width": display_width,
            "display_height": display_height,
            "aspect_ratio": aspect_ratio,
            "aspect_ratio_decimal": float(aspect_ratio),
            "rotation": rotation,
        }

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to get video properties: {e}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse ffprobe output: {e}")


def generate_representations(
    display_width: int, display_height: int, aspect_ratio: Fraction
):
    """
    Generate video representations that maintain the display aspect ratio.

    Args:
        display_width: Display video width (after rotation)
        display_height: Display video height (after rotation)
        aspect_ratio: Display aspect ratio as Fraction

    Returns:
        list: List of Representation objects
    """
    is_portrait = display_height > display_width
    max_quality = display_width if is_portrait else display_height
    target_qualities = [
        q for q in [2160, 1440, 1080, 720, 480, 360, 240, 144] if q <= max_quality
    ]

    resolutions = []
    if is_portrait:
        # For portrait videos, we use target widths instead of heights
        for target_width in target_qualities:
            target_height = int(target_width / aspect_ratio)
            resolutions.append((target_width, target_height))
    else:
        # For landscape videos, we use traditional height-based approach
        for target_height in target_qualities:
            target_width = int(target_height * aspect_ratio)
            resolutions.append((target_width, target_height))

    # (video, audio) bitrates based on resolution
    bitrate_map = {
        2160: (35840, 320),
        1440: (16384, 320),
        1080: (8192, 320),
        720: (5120, 320),
        480: (2560, 192),
        360: (1024, 128),
        240: (700, 94),
        144: (340, 64),
    }

    representations = []
    for resolution in resolutions:
        # Calculate width maintaining exact aspect ratio
        width = resolution[0]
        height = resolution[1]
        quality = width if is_portrait else height

        # Ensure both dimensions are even (required for many codecs)
        if width % 2 != 0:
            width += 1
        if height % 2 != 0:
            height += 1

        bitrates = bitrate_map[quality]

        representations.append(
            Representation(
                Size(width, height), Bitrate(bitrates[0] * 1024, bitrates[1] * 1024)
            )
        )

    return representations


def preprocess_video_if_needed(
    input_path: Path, temp_dir: Path = None, debug: bool = False
) -> Path:
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

        # Copy only video and audio streams while preserving metadata
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
                "-map_metadata",
                "0",  # Preserve metadata
                "-movflags",
                "use_metadata_tags",  # Preserve mov/mp4 metadata
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


def create_dash_stream(
    input_path: Path, output_dir: Path, log_path: Path = None, debug: bool = False
):
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

        # Generate representations that maintain the display aspect ratio
        representations = generate_representations(
            video_props["display_width"],
            video_props["display_height"],
            video_props["aspect_ratio"],
        )

        # Create DASH stream from the (possibly cleaned) input
        if log_path:
            with open(log_path, "a") as logf:
                logf.write("\nStarting DASH conversion...\n")
                logf.write(f"Input: {processed_input}\n")
                logf.write(f"Video properties: {video_props}\n")
                logf.write(f"Generated {len(representations)} representations\n")

        video = ffmpeg_streaming.input(str(processed_input))
        dash = video.dash(
            Formats.h264(),
            seg_duration=4,
            use_template=1,
            use_timeline=0,
            force_key_frames="expr:gte(t,n_forced*1)",
            init_seg_name="init_$RepresentationID$.m4s",
            media_seg_name="chunk_$RepresentationID$_$Number%03d$.m4s",
        )

        # For portrait videos, we might need to handle aspect ratios more carefully
        # Let's try adding some tolerance or using fewer representations initially
        if video_props.get("rotation", 0) != 0:
            # For rotated videos, let's use fewer representations to avoid conflicts
            limited_reps = representations[:2]  # Use only top 2 quality levels
            if log_path:
                with open(log_path, "a") as logf:
                    logf.write(
                        f"Using limited representations ({len(limited_reps)}) for rotated video\n"
                    )
            dash.representations(*limited_reps)
        else:
            dash.representations(*representations)

        output_file = str(output_dir / "video.mpd")

        if log_path:
            with open(log_path, "a") as logf:
                logf.write(f"DASH output file: {output_file}\n")
                logf.write("Starting DASH processing...\n")

        # Add progress monitoring if possible
        try:
            if log_path:
                with open(log_path, "a") as logf:
                    logf.write("About to start DASH output generation...\n")
                    if video_props.get("rotation", 0) != 0:
                        active_reps = limited_reps
                    else:
                        active_reps = representations

                    for i, rep in enumerate(active_reps):
                        logf.write(
                            f"  Rep {i}: {rep.size.width}x{rep.size.height} (AR: {rep.size.width / rep.size.height:.4f})\n"
                        )

            dash.output(output_file)
            if log_path:
                with open(log_path, "a") as logf:
                    logf.write("DASH conversion completed successfully\n")
        except Exception as dash_error:
            if log_path:
                with open(log_path, "a") as logf:
                    logf.write(f"DASH conversion failed: {dash_error}\n")
                    logf.write(f"Error type: {type(dash_error)}\n")
            raise

        if log_path:
            with open(log_path, "a") as logf:
                logf.write(f"\nDASH files generated from {input_path}:\n")
                logf.write(
                    f"Physical: {video_props['width']}x{video_props['height']}\n"
                )
                logf.write(
                    f"Display: {video_props['display_width']}x{video_props['display_height']} (AR: {video_props['aspect_ratio']})\n"
                )
                if video_props["rotation"] != 0:
                    logf.write(f"Rotation: {video_props['rotation']}°\n")
                logf.write("Representations:\n")
                for rep in representations:
                    logf.write(
                        f"  {rep.size.width}x{rep.size.height} @ {rep.bitrate.video}kbps\n"
                    )
                logf.write("Generated files:\n")
                for f in sorted(output_dir.iterdir()):
                    logf.write(f"  {f.name}\n")

        # Clean up temporary files if we created them (but not debug files)
        if processed_input != input_path and "debug_preprocessed" not in str(
            processed_input
        ):
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
            "-i",
            str(processed_input),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            str(output_path),
        ]

        subprocess.run(cmd, check=True, capture_output=True, text=True)

        if log_path:
            with open(log_path, "a") as logf:
                logf.write(f"\nDebug MP4 created from {input_path}:\n")
                logf.write(
                    f"Source: {video_props['width']}x{video_props['height']} (AR: {video_props['aspect_ratio']})\n"
                )
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
