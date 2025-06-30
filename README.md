# DashStreamer Documentation

## Table of Contents

- [Overview](#overview)
- [Technology Stack](#technology-stack)
- [Server (Flask API)](#server-flask-api)
  - [Architecture & Design](#architecture--design)
  - [API Endpoints](#api-endpoints)
  - [Video Processing Pipeline](#video-processing-pipeline)
  - [File Structure](#file-structure)
- [Client (Vue.js App)](#client-vuejs-app)
  - [Architecture & Design](#architecture--design-1)
  - [Pages & Components](#pages--components)
  - [API Integration](#api-integration)
  - [DASH Playback](#dash-playback)
- [Development & Setup](#development--setup)
- [Design Choices](#design-choices)
- [Known Issues & Future Improvements](#known-issues--future-improvements)

---

## Overview

DashStreamer is a full-stack web application for uploading, processing, and streaming videos using MPEG-DASH. This project was developed as a **master's degree final project** for the course "Sistemas Gráficos e Multimídia" (Graphics and Multimedia Systems) taught by Prof. Tiago Maritan.

The application features a Flask backend for video processing and API, a Vue.js frontend for a modern user interface, and includes an academic presentation built with Slidev to showcase the technical implementation and achievements.

**📑 Academic Presentation:** [View Slides](https://gosoares.github.io/DashStreamer/)

---

## Technology Stack

**Server:**

- Python 3.13+
- Flask
- Flask-CORS
- ffmpeg (system dependency)
- python-ffmpeg-video-streaming
- Enhanced video processing with universal aspect ratio support

**Key Improvements:**

- **Robust DASH Conversion:** Supports any video aspect ratio automatically
- **iPhone Video Support:** Handles complex metadata streams in iOS-recorded videos
- **Smart Quality Ladders:** Generates optimal bitrate representations for each source
- **Preprocessing Pipeline:** Automatically cleans problematic video formats

**Client:**

- Vue.js 3 (Vite)
- Axios
- dash.js (MPEG-DASH player)
- Modern CSS (no Tailwind)

**Presentation:**

- Slidev (Vue-based presentation framework)
- Markdown-driven slides
- Interactive web presentation

---

## Server (Flask API)

### Architecture & Design

- **Asynchronous Processing:** Video uploads are processed in a background thread to avoid client timeouts.
- **DASH Packaging:** Uses ffmpeg and python-ffmpeg-video-streaming to generate DASH segments and manifest.
- **Thumbnails:** A thumbnail is extracted from each video for use in the frontend.
- **Metadata:** Each video has a `meta.json` file with status, title, creation date, and thumbnail.
- **CORS:** Enabled for all endpoints to allow cross-origin requests from the client.

### API Endpoints

| Method | Endpoint                                      | Description                                      |
|--------|-----------------------------------------------|--------------------------------------------------|
| POST   | `/videos`                                     | Upload a video file and title. Returns video ID.  |
| GET    | `/videos`                                     | List all videos and their metadata.              |
| GET    | `/videos/<video_id>/info`                     | Get metadata for a specific video.               |
| GET    | `/videos/<video_id>/thumbnail`                | Get the thumbnail image for a video.             |
| GET    | `/videos/<video_id>/log`                      | Get the processing log for a video.              |
| GET    | `/videos/<video_id>/video.mpd`             | Get the MPEG-DASH manifest for a video.          |
| GET    | `/videos/<video_id>/<segment/init file>`      | Get DASH segments or init files (m4s, mpd, etc.) |

#### Example: Video Metadata (`meta.json`)

```json
{
  "id": "2772d902-be72-476d-9f27-944f14fac146",
  "title": "My Video",
  "created": "2025-06-20T18:07:57.123456",
  "status": "done",
  "thumbnail": "thumbnail.jpg",
  "log": "processing.log"
}
```

### Video Processing Pipeline

The video processing pipeline provides comprehensive support for all video formats with robust error handling and optimal quality generation:

#### Phase 1: Upload & Initialization
1. **Video Upload:** User uploads video file and title via `/videos` endpoint
2. **Folder Creation:** Creates snake_case folder name from title with uniqueness guarantee
3. **File Storage:** Saves original file and creates initial `meta.json` with "pending" status
4. **Background Thread:** Processing starts asynchronously to prevent client timeouts

#### Phase 2: Video Analysis & Preprocessing
1. **Stream Analysis:**
   - Uses `ffprobe` to analyze all streams and metadata in the video file
   - Detects problematic metadata streams (iPhone/iOS videos with `mebx` data streams)
   - Identifies rotation metadata from Display Matrix side data

2. **Video Property Extraction:**
   - Physical dimensions (width × height as stored in file)
   - Rotation metadata (-90°, 90°, 180°, etc.)
   - Display dimensions (accounting for rotation)
   - Aspect ratio calculation for proper display (e.g., 9:16 for portrait)

3. **Smart Preprocessing (when needed):**
   - **Metadata Stream Cleaning:** Removes problematic `mebx` data streams from iPhone/iOS videos
   - **Stream Preservation:** Maps only video/audio streams using `-map 0:v:0 -map 0:a:0`
   - **Stream Copy Optimization:** Uses `-c copy` for fast processing without re-encoding
   - **Metadata Preservation:** Maintains rotation data with `-map_metadata 0` and `-movflags use_metadata_tags`
   - **Debug Files:** Optionally saves preprocessed files as `debug_preprocessed_*`

#### Phase 3: Adaptive Quality Ladder Generation
1. **Orientation-Based Approach:**
   - **Portrait Videos (height > width):** Uses target widths [2160, 1440, 1080, 720, 480, 360, 240, 144] and calculates heights
   - **Landscape Videos (width ≥ height):** Uses target heights and calculates widths
   - **Aspect Ratio Preservation:** Maintains exact source aspect ratio for all representations

2. **Quality Level Examples:**
   - **Portrait (9:16):** 1080×1920, 720×1280, 540×960, 360×640
   - **Landscape (16:9):** 1920×1080, 1280×720, 960×540, 640×360
   - **Even Dimension Enforcement:** Adjusts width/height to even numbers for codec compatibility

3. **Bitrate Optimization:**
   - **Video Bitrates:** Mapped by quality level (35840k for 2160p down to 340k for 144p)
   - **Audio Bitrates:** Optimized per resolution (320k for HD, 128k for SD, 64k for lowest)
   - **Library Scaling:** Values multiplied by 1024 for ffmpeg-streaming compatibility

#### Phase 4: DASH Stream Creation
1. **DASH Configuration:**
   - Uses `python-ffmpeg-video-streaming` library with H.264 codec
   - 4-second segment duration with template-based naming
   - Forced keyframes for optimal seeking: `init_$RepresentationID$.m4s`, `chunk_$RepresentationID$_$Number%03d$.m4s`

2. **Rotation Conflict Handling:**
   - **Detection:** Monitors for "Conflicting stream aspect ratios" errors in rotated videos
   - **Fallback:** Uses limited representations (top 2 quality levels) for rotated videos
   - **Detailed Logging:** Records aspect ratios and representation details for debugging

3. **Output Generation:**
   - **Manifest File:** `video.mpd` describing all available representations
   - **Initialization Segments:** Per-quality init files with codec information
   - **Media Segments:** Chunked video/audio data for adaptive streaming

#### Phase 5: Thumbnail Creation & Finalization
1. **Thumbnail Extraction:**
   - Extracted at 1-second mark using `ffmpeg -ss 00:00:01 -vframes 1`
   - Saved as `thumbnail.jpg` in video folder
   - Handles all video formats and orientations

2. **Debug Mode Features:**
   - **Debug MP4:** Creates `debug_converted.mp4` with same preprocessing pipeline
   - **File Preservation:** Saves `debug_preprocessed_*` files for inspection
   - **Enhanced Logging:** Detailed processing steps and file inventory

3. **Cleanup & Status Update:**
   - **Temporary File Cleanup:** Removes processing artifacts (preserves debug files)
   - **Status Finalization:** Updates `meta.json` to "done" or "error"
   - **Comprehensive Logging:** Records all processing details in `processing.log`

#### Advanced Features

- **Universal Format Support:** Handles .mov, .mp4, .mkv with any aspect ratio
- **Intelligent Preprocessing:** Automatic detection and cleaning of problematic formats
- **Metadata Preservation:** Maintains rotation and essential video metadata
- **Error Recovery:** Graceful fallback when preprocessing fails
- **Performance Optimization:** Stream copying when possible, minimal re-encoding

### File Structure

```
uploads/
  <video_id>/
    original.<ext>              # Original uploaded video file
    video.mpd                   # DASH manifest file
    video_init_*.m4s           # Initialization segments for each quality
    video_chunk_*_*.m4s        # Media segments (quality_chunk)
    thumbnail.jpg              # Video thumbnail (extracted at 1s)
    meta.json                  # Video metadata and status
    processing.log             # Detailed processing logs
    temp/                      # Temporary files during processing
      cleaned_original.<ext>   # Preprocessed video (if needed)
    
    # Debug mode files (when DEBUG_VIDEO_PROCESSING=true):
    debug_preprocessed_*       # Preprocessed video for inspection
    debug_converted.mp4        # Simple MP4 conversion for testing
```

#### File Details

- **`original.<ext>`**: Unmodified uploaded file (preserves original format)
- **`video.mpd`**: MPEG-DASH manifest describing available quality levels
- **`video_init_*.m4s`**: Initialization segments containing codec info for each representation
- **`video_chunk_*_*.m4s`**: Media segments containing actual video/audio data
- **`thumbnail.jpg`**: Auto-generated thumbnail for UI display
- **`meta.json`**: Status, title, creation date, and processing information
- **`processing.log`**: Comprehensive log of all processing steps and errors
- **`temp/`**: Temporary directory for intermediate files (auto-cleaned)

#### Debug Files (Optional)

When debug mode is enabled via `DEBUG_VIDEO_PROCESSING=true`:
- **`debug_preprocessed_*`**: Shows result of metadata cleaning step
- **`debug_converted.mp4`**: Simple MP4 conversion using same preprocessing pipeline

---

## Client (Vue.js App)

### Architecture & Design

- **SPA:** Built with Vue 3 and Vite for fast development and hot reload.
- **API Service:** Centralized Axios service for all API calls.
- **Routing:** Vue Router for navigation between Home, Upload, and Player pages.
- **Modern CSS:** Custom CSS for a clean, responsive UI.

### Pages & Components

- **HomeView:** Lists all videos with thumbnails, titles, and status badges. Clicking a video opens the player.
- **UploadView:** Form to upload a video and title. Shows upload progress and processing status.
- **PlayerView:** Streams the video using dash.js with comprehensive streaming analytics dashboard.
- **QualityTimelineChart:** Interactive timeline visualization showing video quality changes over time.
- **BufferStats:** Real-time buffer level chart with color-coded health zones.
- **SegmentDownloadPanel:** Table tracking all downloaded segments with performance metrics.
- **TechnicalInfo & PerformanceStats:** Detailed streaming metrics and video information.
- **ApiService.js:** Handles all HTTP requests to the Flask API.

### API Integration

- All API URLs are configured via `.env` (`VITE_API_URL`).
- The client polls the `/info` endpoint after upload to track processing.
- Thumbnails and manifests are fetched using the video ID.

### DASH Playback

- **dash.js Integration:** Modern MPEG-DASH player for adaptive streaming
- **Portrait Video Support:** Responsive player with height constraints for mobile videos
- **Aspect Ratio Preservation:** Maintains correct video proportions for all orientations
- **Responsive Design:** 
  - Desktop: Max height 70% of viewport
  - Mobile: Max height 60% of viewport
  - Mobile Portrait: Max height 50% of viewport
- **Auto-scaling:** Videos scale appropriately without distortion

### Enhanced Player Dashboard

The PlayerView includes comprehensive streaming analytics with real-time visualizations:

- **Quality Timeline Chart:** Interactive timeline showing video quality changes with hover tooltips
- **Buffer Status Visualization:** Real-time buffer level chart with color-coded health zones (critical/warning/good)
- **Segment Download Tracking:** Complete history of downloaded segments with performance metrics
- **Streaming Analytics:** Frame statistics, stall events, quality changes, and network performance
- **Responsive Layout:** All dashboard components adapt to mobile screens
- **Real-time Updates:** Charts and metrics update live during video playback

---

## Development & Setup

### Server

1. Install Python dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Ensure `ffmpeg` is installed and available in your PATH.
3. Run the Flask server:

   ```
   flask run
   ```

### Client

1. Install Node.js dependencies:

   ```
   cd client
   npm install
   ```

2. Start the development server:

   ```
   npm run dev
   ```

3. Access the client at [http://localhost:5173](http://localhost:5173).

### Presentation

1. Install dependencies:

   ```
   cd presentation
   pnpm install
   ```

2. Start the presentation server:

   ```
   pnpm dev
   ```

3. Access the presentation at [http://localhost:3030](http://localhost:3030).

4. Export to PDF:

   ```
   pnpm export
   ```

### Debug Mode

Enable enhanced debugging for video processing issues:

```bash
export DEBUG_VIDEO_PROCESSING=true
flask run
```

Debug mode provides:
- **Intermediate files** saved for inspection
- **Enhanced logging** with detailed processing steps
- **Debug MP4** conversion for testing
- **Error diagnosis** tools for troubleshooting

Access debug files in `uploads/<video-id>/` after processing.

---

## Design Choices

### Architecture Decisions

- **Background Processing:** Prevents client timeouts on large uploads and complex processing
- **Per-Video Folders:** Keeps all files organized and avoids filename conflicts
- **Polling for Status:** Simple, robust way to track long-running jobs without websockets
- **DASH Streaming:** Enables adaptive bitrate streaming for optimal user experience
- **UUID-based Storage:** Ensures unique video identifiers and prevents conflicts

### Video Processing Decisions

- **Universal Aspect Ratio Support:** Handles any video format without manual configuration
- **Intelligent Preprocessing:** Automatic detection and cleaning of problematic video formats
- **Rotation Metadata Preservation:** Maintains video orientation information for proper display
- **Quality Ladder Optimization:** Generates representations based on source characteristics
- **Fallback Mechanisms:** Graceful error handling when preprocessing fails

### Frontend Decisions

- **Responsive Video Player:** Adapts to different screen sizes and video orientations
- **Height Constraints:** Prevents portrait videos from overwhelming the viewport
- **Custom CSS:** Full control over styling without framework dependencies
- **Vue 3 Composition API:** Modern, maintainable component architecture

### Performance Optimizations

- **Stream Copying:** Fast preprocessing without re-encoding when possible
- **Bitrate Adaptation:** Optimal quality levels for different network conditions
- **Efficient Thumbnails:** Quick extraction at optimal timestamp
- **Cleanup Automation:** Temporary file management to conserve storage
