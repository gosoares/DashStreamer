<template>
  <div class="buffer-stats">
    <h3>Buffer Status</h3>
    <div class="stats-grid">
      <div class="stat-item">
        <label>Video Buffer</label>
        <span :class="getBufferClass(videoBufferLevel)">{{ formatBufferTime(videoBufferLevel) }}</span>
      </div>
      <div class="stat-item">
        <label>Audio Buffer</label>
        <span :class="getBufferClass(audioBufferLevel)">{{ formatBufferTime(audioBufferLevel) }}</span>
      </div>
      <div class="stat-item">
        <label>Stall Events</label>
        <span :class="stallCount > 0 ? 'stall-warning' : ''">{{ stallCount }}</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'BufferStats',
  props: {
    videoBufferLevel: {
      type: Number,
      default: 0
    },
    audioBufferLevel: {
      type: Number,
      default: 0
    },
    stallCount: {
      type: Number,
      default: 0
    }
  },
  methods: {
    formatBufferTime(seconds) {
      if (!seconds || seconds < 0) return '0.0s';
      return `${seconds.toFixed(1)}s`;
    },
    getBufferClass(bufferLevel) {
      if (bufferLevel < 2) return 'buffer-critical';
      if (bufferLevel < 5) return 'buffer-warning'; 
      return 'buffer-good';
    }
  }
};
</script>

<style scoped>
.buffer-stats {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.buffer-stats h3 {
  margin: 0 0 16px 0;
  color: #2c3e50;
  font-size: 1.1rem;
  font-weight: 600;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-item label {
  font-size: 0.875rem;
  color: #6c757d;
  font-weight: 500;
}

.stat-item span {
  font-size: 0.9rem;
  color: #2c3e50;
  font-weight: 600;
}

.buffer-good {
  color: #28a745;
}

.buffer-warning {
  color: #ffc107;
}

.buffer-critical {
  color: #fd7e14;
}

.stall-warning {
  color: #dc3545;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }
}
</style>