<template>
    <main class="container">
        <div class="header">
            <router-link to="/" class="back-link">
                ← Back to videos
            </router-link>
            <h1>{{ videoInfo?.title || 'Loading...' }}</h1>
            <div v-if="videoInfo" class="video-meta">
                <p class="video-date">
                    Uploaded on {{ formatDate(videoInfo.created) }}
                </p>
                <div class="status-container" v-if="videoInfo.status !== 'done'">
                    <span :class="{
                        'status-badge': true,
                        'status-done': videoInfo.status === 'done',
                        'status-pending': videoInfo.status === 'pending',
                        'status-processing': videoInfo.status === 'processing',
                        'status-error': videoInfo.status === 'error'
                    }">
                        {{ capitalizeStatus(videoInfo.status) }}
                    </span>
                </div>
            </div>
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


        <!-- Video Information Dashboard -->
        <div v-if="videoInfo && videoInfo.status === 'done'" class="dashboard-container">
            <!-- Quality Timeline Chart - Full Width -->
            <QualityTimelineChart 
                :segment-downloads="dashboardData.networkStats.segmentDownloads"
                :video-duration="dashboardData.videoInfo.duration"
            />
            
            <!-- Segment Downloads - Full Width -->
            <SegmentDownloadPanel 
                :segment-downloads="dashboardData.networkStats.segmentDownloads"
                @clear-history="clearSegmentHistory"
            />
            
            <!-- Video Information - Full Width -->
            <TechnicalInfo 
                :current-resolution="dashboardData.videoInfo.currentResolution"
                :video-codec="dashboardData.videoInfo.videoCodec"
                :audio-codec="dashboardData.videoInfo.audioCodec"
                :current-bitrate="dashboardData.videoInfo.currentBitrate"
                :frame-rate="dashboardData.videoInfo.frameRate"
                :aspect-ratio="dashboardData.videoInfo.aspectRatio"
                :container-type="dashboardData.videoInfo.containerType"
                :duration="dashboardData.videoInfo.duration"
                :available-qualities="dashboardData.videoInfo.availableQualities"
                :current-quality-id="dashboardData.videoInfo.currentQualityId"
                :total-downloaded="dashboardData.networkStats.totalDownloaded"
            />
            
            <!-- Buffer and Performance Stats - Side by Side -->
            <div class="cards-grid">
                <BufferStats 
                    :video-buffer-level="dashboardData.bufferStats.videoBufferLevel"
                    :audio-buffer-level="dashboardData.bufferStats.audioBufferLevel"
                    :stall-count="dashboardData.bufferStats.stallCount"
                />
                
                <PerformanceStats 
                    :dropped-frames="dashboardData.performanceStats.droppedFrames"
                    :total-frames="dashboardData.performanceStats.totalFrames"
                    :drop-rate="dashboardData.performanceStats.dropRate"
                    :startup-time="dashboardData.performanceStats.startupTime"
                    :total-stall-time="dashboardData.performanceStats.totalStallTime"
                    :quality-changes="dashboardData.performanceStats.qualityChanges"
                />
            </div>
        </div>
    </main>
</template>

<script>
import { ref, reactive, onMounted, onUnmounted } from 'vue';
import { useRoute } from 'vue-router';
import * as dashjs from 'dashjs';
import ApiService from '@/services/ApiService';
import { capitalizeStatus, formatDate } from '@/utils/formatters';
import TechnicalInfo from '@/components/TechnicalInfo.vue';
import BufferStats from '@/components/BufferStats.vue';
import SegmentDownloadPanel from '@/components/SegmentDownloadPanel.vue';
import PerformanceStats from '@/components/PerformanceStats.vue';
import QualityTimelineChart from '@/components/QualityTimelineChart.vue';

