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
| GET    | `/videos/<video_id>/manifest.mpd`             | Get the MPEG-DASH manifest for a video.          |
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

The video processing pipeline has been enhanced with robust aspect ratio support and iPhone video compatibility:

1. **Upload:** User uploads a video and title via `/videos`.
2. **Background Processing:**
   - **Automatic Preprocessing:** Videos with problematic metadata streams (like iPhone videos) are automatically cleaned
   - **Aspect Ratio Detection:** Source video properties are analyzed using `ffprobe`
   - **Smart Representation Generation:** Quality ladders are generated that maintain the exact source aspect ratio
   - **DASH Generation:** Segments and manifest are created using the optimized representations
   - **Thumbnail Extraction:** Thumbnail is extracted at 1 second
   - **All outputs are saved in a unique folder for the video**
   - **Comprehensive Logging:** Status, errors, and processing details are tracked in `meta.json` and processing logs
3. **Client Polling:** The client polls `/videos/<id>/info` for status updates.

#### Enhanced Features

- **Universal Aspect Ratio Support:** Works with any aspect ratio (16:9, 4:3, 21:9, 9:16, cinematic ratios, etc.)
- **iPhone Video Compatibility:** Automatically handles complex metadata streams in iPhone/iOS videos
- **Smart Quality Ladders:** Generates appropriate bitrate representations based on source resolution
- **Preprocessing Pipeline:** Automatically cleans problematic video files when needed
- **Error Recovery:** Graceful fallback if preprocessing fails

### File Structure

```
uploads/
  <video_id>/
    original.<ext>
    manifest.mpd
    manifest_chunk_*.m4s
    manifest_init_*.m4s
    thumbnail.jpg
    meta.json
    processing.log
```

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
- **PlayerView:** Streams the video using dash.js and displays metadata.
- **ApiService.js:** Handles all HTTP requests to the Flask API.

### API Integration

- All API URLs are configured via `.env` (`VITE_API_URL`).
- The client polls the `/info` endpoint after upload to track processing.
- Thumbnails and manifests are fetched using the video ID.

### DASH Playback

- Uses dash.js to play MPEG-DASH streams.
- Manifest and segments are loaded directly from the Flask server.

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

---

## Design Choices

- **Background Processing:** Prevents client timeouts on large uploads.
- **Per-Video Folders:** Keeps all files for a video together and avoids filename conflicts.
- **Polling for Status:** Simple, robust way to track long-running jobs.
- **DASH Streaming:** Enables adaptive bitrate streaming for modern browsers.
- **Custom CSS:** Avoids dependency on Tailwind and ensures full control over styles.
