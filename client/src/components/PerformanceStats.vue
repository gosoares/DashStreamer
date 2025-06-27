<template>
  <div class="performance-stats">
    <h3>Playback Performance</h3>
    <div class="metrics-grid">
      <div class="metric-item">
        <label>Dropped Frames</label>
        <span :class="getDropRateClass(dropRate)">{{ droppedFrames }}</span>
      </div>
      <div class="metric-item">
        <label>Total Frames</label>
        <span>{{ totalFrames }}</span>
      </div>
      <div class="metric-item">
        <label>Drop Rate</label>
        <span :class="getDropRateClass(dropRate)">{{ formatPercentage(dropRate) }}</span>
      </div>
      <div class="metric-item">
        <label>Quality Changes</label>
        <span :class="getQualityChangesClass(qualityChanges)">{{ qualityChanges }}</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PerformanceStats',
  props: {
    droppedFrames: {
      type: Number,
      default: 0
    },
    totalFrames: {
      type: Number,
      default: 0
    },
    dropRate: {
      type: Number,
      default: 0
    },
    startupTime: {
      type: Number,
      default: 0
    },
    totalStallTime: {
      type: Number,
      default: 0
    },
    qualityChanges: {
      type: Number,
      default: 0
    }
  },
  methods: {
    formatPercentage(value) {
      if (!value || isNaN(value)) return '0%';
      return `${(value * 100).toFixed(2)}%`;
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
.performance-stats {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.performance-stats h3 {
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