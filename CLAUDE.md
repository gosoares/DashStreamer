# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Server (Flask/Python)

- **Install dependencies**: `pip install -r requirements.txt`
- **Run server**: `flask run` or `python app.py`
- **Server URL**: <http://127.0.0.1:5000>

### Client (Vue.js)

- **Install dependencies**: `cd client && npm install`
- **Development server**: `cd client && npm run dev`
- **Build for production**: `cd client && npm run build`
- **Preview production build**: `cd client && npm run preview`
- **Client URL**: <http://localhost:5173>

### Presentation (Slidev)

- **Install dependencies**: `cd presentation && pnpm install`
- **Development server**: `cd presentation && pnpm dev`
- **Build presentation**: `cd presentation && pnpm build`
- **Export to PDF**: `cd presentation && pnpm export`
- **Deploy to GitHub Pages**: Manual trigger via GitHub Actions workflow
- **Presentation URL**: <http://localhost:3030>

### System Dependencies

- **ffmpeg**: Required for video processing and DASH conversion
- **ffprobe**: Required for video analysis (usually comes with ffmpeg)

## Project Context

DashStreamer is a **master's degree final project** for the course "Sistemas Gráficos e Multimídia" (Graphics and Multimedia Systems) taught by Prof. Tiago Maritan. The project includes both the implementation and an academic presentation showcasing the technical achievements.

## Architecture Overview

DashStreamer is a full-stack MPEG-DASH video streaming application with these key components:

### Backend (Flask API)

- **app.py**: Main Flask application with video upload, processing, and streaming endpoints
- **video_processor.py**: Video processing utilities with universal aspect ratio support and iPhone video compatibility
- **convert.py**: Standalone video processing script (can be used independently)
- **Background processing**: Videos are processed asynchronously to prevent client timeouts
- **Storage structure**: Each video gets a unique UUID folder in `uploads/` containing all related files

### Frontend (Vue.js SPA)

- **src/services/ApiService.js**: Centralized API client with axios for all server communication
- **Views**: HomeView (video list), UploadView (upload form), PlayerView (DASH player with dashboard)
- **DASH Playback**: Uses dash.js library for adaptive streaming
- **Player Dashboard**: Real-time streaming analytics and visualizations

### Key Features

- **Universal aspect ratio support**: Handles any video aspect ratio (16:9, 4:3, 21:9, 9:16, cinematic ratios)
- **Portrait video support**: Proper handling of rotated mobile videos with correct aspect ratios
- **iPhone video preprocessing**: Automatically cleans problematic metadata streams from iOS-recorded videos
- **Rotation metadata preservation**: Maintains video orientation information for proper display
- **Smart quality ladders**: Generates appropriate bitrate representations based on source resolution and orientation
- **Thumbnail extraction**: Automatically generates thumbnails at 1-second mark
- **Status polling**: Client polls server for processing status updates
- **Responsive video player**: Frontend adapts to different video orientations with height constraints
- **Quality timeline visualization**: Interactive timeline chart showing video quality changes over time
- **Real-time buffer monitoring**: Visual buffer status chart with color-coded health zones
- **Streaming analytics dashboard**: Comprehensive playback metrics and segment tracking

## File Structure

```
/
├── app.py                 # Main Flask server
├── video_processor.py     # Video processing utilities (used by app.py)
├── convert.py            # Standalone video processing script
├── requirements.txt      # Python dependencies
├── uploads/              # Video storage (auto-created)
│   └── <video-id>/      # Per-video folders
│       ├── original.*   # Original uploaded file
│       ├── video.mpd    # DASH manifest
│       ├── video_init_*.m4s     # Initialization segments
│       ├── video_chunk_*.m4s    # Media segments
│       ├── thumbnail.jpg        # Auto-generated thumbnail
│       ├── meta.json    # Video metadata and status
│       ├── processing.log       # Detailed processing logs
│       ├── temp/        # Temporary files (auto-cleaned)
│       └── debug_*      # Debug files (when DEBUG_VIDEO_PROCESSING=true)
├── client/              # Vue.js frontend
│   ├── package.json
│   ├── src/
│   │   ├── services/ApiService.js
│   │   ├── views/       # Main pages
│   │   └── components/  # Vue components
│   └── vite.config.js
└── presentation/        # Slidev presentation for academic project
    ├── package.json
    ├── slides.md        # Presentation slides content
    ├── images/          # Presentation assets
    └── README.md        # Slidev setup instructions
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/videos` | Upload video and title |
| GET | `/videos` | List all videos |
| GET | `/videos/<id>/info` | Get video metadata |
| GET | `/videos/<id>/thumbnail` | Get thumbnail image |
| GET | `/videos/<id>/video.mpd` | Get DASH manifest |
| GET | `/videos/<id>/<file>` | Get DASH segments/files |

## Video Processing Pipeline

1. **Upload & Initialization**:
   - User uploads video via `/videos` endpoint with title
   - Creates unique folder name from title (snake_case format)
   - Generates unique video ID and dedicated storage folder
   - Saves original file and creates initial `meta.json` with "pending" status
   - Starts background processing thread

