<template>
  <div class="network-stats">
    <h3>Network Performance</h3>
    <div class="stats-grid">
      <div class="stat-item">
        <label>Current Speed</label>
        <span>{{ formatSpeed(currentSpeed) }}</span>
      </div>
      <div class="stat-item">
        <label>Average Speed</label>
        <span>{{ formatSpeed(averageSpeed) }}</span>
      </div>
      <div class="stat-item">
        <label>Total Downloaded</label>
        <span>{{ formatBytes(totalDownloaded) }}</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'NetworkStats',
  props: {
    currentSpeed: {
      type: Number,
      default: 0
    },
    averageSpeed: {
      type: Number,
      default: 0
    },
    totalDownloaded: {
      type: Number,
      default: 0
    }
  },
  methods: {
    formatSpeed(speed) {
      if (!speed) return '0 Mbps';
      if (speed >= 1000000) {
        return `${(speed / 1000000).toFixed(1)} Mbps`;
      } else if (speed >= 1000) {
        return `${(speed / 1000).toFixed(0)} kbps`;
      }
      return `${speed} bps`;
    },
    formatBytes(bytes) {
      if (!bytes) return '0 B';
      const sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(1024));
      return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
    }
  }
};
</script>

<style scoped>
.network-stats {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.network-stats h3 {
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


@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }
}
</style>