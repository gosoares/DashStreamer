<template>
  <div class="buffer-chart">
    <h3>Buffer Status</h3>
    <div class="chart-container">
      <Line ref="chartRef" :data="chartData" :options="chartOptions" />
    </div>
    <div class="buffer-stats">
      <div class="stat-item">
        <label>Video Buffer</label>
        <span :class="getBufferClass(videoBufferLevel)">{{ formatBufferTime(videoBufferLevel) }}</span>
      </div>
      <div class="stat-item">
        <label>Audio Buffer</label>
        <span :class="getBufferClass(audioBufferLevel)">{{ formatBufferTime(audioBufferLevel) }}</span>
      </div>
      <div class="stat-item">
        <label>Buffer Health</label>
        <span :class="getHealthClass()">{{ getHealthStatus() }}</span>
      </div>
      <div class="stat-item">
        <label>Stall Events</label>
        <span>{{ stallCount }}</span>
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
  name: 'BufferChart',
  components: {
    Line
  },
  props: {
    bufferData: {
      type: Array,
      default: () => []
    },
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
  data() {
    return {
      maxDataPoints: 60
    };
  },
  computed: {
    chartData() {
      const labels = this.bufferData.map((_, index) => {
        const secondsAgo = this.bufferData.length - 1 - index;
        return secondsAgo === 0 ? 'Now' : `${secondsAgo}s ago`;
      }).reverse();

      const videoBuffer = this.bufferData.map(data => data.video || 0).reverse();
      const audioBuffer = this.bufferData.map(data => data.audio || 0).reverse();

      return {
        labels,
        datasets: [
          {
            label: 'Video Buffer (s)',
            data: videoBuffer,
            borderColor: '#28a745',
            backgroundColor: 'rgba(40, 167, 69, 0.1)',
            fill: false,
            tension: 0.4,
            pointRadius: 0,
            pointHoverRadius: 4,
            borderWidth: 2
          },
          {
            label: 'Audio Buffer (s)',
            data: audioBuffer,
            borderColor: '#17a2b8',
            backgroundColor: 'rgba(23, 162, 184, 0.1)',
            fill: false,
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
            display: true,
            position: 'top',
            labels: {
              usePointStyle: true,
              pointStyle: 'line',
              color: '#2c3e50'
            }
          },
          tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            titleColor: '#fff',
            bodyColor: '#fff',
            borderColor: '#28a745',
            borderWidth: 1,
            callbacks: {
              label: (context) => {
                return `${context.dataset.label}: ${context.parsed.y.toFixed(1)}s`;
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
            max: 30, // 30 seconds max for better visualization
            grid: {
              color: 'rgba(0, 0, 0, 0.1)'
            },
            ticks: {
              color: '#6c757d',
              callback: (value) => `${value.toFixed(0)}s`
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
    formatBufferTime(seconds) {
      if (!seconds || seconds < 0) return '0.0s';
      return `${seconds.toFixed(1)}s`;
    },
    getBufferClass(bufferLevel) {
      if (bufferLevel < 2) return 'buffer-critical';
      if (bufferLevel < 5) return 'buffer-warning'; 
      return 'buffer-good';
    },
    getHealthClass() {
      const avgBuffer = (this.videoBufferLevel + this.audioBufferLevel) / 2;
      if (avgBuffer < 2) return 'health-critical';
      if (avgBuffer < 5) return 'health-warning';
      return 'health-good';
    },
    getHealthStatus() {
      const avgBuffer = (this.videoBufferLevel + this.audioBufferLevel) / 2;
      if (avgBuffer < 2) return 'Critical';
      if (avgBuffer < 5) return 'Warning';
      return 'Healthy';
    }
  }
};
</script>

<style scoped>
.buffer-chart {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.buffer-chart h3 {
  margin: 0 0 16px 0;
  color: #2c3e50;
  font-size: 1.1rem;
  font-weight: 600;
}

.chart-container {
  height: 200px;
  margin-bottom: 16px;
}

.buffer-stats {
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
  font-weight: 600;
}

.buffer-good, .health-good {
  color: #28a745;
}

.buffer-warning, .health-warning {
  color: #ffc107;
}

.buffer-critical, .health-critical {
  color: #dc3545;
}

@media (max-width: 768px) {
  .chart-container {
    height: 150px;
  }
  
  .buffer-stats {
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }
}
</style>