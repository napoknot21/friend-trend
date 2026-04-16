<template>
  <div class="chart-frame">
    <Line v-if="hasData" :data="chartData" :options="chartOptions" />
    <div v-else class="chart-empty">No timeline data for the current filters.</div>
  </div>
</template>

<script>
import {
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LineElement,
  LinearScale,
  PointElement,
  Tooltip
} from 'chart.js'
import { Line } from 'vue-chartjs'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend, Filler)

export default {
  name: 'TimelineChart',
  components: { Line },
  props: {
    items: {
      type: Array,
      default: () => []
    }
  },
  computed: {
    hasData() {
      return this.items.length > 0
    },
    chartData() {
      return {
        labels: this.items.map(item => item.date),
        datasets: [
          {
            label: 'Views',
            data: this.items.map(item => item.total),
            borderColor: '#ff7a18',
            backgroundColor: 'rgba(255, 122, 24, 0.16)',
            fill: true,
            tension: 0.35,
            borderWidth: 3,
            pointRadius: 3,
            pointBackgroundColor: '#ffb36b',
            yAxisID: 'y'
          },
          {
            label: 'Avg confidence',
            data: this.items.map(item => item.avg_confidence),
            borderColor: '#25b6a1',
            backgroundColor: '#25b6a1',
            tension: 0.3,
            borderWidth: 2,
            pointRadius: 3,
            yAxisID: 'y1'
          }
        ]
      }
    },
    chartOptions() {
      return {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false
        },
        plugins: {
          legend: {
            labels: {
              color: '#334155',
              usePointStyle: true
            }
          }
        },
        scales: {
          x: {
            ticks: { color: '#334155' },
            grid: { color: '#f1f5f9' }
          },
          y: {
            position: 'left',
            beginAtZero: true,
            ticks: { color: '#64748b', stepSize: 1 },
            grid: { color: '#e2e8f0' }
          },
          y1: {
            position: 'right',
            beginAtZero: true,
            max: 100,
            ticks: {
              color: '#64748b',
              callback: value => `${value}%`
            },
            grid: { drawOnChartArea: false }
          }
        }
      }
    }
  }
}
</script>

<style scoped>
.chart-frame {
  min-height: 320px;
}

.chart-empty {
  min-height: 320px;
  display: grid;
  place-items: center;
  color: #64748b;
}
</style>
