<template>
    <main class="container">
        <div class="header">
            <router-link to="/" class="back-link">
                ← Back to videos
            </router-link>
            <h1>Upload Video</h1>
        </div>

        <!-- Upload Form -->
        <form @submit.prevent="handleSubmit" class="upload-form">
            <div class="form-group">
                <label class="form-label">Video Title</label>
                <input v-model="title" type="text" required class="form-input" placeholder="Enter video title">
            </div>

            <div class="form-group">
                <label class="form-label">Video File</label>
                <div class="upload-area" @click="triggerFileInput" @dragover.prevent @drop.prevent="handleFileDrop">
                    <input type="file" ref="fileInput" @change="handleFileSelect"
                        accept=".mp4,.mov,.mkv,video/mp4,video/quicktime,video/x-matroska" class="hidden">
                    <div v-if="!selectedFile" class="upload-placeholder">
                        <p>Drag and drop your video here or click to browse</p>
                        <p class="upload-formats">Supported formats: MP4, MOV, MKV</p>
                    </div>
                    <div v-else class="file-info">
                        <p class="file-name">{{ selectedFile.name }}</p>
                        <p class="file-size">
                            {{ formatFileSize(selectedFile.size) }}
                        </p>
                    </div>
                </div>
            </div>

            <!-- Upload Progress -->
            <div v-if="uploadProgress > 0 && uploadProgress < 100" class="progress-container">
                <div class="progress-bar">
                    <div class="progress-bar-fill" :style="{ width: uploadProgress + '%' }"></div>
                </div>
                <p class="progress-text">Uploading... {{ uploadProgress }}%</p>
            </div>

            <!-- Processing Status -->
            <div v-if="processingStatus" class="processing-status">
                <div class="spinner"></div>
                <p>Processing video... {{ capitalizeStatus(processingStatus) }}</p>
            </div>

            <!-- Error Message -->
            <div v-if="errorMessage" class="error-message">
                {{ errorMessage }}
            </div>

            <!-- Submit Button -->
            <button type="submit" :disabled="!canSubmit" class="btn btn-primary submit-button">
                Upload Video
            </button>
        </form>
    </main>
</template>

<script>
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import ApiService from '@/services/ApiService';

export default {
    name: 'UploadView',
    setup() {
        const router = useRouter();
        const fileInput = ref(null);
        const selectedFile = ref(null);
        const title = ref('');
        const uploadProgress = ref(0);
        const processingStatus = ref('');
        const errorMessage = ref('');

        const canSubmit = computed(() => {
            return title.value.trim() && selectedFile.value && !processingStatus.value;
        });

        const triggerFileInput = () => {
            fileInput.value.click();
        };

        const handleFileSelect = (event) => {
            const file = event.target.files[0];
            if (file) {
                selectedFile.value = file;
            }
        };

        const handleFileDrop = (event) => {
            const file = event.dataTransfer.files[0];
            if (file && file.type.startsWith('video/')) {
                selectedFile.value = file;
            }
        };

        const formatFileSize = (bytes) => {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        };

        const pollProcessingStatus = async (videoId) => {
            try {
                const response = await ApiService.getVideoInfo(videoId);
                const status = response.data.status;

                console.log('Polling status for video', videoId, ':', status);

                if (status === 'done') {
                    processingStatus.value = '';
                    router.push('/');
                } else if (status === 'error') {
                    errorMessage.value = response.data.error || 'Processing failed';
                    processingStatus.value = '';
                } else {
                    processingStatus.value = status;
                    // Continue polling every 2 seconds
                    setTimeout(() => pollProcessingStatus(videoId), 2000);
                }
            } catch (error) {
                console.error('Error polling status:', error);
                errorMessage.value = `Failed to check processing status: ${error.response?.data?.error || error.message}`;
                processingStatus.value = '';
            }
        };

        const handleSubmit = async () => {
            if (!canSubmit.value) return;

            const formData = new FormData();
            formData.append('video', selectedFile.value);
            formData.append('title', title.value.trim());

            try {
                errorMessage.value = '';
                uploadProgress.value = 0;

                const response = await ApiService.uploadVideo(formData, (progress) => {
                    uploadProgress.value = progress;
                });

                const videoId = response.data.id;
                console.log('Video uploaded with ID:', videoId);
                processingStatus.value = 'pending';
                // Start polling immediately
                setTimeout(() => pollProcessingStatus(videoId), 1000);
            } catch (error) {
                console.error('Upload error:', error);
                errorMessage.value = error.response?.data?.error || 'Upload failed';
                uploadProgress.value = 0;
            }
        };

        const capitalizeStatus = (status) => {
            return status.charAt(0).toUpperCase() + status.slice(1);
        };

        return {
            fileInput,
            selectedFile,
            title,
            uploadProgress,
            processingStatus,
            errorMessage,
            canSubmit,
            triggerFileInput,
            handleFileSelect,
            handleFileDrop,
            handleSubmit,
            formatFileSize,
            capitalizeStatus
        };
    }
};
</script>

<style scoped>
.header {
    margin-bottom: 2rem;
}

.back-link {
    color: var(--primary-color);
    text-decoration: none;
    margin-bottom: 0.5rem;
    display: inline-block;
}

.header h1 {
    font-size: 2rem;
    font-weight: 600;
}

.upload-form {
    max-width: 640px;
    margin: 0 auto;
}

.hidden {
    display: none;
}

.upload-placeholder {
    color: var(--gray-600);
}

.upload-formats {
    font-size: 0.875rem;
    margin-top: 0.5rem;
    color: var(--gray-600);
}

.file-info {
    text-align: left;
}

.file-name {
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
}

.file-size {
    font-size: 0.875rem;
    color: var(--gray-600);
    margin-top: 0.25rem;
}

.progress-container {
    margin: 1rem 0;
}

.progress-text {
    font-size: 0.875rem;
    color: var(--gray-600);
    margin-top: 0.5rem;
}

.processing-status {
    display: flex;
    align-items: center;
    margin: 1rem 0;
    color: var(--gray-600);
}

.spinner {
    width: 1rem;
    height: 1rem;
    border: 2px solid var(--primary-color);
    border-top-color: transparent;
    border-radius: 50%;
    margin-right: 0.5rem;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}

.submit-button {
    width: 100%;
    margin-top: 1rem;
}

.submit-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}
</style>
