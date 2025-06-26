<template>
    <main class="container">
        <div class="header">
            <h1>Videos</h1>
            <router-link to="/upload" class="btn btn-primary">
                Upload Video
            </router-link>
        </div>

        <!-- Video grid -->
        <div v-if="videos.length > 0" class="video-grid">
            <div v-for="video in videos" :key="video.id" class="video-card" @click="goToPlayer(video.id)">
                <div class="video-thumbnail">
                    <img :src="getThumbnailUrl(video.id)" :alt="video.title">
                </div>
                <div class="video-info">
                    <h2 class="video-title">{{ video.title }}</h2>
                    <p class="video-date">
                        {{ formatDate(video.created) }}
                    </p>
                    <div class="status-container" v-if="video.status !== 'done'">
                        <span :class="{
                            'status-badge': true,
                            'status-done': video.status === 'done',
                            'status-pending': video.status === 'pending',
                            'status-processing': video.status === 'processing',
                            'status-error': video.status === 'error'
                        }">
                            {{ capitalizeStatus(video.status) }}
                        </span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Empty state -->
        <div v-else class="empty-state">
            <h3>No videos uploaded yet</h3>
            <router-link to="/upload" class="btn btn-primary">
                Upload your first video
            </router-link>
        </div>
    </main>
</template>

<script>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import ApiService from '@/services/ApiService';
import { capitalizeStatus, formatDate } from '@/utils/formatters';

export default {
    name: 'HomeView',
    setup() {
        const router = useRouter();
        const videos = ref([]);

        const fetchVideos = async () => {
            try {
                const response = await ApiService.getVideos();
                videos.value = response.data;
            } catch (error) {
                console.error('Error fetching videos:', error);
            }
        };

        const getThumbnailUrl = (videoId) => {
            return ApiService.getThumbnailUrl(videoId);
        };

        const goToPlayer = (videoId) => {
            router.push(`/player/${videoId}`);
        };

        onMounted(fetchVideos);

        return {
            videos,
            getThumbnailUrl,
            goToPlayer,
            capitalizeStatus,
            formatDate
        };
    }
};
</script>

<style scoped>
.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
}

.header h1 {
    font-size: 2rem;
    font-weight: 600;
}

.empty-state {
    text-align: center;
    padding: 3rem;
    background-color: white;
    border-radius: 0.5rem;
}

.empty-state h3 {
    font-size: 1.25rem;
    color: var(--gray-600);
    margin-bottom: 1rem;
}

.status-container {
    margin-top: 0.5rem;
}
</style>
