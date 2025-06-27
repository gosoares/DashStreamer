<template>
  <div class="video-info-panel" :class="{ collapsed: isCollapsed }">
    <div class="panel-header">
      <h2>Video Information</h2>
      <button @click="togglePanel" class="toggle-btn" :title="isCollapsed ? 'Expand' : 'Collapse'">
        <span :class="isCollapsed ? 'expand-icon' : 'collapse-icon'">
          {{ isCollapsed ? '▲' : '▼' }}
        </span>
      </button>
    </div>
    
    <div class="panel-content" v-show="!isCollapsed">
      <div class="cards-grid">
        <TechnicalInfo 
          :current-resolution="videoInfo.currentResolution"
          :video-codec="videoInfo.videoCodec"
          :audio-codec="videoInfo.audioCodec"
          :current-bitrate="videoInfo.currentBitrate"
          :frame-rate="videoInfo.frameRate"
          :aspect-ratio="videoInfo.aspectRatio"
          :container-type="videoInfo.containerType"
          :duration="videoInfo.duration"
          :available-qualities="videoInfo.availableQualities"
          :current-quality-id="videoInfo.currentQualityId"
        />
        
        <NetworkStats 
          :current-speed="networkStats.currentSpeed"
          :average-speed="networkStats.averageSpeed"
          :total-downloaded="networkStats.totalDownloaded"
        />
        
        <BufferStats 
          :video-buffer-level="bufferStats.videoBufferLevel"
          :audio-buffer-level="bufferStats.audioBufferLevel"
          :stall-count="bufferStats.stallCount"
        />
        
        <div class="performance-card">
          <div class="performance-metrics">
            <h3>Playback Performance</h3>
            <div class="metrics-grid">
              <div class="metric-item">
                <label>Dropped Frames</label>
                <span :class="getDropRateClass(performanceStats.dropRate)">{{ performanceStats.droppedFrames }}</span>
              </div>
              <div class="metric-item">
                <label>Total Frames</label>
                <span>{{ performanceStats.totalFrames }}</span>
              </div>
              <div class="metric-item">
                <label>Drop Rate</label>
                <span :class="getDropRateClass(performanceStats.dropRate)">{{ formatPercentage(performanceStats.dropRate) }}</span>
              </div>
              <div class="metric-item">
                <label>Quality Changes</label>
                <span :class="getQualityChangesClass(performanceStats.qualityChanges)">{{ performanceStats.qualityChanges }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import TechnicalInfo from './TechnicalInfo.vue';
import NetworkStats from './NetworkStats.vue';
import BufferStats from './BufferStats.vue';

export default {
  name: 'VideoInfoPanel',
  components: {
    TechnicalInfo,
    NetworkStats,
    BufferStats
  },
  props: {
    videoInfo: {
      type: Object,
      default: () => ({
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
      })
    },
    networkStats: {
      type: Object,
      default: () => ({
        currentSpeed: 0,
        averageSpeed: 0,
        totalDownloaded: 0
      })
    },
    bufferStats: {
      type: Object,
      default: () => ({
        videoBufferLevel: 0,
        audioBufferLevel: 0,
        stallCount: 0
      })
    },
    performanceStats: {
      type: Object,
      default: () => ({
        droppedFrames: 0,
        totalFrames: 0,
        dropRate: 0,
        startupTime: 0,
        totalStallTime: 0,
        qualityChanges: 0
      })
    }
  },
  data() {
    return {
      isCollapsed: false
    };
  },
  methods: {
    togglePanel() {
      this.isCollapsed = !this.isCollapsed;
    },
    formatPercentage(value) {
      if (!value || isNaN(value)) return '0%';
      return `${(value * 100).toFixed(2)}%`;
    },
    formatTime(seconds) {
      if (!seconds || seconds < 0) return '0s';
      if (seconds < 1) return `${(seconds * 1000).toFixed(0)}ms`;
      return `${seconds.toFixed(2)}s`;
    },
    getDropRateClass(dropRate) {
      if (dropRate > 0.05) return 'metric-critical'; // >5%
      if (dropRate > 0.01) return 'metric-warning';  // >1%
      return 'metric-good';
    },
    getQualityChangesClass(changes) {
      if (changes > 20) return 'metric-warning';       // Too many changes
      if (changes > 10) return 'metric-fair';
      return 'metric-good';
    }
  }
};
</script>

<style scoped>
.video-info-panel {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  margin-top: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.video-info-panel.collapsed {
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e9ecef;
  background: #f8f9fa;
  border-radius: 8px 8px 0 0;
  cursor: pointer;
}

.panel-header h2 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.2rem;
  font-weight: 600;
}

.toggle-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.2s ease;
}

.toggle-btn:hover {
  background: rgba(0, 0, 0, 0.1);
}

.expand-icon, .collapse-icon {
  font-size: 1rem;
  color: #6c757d;
  display: inline-block;
  transition: transform 0.3s ease;
}

.panel-content {
  padding: 20px;
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 20px;
}

.performance-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.performance-metrics h3 {
  margin: 0 0 16px 0;
  color: #2c3e50;
  font-size: 1.1rem;
  font-weight: 600;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric-item label {
  font-size: 0.875rem;
  color: #6c757d;
  font-weight: 500;
}

.metric-item span {
  font-size: 0.9rem;
  color: #2c3e50;
  font-weight: 600;
}

.metric-good {
  color: #28a745;
}

.metric-fair {
  color: #17a2b8;
}

.metric-warning {
  color: #ffc107;
}

.metric-critical {
  color: #dc3545;
}

@media (max-width: 768px) {
  .panel-header {
    padding: 12px 16px;
  }
  
  .panel-header h2 {
    font-size: 1.1rem;
  }
  
  .panel-content {
    padding: 16px;
  }
  
  .cards-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .metrics-grid {
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }
}

@media (max-width: 480px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }
}
</style>