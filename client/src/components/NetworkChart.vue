<template>
  <div class="network-chart">
    <h3>Network Performance</h3>
    <div class="chart-container">
      <Line ref="chartRef" :data="chartData" :options="chartOptions" />
    </div>
    <div class="network-stats">
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
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line } from 'vue-chartjs';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export default {
  name: 'NetworkChart',
  components: {
    Line
  },
  props: {
    networkData: {
      type: Array,
      default: () => []
    },
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
  data() {
    return {
      maxDataPoints: 60 // Keep last 60 data points (1 minute at 1 second intervals)
    };
  },
  computed: {
    chartData() {
      const labels = this.networkData.map((_, index) => {
        const secondsAgo = this.networkData.length - 1 - index;
        return secondsAgo === 0 ? 'Now' : `${secondsAgo}s ago`;
      }).reverse();

      const speeds = this.networkData.map(data => data.speed / 1000000).reverse(); // Convert to Mbps

      return {
        labels,
        datasets: [
          {
            label: 'Download Speed (Mbps)',
            data: speeds,
            borderColor: '#007bff',
            backgroundColor: 'rgba(0, 123, 255, 0.1)',
            fill: true,
            tension: 0.4,
            pointRadius: 0,
            pointHoverRadius: 4,
            borderWidth: 2
          }
        ]
      };
    },
    chartOptions() {
      return {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          intersect: false,
          mode: 'index'
        },
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            titleColor: '#fff',
            bodyColor: '#fff',
            borderColor: '#007bff',
            borderWidth: 1,
            callbacks: {
              label: (context) => {
                return `Speed: ${context.parsed.y.toFixed(1)} Mbps`;
              }
            }
          }
        },
        scales: {
          x: {
            display: true,
            grid: {
              display: false
            },
            ticks: {
              maxTicksLimit: 8,
              color: '#6c757d'
            }
          },
          y: {
            display: true,
            beginAtZero: true,
            grid: {
              color: 'rgba(0, 0, 0, 0.1)'
            },
            ticks: {
              color: '#6c757d',
              callback: (value) => `${value.toFixed(1)} Mbps`
            }
          }
        },
        elements: {
          point: {
            radius: 0
          }
        }
      };
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
.network-chart {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.network-chart h3 {
  margin: 0 0 16px 0;
  color: #2c3e50;
  font-size: 1.1rem;
  font-weight: 600;
}

.chart-container {
  height: 200px;
  margin-bottom: 16px;
}

.network-stats {
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
  .chart-container {
    height: 150px;
  }
  
  .network-stats {
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }
}
</style>