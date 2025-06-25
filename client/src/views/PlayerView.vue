<template>
    <main class="container">
        <div class="header">
            <router-link to="/" class="back-link">
                ← Back to videos
            </router-link>
            <h1>{{ videoInfo?.title || 'Loading...' }}</h1>
        </div>

        <!-- Video Player -->
        <div class="video-player-container">
            <div class="video-player">
                <video ref="videoPlayer" controls></video>
            </div>
        </div>

        <!-- Error Message -->
        <div v-if="errorMessage" class="error-message">
            {{ errorMessage }}
        </div>

        <!-- Video Info -->
        <div v-if="videoInfo" class="video-details">
            <h2>{{ videoInfo.title }}</h2>
            <p class="video-date">
                Uploaded on {{ new Date(videoInfo.created).toLocaleDateString() }}
            </p>
            <div class="status-container">
                <span :class="{
                    'status-badge': true,
                    'status-done': videoInfo.status === 'done',
                    'status-pending': videoInfo.status === 'pending',
                    'status-processing': videoInfo.status === 'processing',
                    'status-error': videoInfo.status === 'error'
                }">
                    {{ videoInfo.status }}
                </span>
            </div>
        </div>
    </main>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue';
import { useRoute } from 'vue-router';
import * as dashjs from 'dashjs';
import ApiService from '@/services/ApiService';

export default {
    name: 'PlayerView',
    setup() {
        const route = useRoute();
        const videoPlayer = document.querySelector("#videoPlayer") || ref(null);
        const videoInfo = ref(null);
        const errorMessage = ref('');
        let player = null;

        const initializePlayer = async () => {
            try {
                // Get video info
                const response = await ApiService.getVideoInfo(route.params.id);
                videoInfo.value = response.data;

                if (videoInfo.value.status !== 'done') {
                    errorMessage.value = 'Video is not ready for playback';
                    return;
                }

                // Initialize DASH player
                player = dashjs.MediaPlayer().create();
                player.initialize(videoPlayer.value, ApiService.getManifestUrl(route.params.id), true);

                // Add error handling
                player.on('error', (e) => {
                    console.error('DASH player error:', e);
                    errorMessage.value = 'Error playing video';
                });

            } catch (error) {
                console.error('Error initializing player:', error);
                errorMessage.value = 'Failed to load video';
            }
        };

        onMounted(initializePlayer);

        onUnmounted(() => {
            if (player) {
                player.destroy();
                player = null;
            }
        });

        return {
            videoPlayer,
            videoInfo,
            errorMessage
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

.video-player-container {
    max-width: 1024px;
    margin: 0 auto 2rem;
}

.video-details {
    max-width: 1024px;
    margin: 0 auto;
    background: white;
    padding: 1.5rem;
    border-radius: 0.5rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.video-details h2 {
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
}

.video-date {
    color: var(--gray-600);
    margin-bottom: 1rem;
}

.status-container {
    margin-top: 1rem;
}
</style>
