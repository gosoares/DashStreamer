<template>
  <div class="quality-timeline-chart">
    <div class="chart-header">
      <h3>Quality Timeline</h3>
      <div class="chart-legend">
        <div 
          v-for="quality in qualityLevels" 
          :key="quality.label"
          class="legend-item"
        >
          <div class="legend-color" :style="{ backgroundColor: quality.color }"></div>
          <span class="legend-label">{{ quality.label }}</span>
        </div>
      </div>
    </div>
    
    <div class="chart-container" ref="chartContainer">
      <canvas 
        ref="canvas" 
        @mousemove="handleMouseMove"
        @mouseleave="hideTooltip"
        :width="canvasWidth"
        :height="canvasHeight"
      ></canvas>
      
      <!-- Tooltip -->
      <div 
        v-if="tooltip.visible"
        class="tooltip"
        :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }"
      >
        <div class="tooltip-content">
          <div><strong>Time:</strong> {{ tooltip.timeRange }}</div>
          <div><strong>Quality:</strong> {{ tooltip.resolution }}</div>
          <div><strong>Bitrate:</strong> {{ tooltip.bitrate }}</div>
          <div><strong>Segment:</strong> {{ tooltip.segmentName }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'

export default {
  name: 'QualityTimelineChart',
  props: {
    segmentDownloads: {
      type: Array,
      default: () => []
    },
    videoDuration: {
      type: Number,
      default: 0
    }
  },
  setup(props) {
    const canvas = ref(null)
    const chartContainer = ref(null)
    
    const tooltip = ref({
      visible: false,
      x: 0,
      y: 0,
      timeRange: '',
      resolution: '',
      bitrate: '',
      segmentName: ''
    })

    // Filter video segments and sort by time
    const videoSegments = computed(() => {
      return props.segmentDownloads
        .filter(segment => segment.mediaType === 'video' && !segment.failed)
        .map(segment => ({
          ...segment,
          startTimeSeconds: parseTimeToSeconds(segment.timeRange)
        }))
        .sort((a, b) => a.startTimeSeconds - b.startTimeSeconds)
    })

    // Extract unique quality levels and assign colors
    const qualityLevels = computed(() => {
      const qualities = new Set()
      videoSegments.value.forEach(segment => {
        if (segment.resolution && segment.resolution !== 'N/A') {
          qualities.add(segment.resolution)
        }
      })
      
      const qualityArray = Array.from(qualities).sort((a, b) => {
        // Sort by resolution (height)
        const heightA = parseInt(a.split('×')[1]) || 0
        const heightB = parseInt(b.split('×')[1]) || 0
        return heightA - heightB
      })
      
      return qualityArray.map((quality, index) => ({
        label: quality,
        color: getQualityColor(quality, index, qualityArray.length)
      }))
    })

    // Convert time string to seconds
    function parseTimeToSeconds(timeStr) {
      if (!timeStr || timeStr === 'N/A') return 0
      
      // Handle MM:SS format
      const parts = timeStr.split(':')
      if (parts.length === 2) {
        const minutes = parseInt(parts[0]) || 0
        const seconds = parseInt(parts[1]) || 0
        return minutes * 60 + seconds
      }
      
      // Handle HH:MM:SS format
      if (parts.length === 3) {
        const hours = parseInt(parts[0]) || 0
        const minutes = parseInt(parts[1]) || 0
        const seconds = parseInt(parts[2]) || 0
        return hours * 3600 + minutes * 60 + seconds
      }
      
      // Handle plain seconds
      return parseInt(timeStr) || 0
    }

    // Get color for quality level
    function getQualityColor(quality, index, total) {
      // Extract height from resolution (e.g., "1920×1080" -> 1080)
      const height = parseInt(quality.split('×')[1]) || 0
      
      // Map resolution heights to specific colors (matching presentation diagram)
      const colorMap = {
        2160: '#3b82f6', // 4K - blue
        1440: '#6366f1', // 1440p - indigo
        1080: '#10b981', // 1080p - green
        720: '#f59e0b',  // 720p - amber
        480: '#ebd300',  // 480p - yellow
        360: '#dc2626',  // 360p - darker red
        240: '#9ca3af',  // 240p - gray
        144: '#6b7280',  // 144p - light gray
      }
      
      // Find the closest matching resolution or use a default
      return colorMap[height] || '#9ca3af' // Default gray for unknown resolutions
    }

    // Format seconds to time string
    function formatSeconds(seconds) {
      const mins = Math.floor(seconds / 60)
      const secs = Math.floor(seconds % 60)
      return `${mins}:${secs.toString().padStart(2, '0')}`
    }

    // Draw the timeline chart
    function drawChart() {
      if (!canvas.value) return
      
      const ctx = canvas.value.getContext('2d')
      const { width, height } = canvas.value.getBoundingClientRect()
      
      // Clear canvas
      ctx.clearRect(0, 0, width, height)
      
      if (videoSegments.value.length === 0) {
        // Draw empty state
        ctx.fillStyle = '#666'
        ctx.font = '14px sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText('No video segments downloaded yet', width / 2, height / 2)
        return
      }

      const duration = props.videoDuration || getMaxSegmentTime()
      const isMobile = width < 768
      const padding = { top: 5, right: 12, bottom: 20, left: 12 }
      const chartWidth = width - padding.left - padding.right
      const chartHeight = height - padding.top - padding.bottom
      const barHeight = isMobile ? 14 : 18
      const y = padding.top

      // Draw timeline background
      ctx.fillStyle = '#f5f5f5'
      ctx.fillRect(padding.left, y, chartWidth, barHeight)
      
      // Draw time markers
      ctx.fillStyle = '#999'
      ctx.font = isMobile ? '10px sans-serif' : '12px sans-serif'
      ctx.textAlign = 'center'
      
      const timeMarkers = Math.min(10, Math.floor(duration / 30)) || 5
      for (let i = 0; i <= timeMarkers; i++) {
        const time = (duration / timeMarkers) * i
        const x = padding.left + (chartWidth / timeMarkers) * i
        
        // Draw marker line
        ctx.beginPath()
        ctx.moveTo(x, y)
        ctx.lineTo(x, y + barHeight)
        ctx.strokeStyle = '#ddd'
        ctx.lineWidth = 1
        ctx.stroke()
        
        // Draw time label
        ctx.fillText(formatSeconds(time), x, y + barHeight + 15)
      }

      // Draw segments
      videoSegments.value.forEach((segment, index) => {
        // Estimate segment duration based on gaps between segments or use default
        let segmentDuration = 2 // Default 2-second segments (typical for DASH)
        
        if (index < videoSegments.value.length - 1) {
          const nextSegment = videoSegments.value[index + 1]
          const gap = nextSegment.startTimeSeconds - segment.startTimeSeconds
          if (gap > 0 && gap <= 10) { // Reasonable segment duration
            segmentDuration = gap
          }
        }
        
        const startX = padding.left + (segment.startTimeSeconds / duration) * chartWidth
        const segmentWidth = Math.max(2, (segmentDuration / duration) * chartWidth)
        
        // Ensure segment doesn't overflow chart bounds
        const maxX = padding.left + chartWidth
        const clampedWidth = Math.min(segmentWidth, maxX - startX)
        
        const quality = qualityLevels.value.find(q => q.label === segment.resolution)
        const color = quality ? quality.color : '#999'
        
        ctx.fillStyle = color
        ctx.fillRect(startX, y, clampedWidth, barHeight)
        
        // Add a subtle border to separate segments
        ctx.strokeStyle = '#fff'
        ctx.lineWidth = 1
        ctx.strokeRect(startX, y, clampedWidth, barHeight)
        
        // Store segment bounds for hover detection
        segment._bounds = {
          x: startX,
          y: y,
          width: clampedWidth,
          height: barHeight
        }
      })

      // Draw border
      ctx.strokeStyle = '#ddd'
      ctx.lineWidth = 1
      ctx.strokeRect(padding.left, y, chartWidth, barHeight)
    }

    function getMaxSegmentTime() {
      if (videoSegments.value.length === 0) return 60
      const maxTime = Math.max(...videoSegments.value.map(s => s.startTimeSeconds))
      return maxTime + 2 // Add segment duration
    }

    function handleMouseMove(event) {
      const rect = canvas.value.getBoundingClientRect()
      const x = event.clientX - rect.left
      const y = event.clientY - rect.top
      
      // Check if mouse is over any segment
      const hoveredSegment = videoSegments.value.find(segment => {
        const bounds = segment._bounds
        return bounds && 
               x >= bounds.x && x <= bounds.x + bounds.width &&
               y >= bounds.y && y <= bounds.y + bounds.height
      })
      
      if (hoveredSegment) {
        tooltip.value = {
          visible: true,
          x: event.clientX - rect.left + 10,
          y: event.clientY - rect.top - 10,
          timeRange: hoveredSegment.timeRange || 'N/A',
          resolution: hoveredSegment.resolution || 'N/A',
          bitrate: hoveredSegment.bitrate,
          segmentName: hoveredSegment.segmentName || 'N/A'
        }
        canvas.value.style.cursor = 'pointer'
      } else {
        hideTooltip()
      }
    }

    function hideTooltip() {
      tooltip.value.visible = false
      if (canvas.value) {
        canvas.value.style.cursor = 'default'
      }
    }

    function handleResize() {
      if (!chartContainer.value || !canvas.value) return

      const dpr = window.devicePixelRatio || 1
      const newWidth = chartContainer.value.clientWidth
      const newHeight = 60 // Reduced height

      if (newWidth > 0 && newHeight > 0) {
        canvas.value.width = newWidth * dpr
        canvas.value.height = newHeight * dpr
        canvas.value.style.width = `${newWidth}px`
        canvas.value.style.height = `${newHeight}px`

        const ctx = canvas.value.getContext('2d')
        ctx.scale(dpr, dpr)

        nextTick(() => {
          drawChart()
        })
      }
    }

    // Watch for changes in segments or duration
    watch([videoSegments, () => props.videoDuration], () => {
      nextTick(() => {
        drawChart()
      })
    }, { deep: true })

    onMounted(() => {
      window.addEventListener('resize', handleResize)
      handleResize()
      nextTick(() => {
        drawChart()
      })
    })

    onUnmounted(() => {
      window.removeEventListener('resize', handleResize)
    })

    return {
      canvas,
      chartContainer,
      tooltip,
      qualityLevels,
      handleMouseMove,
      hideTooltip
    }
  }
}
</script>

<style scoped>
.quality-timeline-chart {
  background: white;
  border-radius: 8px;
  padding: 16px 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 16px;
}

.chart-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.2em;
}

