<template>
  <div class="technical-info">
    <h3>Technical Information</h3>
    <div class="info-grid">
      <div class="info-item">
        <label>Resolution</label>
        <span>{{ currentResolution }}</span>
      </div>
      <div class="info-item">
        <label>Video Codec</label>
        <span>{{ videoCodec }}</span>
      </div>
      <div class="info-item">
        <label>Audio Codec</label>
        <span>{{ audioCodec }}</span>
      </div>
      <div class="info-item">
        <label>Bitrate</label>
        <span>{{ formatBitrate(currentBitrate) }}</span>
      </div>
      <div class="info-item">
        <label>Frame Rate</label>
        <span>{{ frameRate }} fps</span>
      </div>
      <div class="info-item">
        <label>Aspect Ratio</label>
        <span>{{ aspectRatio }}</span>
      </div>
      <div class="info-item">
        <label>Container</label>
        <span>{{ containerType }}</span>
      </div>
      <div class="info-item">
        <label>Duration</label>
        <span>{{ formatDuration(duration) }}</span>
      </div>
    </div>
    
    <div class="quality-selector" v-if="availableQualities.length > 1">
      <h4>Available Qualities</h4>
      <div class="quality-list">
        <div 
          v-for="quality in availableQualities" 
          :key="quality.id"
          class="quality-item"
          :class="{ active: quality.id === currentQualityId }"
        >
          {{ quality.width }}×{{ quality.height }} - {{ formatBitrate(quality.bandwidth) }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TechnicalInfo',
  props: {
    currentResolution: {
      type: String,
      default: 'N/A'
    },
    videoCodec: {
      type: String,
      default: 'N/A'
    },
    audioCodec: {
      type: String,
      default: 'N/A'
    },
    currentBitrate: {
      type: Number,
      default: 0
    },
    frameRate: {
      type: Number,
      default: 0
    },
    aspectRatio: {
      type: String,
      default: 'N/A'
    },
    containerType: {
      type: String,
      default: 'DASH'
    },
    duration: {
      type: Number,
      default: 0
    },
    availableQualities: {
      type: Array,
      default: () => []
    },
    currentQualityId: {
      type: String,
      default: ''
    }
  },
  methods: {
    formatBitrate(bitrate) {
      if (!bitrate) return 'N/A';
      if (bitrate >= 1000000) {
        return `${(bitrate / 1000000).toFixed(1)} Mbps`;
      } else if (bitrate >= 1000) {
        return `${(bitrate / 1000).toFixed(0)} kbps`;
      }
      return `${bitrate} bps`;
    },
    formatDuration(seconds) {
      if (!seconds) return 'N/A';
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      const secs = Math.floor(seconds % 60);
      
      if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
      }
      return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
  }
};
</script>

<style scoped>
.technical-info {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.technical-info h3 {
  margin: 0 0 16px 0;
  color: #2c3e50;
  font-size: 1.1rem;
  font-weight: 600;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item label {
  font-size: 0.875rem;
  color: #6c757d;
  font-weight: 500;
}

.info-item span {
  font-size: 0.9rem;
  color: #2c3e50;
  font-weight: 600;
}

.quality-selector h4 {
  margin: 0 0 8px 0;
  color: #2c3e50;
  font-size: 1rem;
  font-weight: 600;
}

.quality-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.quality-item {
  padding: 4px 8px;
  background: #e9ecef;
  border-radius: 4px;
  font-size: 0.875rem;
  color: #495057;
  border: 1px solid transparent;
}

.quality-item.active {
  background: #007bff;
  color: white;
  border-color: #0056b3;
}

@media (max-width: 768px) {
  .info-grid {
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }
  
  .quality-list {
    flex-direction: column;
  }
}
</style>