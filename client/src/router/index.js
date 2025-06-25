import { createRouter, createWebHistory } from 'vue-router';
import HomeView from '../views/HomeView.vue';
import UploadView from '../views/UploadView.vue';
import PlayerView from '../views/PlayerView.vue';

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            name: 'home',
            component: HomeView
        },
        {
            path: '/upload',
            name: 'upload',
            component: UploadView
        },
        {
            path: '/player/:id',
            name: 'player',
            component: PlayerView,
            props: true
        }
    ]
});

export default router;