.chart-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 3px;
  border: 1px solid #ddd;
}

.legend-label {
  font-size: 0.85em;
  color: #666;
  white-space: nowrap;
}

.chart-container {
  position: relative;
  width: 100%;
  overflow: hidden;
}

canvas {
  display: block;
  width: 100%;
  height: auto;
  cursor: default;
}

.tooltip {
  position: absolute;
  background: rgba(0, 0, 0, 0.9);
  color: white;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 0.85em;
  pointer-events: none;
  z-index: 1000;
  white-space: nowrap;
  max-width: 250px;
}

.tooltip-content > div {
  margin-bottom: 2px;
}

.tooltip-content > div:last-child {
  margin-bottom: 0;
}

@media (max-width: 768px) {
  .chart-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .chart-legend {
    justify-content: flex-start;
    width: 100%;
    overflow-x: auto;
    flex-wrap: nowrap;
    padding-bottom: 4px;
  }
  
  .legend-item {
    min-width: 0;
    flex-shrink: 0;
  }
  
  .legend-label {
    font-size: 0.8em;
  }
  
  .chart-container {
    touch-action: pan-x;
  }
  
  .tooltip {
    font-size: 0.8em;
    padding: 6px 10px;
    max-width: 200px;
  }
}

@media (max-width: 480px) {
  .quality-timeline-chart {
    padding: 16px;
  }
  
  .chart-legend {
    gap: 8px;
  }
  
  .legend-color {
    width: 14px;
    height: 14px;
  }
}
</style>
