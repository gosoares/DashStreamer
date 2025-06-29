<template>
  <div class="buffer-stats">
    <div class="header">
      <h3>Buffer Status</h3>
      <span class="current-level" :class="getBufferClass(videoBufferLevel)">
        {{ formatBufferTime(videoBufferLevel) }}
      </span>
    </div>
    
    <!-- Buffer Chart -->
    <div class="buffer-chart" ref="chartContainer">
      <canvas 
        ref="canvas" 
        :width="canvasWidth"
        :height="canvasHeight"
      ></canvas>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'

export default {
  name: 'BufferStats',
  props: {
    videoBufferLevel: {
      type: Number,
      default: 0
    }
  },
  setup(props) {
    const canvas = ref(null)
    const chartContainer = ref(null)
    const canvasWidth = ref(300)
    const canvasHeight = ref(50)
    
    // Buffer history for chart
    const bufferHistory = ref([])
    const maxHistoryLength = 60 // 60 data points for history
    
    const formatBufferTime = (seconds) => {
      if (!seconds || seconds < 0) return '0.0s';
      return `${seconds.toFixed(1)}s`;
    }
    
    const getBufferClass = (bufferLevel) => {
      if (bufferLevel < 2) return 'buffer-critical';
      if (bufferLevel < 5) return 'buffer-warning'; 
      return 'buffer-good';
    }
    
    const drawBufferChart = () => {
      if (!canvas.value) return
      
      const ctx = canvas.value.getContext('2d')
      const { width, height } = canvas.value
      
      // Clear canvas
      ctx.clearRect(0, 0, width, height)
      
      const padding = 6
      const chartWidth = width - padding * 2
      const chartHeight = height - padding * 2
      const maxBuffer = 30 // Maximum buffer seconds to show
      
      // Draw background
      ctx.fillStyle = '#f8f9fa'
      ctx.fillRect(padding, padding, chartWidth, chartHeight)
      
      // Draw buffer zones
      const criticalHeight = (2 / maxBuffer) * chartHeight
      const warningHeight = (5 / maxBuffer) * chartHeight
      
      // Critical zone (0-2s) - red
      ctx.fillStyle = 'rgba(220, 53, 69, 0.1)'
      ctx.fillRect(padding, padding + chartHeight - criticalHeight, chartWidth, criticalHeight)
      
      // Warning zone (2-5s) - yellow
      ctx.fillStyle = 'rgba(255, 193, 7, 0.1)'
      ctx.fillRect(padding, padding + chartHeight - warningHeight, chartWidth, warningHeight - criticalHeight)
      
      // Good zone (5s+) - green
      ctx.fillStyle = 'rgba(40, 167, 69, 0.1)'
      ctx.fillRect(padding, padding, chartWidth, chartHeight - warningHeight)
      
      // Draw buffer history line
      if (bufferHistory.value.length > 1) {
        ctx.beginPath()
        ctx.strokeStyle = '#007bff'
        ctx.lineWidth = 2
        
        bufferHistory.value.forEach((level, index) => {
          const x = padding + (index / (maxHistoryLength - 1)) * chartWidth
          const y = padding + chartHeight - Math.min((level / maxBuffer) * chartHeight, chartHeight)
          
          if (index === 0) {
            ctx.moveTo(x, y)
          } else {
            ctx.lineTo(x, y)
          }
        })
        
        ctx.stroke()
      }
      
      // Draw current buffer level indicator
      const currentLevel = props.videoBufferLevel
      const currentY = padding + chartHeight - Math.min((currentLevel / maxBuffer) * chartHeight, chartHeight)
      
      // Current level dot
      ctx.beginPath()
      ctx.fillStyle = currentLevel < 2 ? '#dc3545' : currentLevel < 5 ? '#ffc107' : '#28a745'
      ctx.arc(padding + chartWidth - 5, currentY, 4, 0, 2 * Math.PI)
      ctx.fill()
      
      // Border
      ctx.strokeStyle = '#dee2e6'
      ctx.lineWidth = 1
      ctx.strokeRect(padding, padding, chartWidth, chartHeight)
    }
    
    const updateBufferHistory = () => {
      bufferHistory.value.push(props.videoBufferLevel)
      if (bufferHistory.value.length > maxHistoryLength) {
        bufferHistory.value.shift()
      }
      nextTick(() => {
        drawBufferChart()
      })
    }
    
    const handleResize = () => {
      if (!chartContainer.value) return
      
      const containerWidth = chartContainer.value.clientWidth
      canvasWidth.value = Math.max(250, containerWidth - 20)
      
      nextTick(() => {
        drawBufferChart()
      })
    }
    
    // Watch for buffer level changes
    watch(() => props.videoBufferLevel, () => {
      updateBufferHistory()
    })
    
    onMounted(() => {
      window.addEventListener('resize', handleResize)
      handleResize()
      
      // Initialize with current value
      updateBufferHistory()
    })
    
    onUnmounted(() => {
      window.removeEventListener('resize', handleResize)
    })
    
    return {
      canvas,
      chartContainer,
      canvasWidth,
      canvasHeight,
      formatBufferTime,
      getBufferClass
    }
  }
};
</script>

<style scoped>
.buffer-stats {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.buffer-stats h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.1rem;
  font-weight: 600;
}

.current-level {
  font-size: 1rem;
  font-weight: 600;
}

.buffer-chart {
  position: relative;
  width: 100%;
}

canvas {
  display: block;
  width: 100%;
  height: auto;
  border-radius: 4px;
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

@media (max-width: 480px) {
  .buffer-stats {
    padding: 10px;
  }
  
  .header {
    margin-bottom: 6px;
  }
  
  .buffer-stats h3 {
    font-size: 1rem;
  }
  
  .current-level {
    font-size: 0.9rem;
  }
}
</style>
