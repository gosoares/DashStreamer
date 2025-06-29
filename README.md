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

DashStreamer is a full-stack web application for uploading, processing, and streaming videos using MPEG-DASH. It features a Flask backend for video processing and API, and a Vue.js frontend for a modern, user-friendly interface.

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
2. **UUID Generation:** Each video gets a unique identifier and dedicated storage folder
3. **Initial Metadata:** Basic `meta.json` created with status "pending"
4. **Background Thread:** Processing starts asynchronously to prevent client timeouts

#### Phase 2: Preprocessing & Analysis
1. **Metadata Stream Detection:**
   - Uses `ffprobe` to analyze all streams in the video file
   - Detects problematic metadata streams (especially iPhone/iOS videos with `mebx` data streams)
   - Identifies rotation metadata from Display Matrix side data

2. **Video Property Analysis:**
   - Extracts physical dimensions (width × height as stored in file)
   - Detects rotation metadata (-90°, 90°, 180°, etc.)
   - Calculates display dimensions (accounting for rotation)
   - Determines correct aspect ratio for display (e.g., 9:16 for portrait)

3. **Preprocessing (if needed):**
   - **iPhone/iOS Video Cleaning:** Removes problematic metadata streams while preserving video/audio
   - **Metadata Preservation:** Uses `-map_metadata 0` and `-movflags use_metadata_tags` to preserve rotation data
   - **Stream Copy:** Uses `-c copy` for fast processing without re-encoding
   - **Debug Mode:** Optionally saves preprocessed files for debugging

#### Phase 3: Quality Ladder Generation
1. **Adaptive Approach by Orientation:**
   - **Portrait Videos (AR < 1):** Uses target widths (1080p, 720p, 540p, 360p) and calculates heights
   - **Landscape Videos (AR ≥ 1):** Uses target heights and calculates widths
   - **Maintains exact aspect ratio** for all representations

2. **Quality Levels Generated:**
   - **Portrait Example:** 1080×1920, 720×1280, 540×960, 360×640
   - **Landscape Example:** 1920×1080, 1280×720, 960×540, 640×360
   - **Even Dimension Enforcement:** Ensures width/height are even numbers for codec compatibility

3. **Bitrate Calculation:**
   - **Video Bitrates:** Optimized per resolution (3000k for 1080p, 1500k for 720p, etc.)
   - **Audio Bitrates:** 128kbps for HD quality, 96kbps for lower resolutions
   - **Library Compatibility:** Values multiplied by 1000 for ffmpeg-streaming library

#### Phase 4: DASH Conversion
1. **DASH Stream Creation:**
   - Uses `python-ffmpeg-video-streaming` library for DASH packaging
   - **H.264 codec** with optimized settings for web streaming
   - **Adaptive streaming** with multiple quality representations

2. **Error Handling for Portrait Videos:**
   - **Conflict Detection:** Monitors for "Conflicting stream aspect ratios" errors
   - **Limited Representations:** Uses fewer quality levels for rotated videos if needed
   - **Detailed Logging:** Records exact aspect ratios and error details

3. **Segment Generation:**
   - **Initialization Segments:** `video_init_*.m4s` files for each quality level
   - **Media Segments:** `video_chunk_*_*.m4s` files containing actual video data
   - **Manifest File:** `video.mpd` describing all available representations

#### Phase 5: Thumbnail & Finalization
1. **Thumbnail Extraction:**
   - Extracted at 1-second mark using `ffmpeg`
   - Saved as `thumbnail.jpg` in video folder
   - Handles any video format and orientation

2. **Status Updates:**
   - **Real-time logging** in `processing.log` with detailed steps
   - **Metadata updates** in `meta.json` with final status
   - **File inventory** listing all generated files

3. **Cleanup:**
   - **Temporary files** removed automatically
   - **Debug files** preserved if debug mode enabled
   - **Error logging** for any cleanup failures

#### Debug Mode Features

When `DEBUG_VIDEO_PROCESSING=true`:
- **Preprocessed files** saved as `debug_preprocessed_*`
- **Debug MP4** created as `debug_converted.mp4` for testing
- **Enhanced logging** with detailed processing steps
- **File preservation** for troubleshooting

#### Supported Features

- **Universal Aspect Ratios:** 16:9, 4:3, 21:9, 9:16, 1:1, and any custom ratio
- **Portrait Video Support:** Proper handling of rotated mobile videos
- **iPhone Video Compatibility:** Automatic metadata stream cleaning
- **Error Recovery:** Graceful fallback if preprocessing fails
- **Comprehensive Logging:** Detailed processing information for debugging

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