2. **Background Processing**:
   - **Status Update**: Changes status to "processing" in `meta.json`
   - **Video Analysis**: Uses `ffprobe` to analyze video properties, streams, and metadata
   - **Preprocessing**: Automatic detection and cleaning of problematic videos (iPhone/iOS metadata streams with `mebx` data)
   - **Rotation Detection**: Analyzes Display Matrix side data for portrait videos (-90°, 90°, etc.)
   - **Aspect Ratio Calculation**: Calculates display dimensions accounting for rotation
   - **Quality Ladder Generation**: Creates adaptive representations based on video orientation (portrait vs landscape)
   - **Thumbnail Extraction**: Creates thumbnail at 1-second mark using `ffmpeg`
   - **Debug Mode**: Optionally creates debug MP4 and saves preprocessed files
   - **DASH Conversion**: Generates segments with conflict handling for rotated videos
   - **Cleanup**: Removes temporary files (preserves debug files if enabled)
   - **Final Status**: Updates `meta.json` to "done" or "error" with detailed logging

3. **Status Updates**: Client polls `/videos/<id>/info` for processing status and logs
4. **Playback**: dash.js loads manifest with responsive player sizing

## Player Dashboard Features

The PlayerView includes a comprehensive streaming analytics dashboard with real-time visualizations:

### Quality Timeline Chart
- **Visual timeline**: Interactive chart showing video quality changes over time
- **Color-coded quality levels**: Different colors for each resolution (360p, 720p, 1080p, etc.)
- **Hover tooltips**: Detailed segment information (time, resolution, bitrate, segment name)
- **Responsive design**: Adapts to mobile screens with optimized layout
- **Real-time updates**: Chart updates as new segments are downloaded

### Buffer Status Visualization
- **Real-time buffer chart**: Visual representation of video buffer level
- **Color-coded health zones**: 
  - Red (0-2s): Critical buffer level
  - Yellow (2-5s): Warning buffer level
  - Green (5s+): Good buffer level
- **Historical tracking**: Shows buffer level changes over time
- **Compact layout**: Title and current value on same line for space efficiency

### Segment Download Tracking
- **Download history**: Table showing all downloaded video/audio segments
- **Quality information**: Resolution and bitrate for each segment (formatted as "8 Mbps", "720 kbps")
- **Performance metrics**: Download size, speed, and timing for each segment
- **Filter options**: View all segments, video only, or audio only
- **Real-time updates**: New segments appear as they're downloaded

### Technical Information
- **Current quality**: Real-time resolution, bitrate, and codec information
- **Video properties**: Aspect ratio, frame rate, duration, container type
- **Available qualities**: List of all quality levels in the stream
- **Network stats**: Total data downloaded and current streaming metrics

### Performance Analytics
- **Frame statistics**: Dropped frames, total frames, and drop rate
- **Playback metrics**: Startup time, stall events, quality changes
- **Buffer monitoring**: Video and audio buffer levels
- **Streaming health**: Overall performance indicators

## Important Notes

- **Asynchronous Processing**: Videos are processed in background threads to prevent client timeouts
- **Universal Aspect Ratio Support**: Handles any video orientation automatically (16:9, 4:3, 9:16, etc.)
- **Smart Preprocessing**: iPhone/iOS videos are cleaned to remove problematic `mebx` metadata streams while preserving rotation data
- **Adaptive Quality Ladders**: Portrait videos use width-based targets (1080px, 720px, 540px, 360px), landscape videos use height-based targets
- **Folder Organization**: Each video gets isolated storage with snake_case folder names from titles
- **Comprehensive Logging**: Processing status tracked in `meta.json` with detailed logs in `processing.log`
- **Debug Mode**: Enable via `DEBUG_VIDEO_PROCESSING=true` to save intermediate files and debug MP4
- **Conflict Handling**: Rotated videos use limited representations to avoid DASH conversion conflicts
- **Stream Copy Optimization**: Preprocessing uses stream copying for speed when possible
- **Metadata Preservation**: Maintains rotation and other essential metadata during preprocessing
- **Even Dimension Enforcement**: Ensures width/height are even numbers for codec compatibility
- **Bitrate Mapping**: Quality levels have optimized video/audio bitrate combinations
- **File Extension Support**: Accepts .mov, .mp4, and .mkv formats
- **Error Recovery**: Graceful fallback if preprocessing fails
- **Auto Cleanup**: Temporary files removed automatically (debug files preserved)

## Commit Guidelines

- Commit messages should be single-line only, without detailed information, or attributions

## Debug Commands

- **Enable debug mode**: `export DEBUG_VIDEO_PROCESSING=true`
- **Check processing logs**: View `uploads/<video-id>/processing.log`
- **Inspect debug files**: Check `uploads/<video-id>/debug_*` files
- **Test video properties**: Use `video_processor.get_video_properties()` function