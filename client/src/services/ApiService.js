import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000';

const apiClient = axios.create({
    baseURL: API_URL,
    timeout: 600000, // 10 minutes timeout for large video uploads
    headers: {
        'Content-Type': 'application/json',
    }
});

export default {
    // Get all videos
    getVideos() {
        return apiClient.get('/videos');
    },

    // Get video info by ID
    getVideoInfo(videoId) {
        return apiClient.get(`/videos/${videoId}/info`);
    },

    // Upload a new video
    uploadVideo(formData, onUploadProgress) {
        return apiClient.post('/videos', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            },
            onUploadProgress: (progressEvent) => {
                const percentCompleted = Math.round(
                    (progressEvent.loaded * 100) / progressEvent.total
                );
                if (onUploadProgress) {
                    onUploadProgress(percentCompleted);
                }
            }
        });
    },

    // Get video manifest URL
    getManifestUrl(videoId) {
        return `${API_URL}/videos/${videoId}/video.mpd`;
    },

    // Get thumbnail URL
    getThumbnailUrl(videoId) {
        return `${API_URL}/videos/${videoId}/thumbnail.jpg`;
    }
};