export default {
    name: 'PlayerView',
    components: {
        TechnicalInfo,
        BufferStats,
        SegmentDownloadPanel,
        PerformanceStats,
        QualityTimelineChart
    },
    setup() {
        const route = useRoute();
        const videoPlayer = ref(null);
        const videoInfo = ref(null);
        const errorMessage = ref('');
        let player = null;
        let updateInterval = null;

        // Dashboard data reactive state
        const dashboardData = reactive({
            videoInfo: {
                currentResolution: 'N/A',
                videoCodec: 'N/A',
                audioCodec: 'N/A',
                currentBitrate: 0,
                frameRate: 0,
                aspectRatio: 'N/A',
                containerType: 'DASH',
                duration: 0,
                availableQualities: [],
                currentQualityId: ''
            },
            networkStats: {
                totalDownloaded: 0,
                segmentDownloads: []
            },
            bufferData: [],
            bufferStats: {
                videoBufferLevel: 0,
                audioBufferLevel: 0,
                stallCount: 0
            },
            performanceStats: {
                droppedFrames: 0,
                totalFrames: 0,
                dropRate: 0,
                startupTime: 0,
                totalStallTime: 0,
                qualityChanges: 0
            }
        });

        let updateCounter = 0;
        
        // Segment download tracking
        const segmentTracker = new Map();
        
        // Utility functions for segment tracking
        const getSegmentId = (request) => {
            return request.url || request.requestId || `${request.mediaType}-${Date.now()}`;
        };
        
        const formatBytes = (bytes) => {
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        };
        
        const formatSpeed = (bytesPerSecond) => {
            if (bytesPerSecond === 0) return '0 B/s';
            const k = 1024;
            const sizes = ['B/s', 'KB/s', 'MB/s', 'GB/s'];
            const i = Math.floor(Math.log(bytesPerSecond) / Math.log(k));
            return parseFloat((bytesPerSecond / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        };
        
        const getSegmentName = (url) => {
            if (!url) return 'Unknown';
            const parts = url.split('/');
            return parts[parts.length - 1] || 'segment';
        };
        
        const formatTimeRange = (seconds) => {
            if (seconds < 0 || isNaN(seconds)) return '0:00';
            const mins = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return `${mins}:${secs.toString().padStart(2, '0')}`;
        };
        
        const addSegmentToHistory = (segmentData) => {
            dashboardData.networkStats.segmentDownloads.unshift(segmentData);
        };
        
        const clearSegmentHistory = () => {
            dashboardData.networkStats.segmentDownloads = [];
        };
        
        const updateDashboardData = () => {
            updateCounter++;
            console.log(`=== Update #${updateCounter} at ${new Date().toLocaleTimeString()} ===`);
            if (!player) return;

            try {
                const videoElement = videoPlayer.value;
                if (!videoElement) return;

                console.log('=== DASHBOARD UPDATE START ===');
                
                // Reset complete data flag
                dashboardData.videoInfo._hasCompleteData = false;
                
                // STEP 1: Try to get current representation directly (most accurate)
                let gotCompleteDataFromCurrent = false;
                
                if (typeof player.getCurrentRepresentationForType === 'function') {
                    try {
                        const currentVideoRep = player.getCurrentRepresentationForType('video');
                        console.log('🎯 getCurrentRepresentationForType result:', currentVideoRep);
                        
                        if (currentVideoRep) {
                            console.log('Current representation properties:', Object.keys(currentVideoRep));
                            console.log('Bandwidth:', currentVideoRep.bandwidth);
                            console.log('Width/Height:', currentVideoRep.width, 'x', currentVideoRep.height);
                            
                            // If we have complete data, use it exclusively
                            if (currentVideoRep.bandwidth && currentVideoRep.width && currentVideoRep.height) {
                                dashboardData.videoInfo.currentBitrate = currentVideoRep.bandwidth;
                                dashboardData.videoInfo.currentResolution = `${currentVideoRep.width}×${currentVideoRep.height}`;
                                
                                if (currentVideoRep.codecs) {
                                    dashboardData.videoInfo.videoCodec = currentVideoRep.codecs.split(',')[0] || 'H.264';
                                }
                                
                                gotCompleteDataFromCurrent = true;
                                dashboardData.videoInfo._hasCompleteData = true;
                                
                                console.log('✅ SUCCESS: Got complete data from getCurrentRepresentationForType');
                                console.log('Resolution:', dashboardData.videoInfo.currentResolution);
                                console.log('Bitrate:', dashboardData.videoInfo.currentBitrate);
                            }
                        }
                    } catch (error) {
                        console.warn('getCurrentRepresentationForType failed:', error);
                    }
                }
                
                // STEP 2: If we got complete data, skip other methods
                if (gotCompleteDataFromCurrent) {
                    console.log('✅ Using authoritative data from current representation, skipping fallbacks');
                } else {
                    console.log('⚠️ Fallback: getCurrentRepresentationForType didn\'t provide complete data');
                    
                    // STEP 3: Try quality index approach as fallback
                    let videoQuality = -1;
                    
                    try {
                        if (typeof player.getQualityFor === 'function') {
                            videoQuality = player.getQualityFor('video');
                        } else if (typeof player.getQuality === 'function') {
                            videoQuality = player.getQuality('video');
                        }
                        console.log('Current quality index:', videoQuality);
                    } catch (qualityError) {
                        console.warn('Quality methods failed:', qualityError);
                    }

                    // STEP 4: Try to get quality list and match by index
                    if (videoQuality >= 0) {
                        console.log('🔍 Trying to get representation by quality index:', videoQuality);
                        
                        const possibleMethods = ['getBitrateInfoListFor', 'getBitrateInfoList'];
                        let videoBitrateList = null;
                        
                        for (const method of possibleMethods) {
                            if (typeof player[method] === 'function') {
                                try {
                                    videoBitrateList = player[method]('video');
                                    if (videoBitrateList && videoBitrateList.length > 0) {
                                        console.log(`✅ Got bitrate list from ${method}`);
                                        break;
                                    }
                                } catch (error) {
                                    console.warn(`${method} failed:`, error);
                                }
                            }
                        }
                        
                        if (videoBitrateList && videoBitrateList.length > videoQuality) {
                            const representation = videoBitrateList[videoQuality];
                            console.log('🎯 Found representation at index', videoQuality, ':', representation);
                            
                            // Extract data from this specific representation
                            let resolutionFound = false;
                            let bitrateFound = false;
                            
                            // Try to get resolution
                            if (representation.width && representation.height) {
                                dashboardData.videoInfo.currentResolution = `${representation.width}×${representation.height}`;
                                resolutionFound = true;
                                console.log('✅ Set resolution from bitrate list:', representation.width, 'x', representation.height);
                            }
                            
                            // Try to get bitrate
                            const bitrate = representation.bitrate || representation.bandwidth;
                            if (bitrate) {
                                dashboardData.videoInfo.currentBitrate = bitrate < 100000 ? bitrate * 1000 : bitrate;
                                bitrateFound = true;
                                console.log('✅ Set bitrate from bitrate list:', bitrate);
                            }
                            
                            if (resolutionFound && bitrateFound) {
                                dashboardData.videoInfo._hasCompleteData = true;
                                console.log('✅ SUCCESS: Got complete data from bitrate list method');
                            }
                        }
                    }
                }
                
                // STEP 6: Handle video element properties (but never override DASH resolution)
                console.log('📱 Video element info:', {
                    width: videoElement.videoWidth,
                    height: videoElement.videoHeight,
                    duration: videoElement.duration,
                    hasCompleteDataFromDASH: dashboardData.videoInfo._hasCompleteData,
                    currentDASHResolution: dashboardData.videoInfo.currentResolution
                });
                
                // Set duration (always safe)
                if (videoElement.duration) {
                    dashboardData.videoInfo.duration = videoElement.duration;
                }
                
                // Calculate aspect ratio (always useful, doesn't conflict)
                if (videoElement.videoWidth && videoElement.videoHeight) {
                    const aspectRatio = videoElement.videoWidth / videoElement.videoHeight;
                    if (Math.abs(aspectRatio - 16/9) < 0.01) {
                        dashboardData.videoInfo.aspectRatio = '16:9';
                    } else if (Math.abs(aspectRatio - 4/3) < 0.01) {
                        dashboardData.videoInfo.aspectRatio = '4:3';
                    } else if (Math.abs(aspectRatio - 9/16) < 0.01) {
                        dashboardData.videoInfo.aspectRatio = '9:16';
                    } else {
                        dashboardData.videoInfo.aspectRatio = aspectRatio.toFixed(2);
                    }
                }
                
                // CRITICAL: Only use video element resolution if we have NO DASH data whatsoever
                if (!dashboardData.videoInfo._hasCompleteData && 
                    (!dashboardData.videoInfo.currentResolution || dashboardData.videoInfo.currentResolution === 'N/A×N/A') &&
                    videoElement.videoWidth && videoElement.videoHeight) {
                    
                    dashboardData.videoInfo.currentResolution = `${videoElement.videoWidth}×${videoElement.videoHeight}`;
                    console.log('⚠️ FALLBACK: Using video element resolution (no DASH data):', dashboardData.videoInfo.currentResolution);
                } else if (dashboardData.videoInfo._hasCompleteData) {
                    console.log('✅ PRESERVED: DASH resolution protected from video element override:', dashboardData.videoInfo.currentResolution);
                } else {
                    console.log('🔍 Video element available but waiting for DASH data or metadata:', {
                        videoElementReady: !!(videoElement.videoWidth && videoElement.videoHeight),
                        readyState: videoElement.readyState
                    });
                    
                    // If metadata isn't loaded yet, set up an event listener
                    if (videoElement.readyState < 1) {
                        const handleMetadataLoaded = () => {
                            console.log('Metadata loaded, updating dimensions');
                            if (videoElement.videoWidth && videoElement.videoHeight) {
                                dashboardData.videoInfo.currentResolution = `${videoElement.videoWidth}×${videoElement.videoHeight}`;
                                const aspectRatio = videoElement.videoWidth / videoElement.videoHeight;
                                if (Math.abs(aspectRatio - 16/9) < 0.01) {
                                    dashboardData.videoInfo.aspectRatio = '16:9';
                                } else if (Math.abs(aspectRatio - 4/3) < 0.01) {
                                    dashboardData.videoInfo.aspectRatio = '4:3';
                                } else if (Math.abs(aspectRatio - 9/16) < 0.01) {
                                    dashboardData.videoInfo.aspectRatio = '9:16';
                                } else {
                                    dashboardData.videoInfo.aspectRatio = aspectRatio.toFixed(2);
                                }
                            }
                            videoElement.removeEventListener('loadedmetadata', handleMetadataLoaded);
                        };
                        videoElement.addEventListener('loadedmetadata', handleMetadataLoaded);
                    }
                }

                // Estimate bitrate if not available from DASH
                if (!dashboardData.videoInfo.currentBitrate || dashboardData.videoInfo.currentBitrate === 0) {
                    // Method 1: Use current network throughput as estimate
                    if (dashboardData.networkStats.currentSpeed > 0) {
                        dashboardData.videoInfo.currentBitrate = Math.round(dashboardData.networkStats.currentSpeed);
                        console.log('Estimated bitrate from network speed:', dashboardData.videoInfo.currentBitrate);
                    }
                    // Method 2: Estimate from resolution (rough calculation)
                    else if (videoElement.videoWidth && videoElement.videoHeight) {
                        const pixels = videoElement.videoWidth * videoElement.videoHeight;
                        let estimatedBitrate = 0;
                        
                        // Rough bitrate estimation based on resolution
                        if (pixels <= 640 * 480) { // 480p
                            estimatedBitrate = 1000000; // 1 Mbps
                        } else if (pixels <= 1280 * 720) { // 720p
                            estimatedBitrate = 2500000; // 2.5 Mbps
                        } else if (pixels <= 1920 * 1080) { // 1080p
                            estimatedBitrate = 5000000; // 5 Mbps
                        } else { // 4K+
                            estimatedBitrate = 15000000; // 15 Mbps
                        }
                        
                        dashboardData.videoInfo.currentBitrate = estimatedBitrate;
                        console.log('Estimated bitrate from resolution:', estimatedBitrate, 'for', pixels, 'pixels');
                    }
                }

                // STEP 7: Set reasonable defaults for missing data
                if (!dashboardData.videoInfo.videoCodec || dashboardData.videoInfo.videoCodec === 'N/A') {
                    dashboardData.videoInfo.videoCodec = 'H.264';
                }
                if (!dashboardData.videoInfo.audioCodec || dashboardData.videoInfo.audioCodec === 'N/A') {
                    dashboardData.videoInfo.audioCodec = 'AAC';
                }
                if (!dashboardData.videoInfo.frameRate || dashboardData.videoInfo.frameRate === 0) {
                    dashboardData.videoInfo.frameRate = 30;
                }

                // Get performance stats from video element
                if (videoElement.getVideoPlaybackQuality) {
                    try {
                        const quality = videoElement.getVideoPlaybackQuality();
                        dashboardData.performanceStats.droppedFrames = quality.droppedVideoFrames || 0;
                        dashboardData.performanceStats.totalFrames = quality.totalVideoFrames || 0;
                        dashboardData.performanceStats.dropRate = dashboardData.performanceStats.totalFrames > 0 
                            ? dashboardData.performanceStats.droppedFrames / dashboardData.performanceStats.totalFrames 
                            : 0;
                    } catch (qualityError) {
                        console.warn('Video quality stats not available:', qualityError);
                    }
                }

                // Update buffer levels - try different approaches
                try {
                    // Method 1: Direct API call
                    let videoBufferLevel = 0;
                    let audioBufferLevel = 0;

                    try {
                        if (typeof player.getBufferLength === 'function') {
                            videoBufferLevel = player.getBufferLength('video') || 0;
                            audioBufferLevel = player.getBufferLength('audio') || 0;
                        } else if (typeof player.getBuffer === 'function') {
                            const buffers = player.getBuffer();
                            videoBufferLevel = buffers?.video || 0;
                            audioBufferLevel = buffers?.audio || 0;
                        }
                    } catch (bufferApiError) {
                        console.warn('Buffer API not available, trying alternative:', bufferApiError);
                        
                        // Method 2: Use video element buffered property
                        if (videoElement.buffered && videoElement.buffered.length > 0) {
                            const currentTime = videoElement.currentTime;
                            const buffered = videoElement.buffered;
                            
                            for (let i = 0; i < buffered.length; i++) {
                                if (currentTime >= buffered.start(i) && currentTime <= buffered.end(i)) {
                                    videoBufferLevel = buffered.end(i) - currentTime;
                                    audioBufferLevel = videoBufferLevel; // Assume same for audio
                                    break;
                                }
                            }
                        }
                    }
                    
                    dashboardData.bufferStats.videoBufferLevel = videoBufferLevel;
                    dashboardData.bufferStats.audioBufferLevel = audioBufferLevel;

                    // Add to buffer history
                    dashboardData.bufferData.push({
                        video: videoBufferLevel,
                        audio: audioBufferLevel,
                        timestamp: Date.now()
                    });

                    if (dashboardData.bufferData.length > 60) {
                        dashboardData.bufferData.shift();
                    }

                    console.log('Buffer levels:', { video: videoBufferLevel, audio: audioBufferLevel });
                } catch (bufferError) {
                    console.warn('Buffer monitoring failed:', bufferError);
                }

                // Update total downloaded
                try {
                    console.log('Network stats:', {
                        totalDownloaded: dashboardData.networkStats.totalDownloaded
                    });
                } catch (networkError) {
                    console.warn('Network monitoring failed:', networkError);
                }

                // STEP 8: Final summary
                console.log('=== FINAL DASHBOARD RESULTS ===');
                console.log('🎬 Resolution:', dashboardData.videoInfo.currentResolution);
                console.log('📊 Bitrate:', dashboardData.videoInfo.currentBitrate, 'bps =', (dashboardData.videoInfo.currentBitrate / 1000000).toFixed(2), 'Mbps');
                console.log('🎯 Source consistency:', dashboardData.videoInfo._hasCompleteData ? '✅ DASH (matched)' : '⚠️ Mixed sources');
                console.log('🎞️ Codec:', dashboardData.videoInfo.videoCodec, '/', dashboardData.videoInfo.audioCodec);
                console.log('📐 Aspect:', dashboardData.videoInfo.aspectRatio);
                console.log('=== END DASHBOARD UPDATE ===');
                
                // Clean up internal tracking flag
                delete dashboardData.videoInfo._hasCompleteData;

            } catch (error) {
                console.error('❌ Error updating dashboard data:', error);
            }
        };

        const setupDashEventListeners = () => {
            if (!player) return;

            // Quality change events
            player.on(dashjs.MediaPlayer.events.QUALITY_CHANGE_RENDERED, (e) => {
                dashboardData.performanceStats.qualityChanges++;
                updateDashboardData();
            });

            // Buffer events
            player.on(dashjs.MediaPlayer.events.BUFFER_LEVEL_UPDATED, (e) => {
                updateDashboardData();
            });

            // Stall events
            player.on(dashjs.MediaPlayer.events.PLAYBACK_STALLED, (e) => {
                dashboardData.bufferStats.stallCount++;
            });

            // Fragment loading started event
            player.on(dashjs.MediaPlayer.events.FRAGMENT_LOADING_STARTED, (e) => {
                if (e && e.request) {
                    const segmentId = getSegmentId(e.request);
                    segmentTracker.set(segmentId, {
                        id: segmentId,
                        url: e.request.url,
                        mediaType: e.request.mediaType || 'unknown',
                        startTime: performance.now(),
                        segmentName: getSegmentName(e.request.url)
                    });
                }
            });

            // Fragment loading completed event (enhanced)
            player.on(dashjs.MediaPlayer.events.FRAGMENT_LOADING_COMPLETED, (e) => {
                console.log('Fragment loaded:', e);
                if (e && e.request) {
                    const segmentId = getSegmentId(e.request);
                    const startData = segmentTracker.get(segmentId);
                    const endTime = performance.now();
                    const bytesLoaded = e.request.bytesLoaded || e.request.responseLength || e.request.byteLength;
                    
                    if (bytesLoaded) {
                        dashboardData.networkStats.totalDownloaded += bytesLoaded;
                        console.log('Total downloaded updated:', dashboardData.networkStats.totalDownloaded);
                    }
                    
                    // Create segment download record
                    if (startData && bytesLoaded) {
                        const downloadTime = (endTime - startData.startTime) / 1000; // Convert to seconds
                        const downloadSpeed = downloadTime > 0 ? bytesLoaded / downloadTime : 0;
                        
                        // Get quality information from current dashboard data
                        let resolution = 'N/A';
                        let bitrate = 'N/A';
                        let timeRange = 'N/A';
                        
                        if (startData.mediaType === 'video') {
                            // Use the same data that's shown in Technical Information card
                            if (dashboardData.videoInfo.currentResolution && dashboardData.videoInfo.currentResolution !== 'N/A') {
                                resolution = dashboardData.videoInfo.currentResolution;
                            }
                            
                            if (dashboardData.videoInfo.currentBitrate && dashboardData.videoInfo.currentBitrate > 0) {
                                // Convert bitrate from bps to kbps for display
                                bitrate = `${Math.round(dashboardData.videoInfo.currentBitrate / 1000)}k`;
                            }
                        }
                        
                        // Get segment start time from request data
                        try {
                            if (e.request && e.request.startTime !== undefined) {
                                timeRange = formatTimeRange(e.request.startTime);
                            } else if (e.request && e.request.index !== undefined) {
                                // Estimate based on segment index and typical segment duration (2 seconds)
                                const segmentDuration = 2; // Default segment duration
                                const startTime = e.request.index * segmentDuration;
                                timeRange = formatTimeRange(startTime);
                            }
                        } catch (error) {
                            console.warn('Error calculating start time for segment:', error);
                        }
                        
                        const segmentData = {
                            id: segmentId,
                            segmentName: startData.segmentName,
                            url: startData.url,
                            mediaType: startData.mediaType,
                            size: bytesLoaded,
                            sizeFormatted: formatBytes(bytesLoaded),
                            downloadTime: downloadTime,
                            downloadSpeed: downloadSpeed,
                            downloadSpeedFormatted: formatSpeed(downloadSpeed),
                            timestamp: new Date().toLocaleTimeString(),
                            quality: e.request.quality || 'N/A',
                            index: e.request.index || 0,
                            resolution: resolution,
                            bitrate: bitrate,
                            timeRange: timeRange
                        };
                        
                        addSegmentToHistory(segmentData);
                    }
                    
                    // Clean up tracker
                    segmentTracker.delete(segmentId);
                }
            });

            // Fragment loading abandoned event
            player.on(dashjs.MediaPlayer.events.FRAGMENT_LOADING_ABANDONED, (e) => {
                if (e && e.request) {
                    const segmentId = getSegmentId(e.request);
                    const startData = segmentTracker.get(segmentId);
                    
                    if (startData) {
                        const segmentData = {
                            id: segmentId,
                            segmentName: startData.segmentName,
                            url: startData.url,
                            mediaType: startData.mediaType,
                            size: 0,
                            sizeFormatted: 'Failed',
                            downloadTime: 0,
                            downloadSpeed: 0,
                            downloadSpeedFormatted: 'Failed',
                            timestamp: new Date().toLocaleTimeString(),
                            quality: 'Failed',
                            index: e.request.index || 0,
                            failed: true
                        };
                        
                        addSegmentToHistory(segmentData);
                    }
                    
                    // Clean up tracker
                    segmentTracker.delete(segmentId);
                }
            });

            // Playback started event
            player.on(dashjs.MediaPlayer.events.PLAYBACK_STARTED, (e) => {
                const startTime = performance.now() - dashboardData.performanceStats.startupTime;
                dashboardData.performanceStats.startupTime = startTime / 1000; // Convert to seconds
                
                // Force update when playback starts
                setTimeout(updateDashboardData, 100);
                setTimeout(updateDashboardData, 500);
                setTimeout(updateDashboardData, 1000);
            });

            // Stream initialized event - good time to get video info
            player.on(dashjs.MediaPlayer.events.STREAM_INITIALIZED, (e) => {
                console.log('Stream initialized, updating dashboard data');
                setTimeout(updateDashboardData, 100);
            });

            // Manifest loaded event
            player.on(dashjs.MediaPlayer.events.MANIFEST_LOADED, (e) => {
                console.log('Manifest loaded event:', e);
                
                // Try to get manifest data
                try {
                    if (e && e.data) {
                        console.log('Manifest data available:', e.data);
                        
                        // Look for video representations in manifest
                        if (e.data.Period && e.data.Period.length > 0) {
                            const period = e.data.Period[0];
                            if (period.AdaptationSet) {
                                period.AdaptationSet.forEach((adaptationSet, index) => {
                                    console.log(`AdaptationSet ${index}:`, adaptationSet);
                                    if (adaptationSet.Representation && adaptationSet.contentType === 'video') {
                                        console.log('Video representations found:', adaptationSet.Representation);
                                        
                                        // Store representations for later use
                                        if (adaptationSet.Representation.length > 0) {
                                            const rep = adaptationSet.Representation[0];
                                            if (rep.bandwidth) {
                                                dashboardData.videoInfo.currentBitrate = rep.bandwidth;
                                                console.log('Set bitrate from manifest:', rep.bandwidth);
                                            }
                                        }
                                    }
                                });
                            }
                        }
                    }
                } catch (manifestError) {
                    console.warn('Error parsing manifest:', manifestError);
                }
                
                setTimeout(updateDashboardData, 100);
            });

            // Metrics collection
            player.on(dashjs.MediaPlayer.events.METRICS_CHANGED, (e) => {
                updateDashboardData();
            });
        };

        const initializePlayer = async () => {
            try {
                // Get video info
                const response = await ApiService.getVideoInfo(route.params.id);
                videoInfo.value = response.data;

                if (videoInfo.value.status !== 'done') {
                    errorMessage.value = 'Video is not ready for playback';
                    return;
                }

                // Record startup time
                dashboardData.performanceStats.startupTime = performance.now();

                // Initialize DASH player
                player = dashjs.MediaPlayer().create();
                
                // Configure player to start at lowest quality
                player.updateSettings({
                    streaming: {
                        abr: {
                            initialBitrate: {
                                video: 0  // Start with lowest quality
                            },
                            autoSwitchBitrate: {
                                video: true  // Allow adaptive bitrate after initial selection
                            }
                        }
                    }
                });
                
                player.initialize(videoPlayer.value, ApiService.getManifestUrl(route.params.id), true);

                // Setup event listeners
                setupDashEventListeners();

                // Add HTML5 video element event listeners
                if (videoPlayer.value) {
                    videoPlayer.value.addEventListener('loadedmetadata', () => {
                        console.log('HTML5 loadedmetadata event fired');
                        setTimeout(updateDashboardData, 100);
                    });
                    
                    videoPlayer.value.addEventListener('canplay', () => {
                        console.log('HTML5 canplay event fired');
                        setTimeout(updateDashboardData, 100);
                    });
                    
                    videoPlayer.value.addEventListener('playing', () => {
                        console.log('HTML5 playing event fired');
                        setTimeout(updateDashboardData, 100);
                    });
                }

                // Add error handling
                player.on('error', (e) => {
                    console.error('DASH player error:', e);
                    errorMessage.value = 'Error playing video';
                });

                // Start periodic updates (more frequent for debugging)
                updateInterval = setInterval(updateDashboardData, 500);

                // Initial data update with multiple attempts
                setTimeout(updateDashboardData, 1000);
                setTimeout(updateDashboardData, 3000);
                setTimeout(updateDashboardData, 5000);

            } catch (error) {
                console.error('Error initializing player:', error);
                errorMessage.value = 'Failed to load video';
            }
        };

        onMounted(initializePlayer);

        onUnmounted(() => {
            if (updateInterval) {
                clearInterval(updateInterval);
                updateInterval = null;
            }
            if (player) {
                player.destroy();
                player = null;
            }
        });

        return {
            videoPlayer,
            videoInfo,
            errorMessage,
            dashboardData,
            capitalizeStatus,
            formatDate,
            clearSegmentHistory
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
    margin-bottom: 0.5rem;
}

.video-meta {
    margin-top: 0.5rem;
}

.video-meta .video-date {
    color: var(--gray-600);
    margin-bottom: 0.5rem;
}

.video-meta .status-container {
    margin: 0;
}

.video-player-container {
    max-width: 1024px;
    margin: 0 auto 2rem;
}

.video-player {
    width: 100%;
    max-width: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
}

.video-player video {
    width: 100%;
    height: auto;
    max-width: 100%;
    max-height: 70vh; /* Limit height to 70% of viewport height */
    display: block;
    object-fit: contain; /* Maintain aspect ratio */
}

.dashboard-container {
    max-width: 1024px;
    margin: 0 auto;
}

.cards-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-top: 20px;
}

/* Responsive adjustments for mobile devices */
@media (max-width: 768px) {
    .video-player video {
        max-height: 60vh; /* Smaller max height on mobile */
    }
    
    .video-player-container {
        margin-bottom: 1rem;
    }
    
    .cards-grid {
        grid-template-columns: 1fr;
        gap: 16px;
    }
}

/* Specific adjustments for portrait videos on mobile */
@media (max-width: 768px) and (orientation: portrait) {
    .video-player video {
        max-height: 50vh; /* Even smaller on mobile portrait */
    }
}
</style>
