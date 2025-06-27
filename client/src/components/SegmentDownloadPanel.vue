<template>
  <div class="segment-download-panel">
    <div class="panel-header">
      <h3>Segment Downloads</h3>
      <div class="panel-controls">
        <select v-model="selectedFilter" class="filter-select">
          <option value="all">All Segments</option>
          <option value="video">Video Only</option>
          <option value="audio">Audio Only</option>
        </select>
      </div>
    </div>
    
    <div class="segment-stats">
      <div class="stat-item">
        <label>Total Segments</label>
        <span>{{ filteredSegments.length }}</span>
      </div>
      <div class="stat-item">
        <label>Total Data</label>
        <span>{{ totalDataFormatted }}</span>
      </div>
    </div>
    
    <div class="segment-list" v-if="successfulSegments.length > 0">
      <div class="segment-list-header">
        <div class="col-name">Segment</div>
        <div class="col-resolution">Resolution</div>
        <div class="col-bitrate">Bitrate</div>
        <div class="col-timerange">Start Time</div>
        <div class="col-type">Type</div>
        <div class="col-size">Size</div>
        <div class="col-time">Time</div>
      </div>
      
      <div class="segment-list-body">
        <div 
          v-for="segment in successfulSegments" 
          :key="segment.id"
          class="segment-row"
        >
          <div class="col-name" :title="segment.url">
            {{ segment.segmentName }}
          </div>
          <div class="col-resolution">{{ segment.mediaType === 'video' ? segment.resolution : '-' }}</div>
          <div class="col-bitrate">{{ segment.mediaType === 'video' ? segment.bitrate : '-' }}</div>
          <div class="col-timerange">{{ segment.mediaType === 'video' ? segment.timeRange : '-' }}</div>
          <div class="col-type">
            <span class="type-badge" :class="segment.mediaType">
              {{ segment.mediaType }}
            </span>
          </div>
          <div class="col-size">{{ segment.sizeFormatted }}</div>
          <div class="col-time">{{ segment.timestamp }}</div>
        </div>
      </div>
    </div>
    
    <div v-else class="no-segments">
      <p>No segments downloaded yet. Start video playback to see download activity.</p>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'SegmentDownloadPanel',
  props: {
    segmentDownloads: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      selectedFilter: 'video'
    }
  },
  computed: {
    filteredSegments() {
      // First filter by success (not failed), then by media type
      const successful = this.segmentDownloads.filter(s => !s.failed)
      
      if (this.selectedFilter === 'all') {
        return successful
      }
      return successful.filter(segment => 
        segment.mediaType === this.selectedFilter
      )
    },
    
    successfulSegments() {
      return this.filteredSegments
    },
    
    totalDataFormatted() {
      const totalBytes = this.filteredSegments
        .reduce((sum, segment) => sum + segment.size, 0)
      
      return this.formatBytes(totalBytes)
    }
  },
  methods: {
    
    formatBytes(bytes) {
      if (bytes === 0) return '0 B'
      const k = 1024
      const sizes = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    },
    
    formatSpeed(bytesPerSecond) {
      if (bytesPerSecond === 0) return '0 B/s'
      const k = 1024
      const sizes = ['B/s', 'KB/s', 'MB/s', 'GB/s']
      const i = Math.floor(Math.log(bytesPerSecond) / Math.log(k))
      return parseFloat((bytesPerSecond / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }
  }
}
</script>

<style scoped>
.segment-download-panel {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e0e0e0;
}

.panel-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.2em;
}

.panel-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.filter-select {
  padding: 4px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9em;
}

.clear-btn {
  padding: 4px 12px;
  background: #f44336;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9em;
  transition: background-color 0.2s;
}

.clear-btn:hover {
  background: #d32f2f;
}

.segment-stats {
  display: flex;
  gap: 20px;
  margin-bottom: 16px;
  padding: 12px;
  background: #f5f5f5;
  border-radius: 6px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-item label {
  font-size: 0.85em;
  color: #666;
  margin-bottom: 4px;
}

.stat-item span {
  font-weight: bold;
  color: #333;
}

.segment-list {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  overflow: hidden;
}

.segment-list-header {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1fr 1fr 1fr;
  gap: 10px;
  padding: 12px;
  background: #f8f9fa;
  font-weight: bold;
  font-size: 0.9em;
  color: #555;
  border-bottom: 1px solid #e0e0e0;
}

.segment-list-body {
  max-height: 600px;
  overflow-y: auto;
}

.segment-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1fr 1fr 1fr;
  gap: 10px;
  padding: 10px 12px;
  border-bottom: 1px solid #f0f0f0;
  font-size: 0.85em;
  transition: background-color 0.2s;
}

.segment-row:hover {
  background: #f8f9fa;
}

.segment-row.failed {
  background: #ffebee;
}

.segment-row.failed:hover {
  background: #ffcdd2;
}

.col-name {
  font-family: monospace;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.type-badge {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 12px;
  font-size: 0.75em;
  font-weight: bold;
  text-transform: uppercase;
}

.type-badge.video {
  background: #e3f2fd;
  color: #1976d2;
}

.type-badge.audio {
  background: #f3e5f5;
  color: #7b1fa2;
}

.type-badge.unknown {
  background: #fafafa;
  color: #616161;
}

.status-indicator {
  font-weight: bold;
  font-size: 1.1em;
}

.status-indicator.success {
  color: #4caf50;
}

.status-indicator.failed {
  color: #f44336;
}

.no-segments {
  text-align: center;
  padding: 40px 20px;
  color: #666;
}

.no-segments p {
  margin: 0;
  font-style: italic;
}

@media (max-width: 768px) {
  .segment-stats {
    flex-direction: column;
    gap: 10px;
  }
  
  .stat-item {
    flex-direction: row;
    justify-content: space-between;
  }
  
  .segment-list-header,
  .segment-row {
    grid-template-columns: 1fr;
    gap: 5px;
  }
  
  .segment-list-header > div,
  .segment-row > div {
    display: flex;
    justify-content: space-between;
  }
  
  .segment-list-header > div:before,
  .segment-row > div:before {
    content: attr(class);
    font-weight: bold;
    text-transform: capitalize;
  }
}
</style>