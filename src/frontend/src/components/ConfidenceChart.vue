<template>
  <div class="chart-frame">
    <Bar v-if="hasData" :data="chartData" :options="chartOptions" />
    <div v-else class="chart-empty">No confidence data for the current filters.</div>
  </div>
</template>

<script>
import { BarElement, CategoryScale, Chart as ChartJS, Legend, LinearScale, Tooltip } from 'chart.js'
import { Bar } from 'vue-chartjs'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

export default {
  name: 'ConfidenceChart',
  components: { Bar },
  props: {
    items: {
      type: Array,
      default: () => []
    }
  },
  computed: {
    hasData() {
      return this.items.some(item => item.count > 0)
    },
    chartData() {
      return {
        labels: this.items.map(item => item.label),
        datasets: [
          {
            label: 'Views',
            data: this.items.map(item => item.count),
            backgroundColor: ['#5b8def', '#4bc0c8', '#25b6a1', '#ffb36b', '#ff7a18'],
            borderRadius: 12,
            borderSkipped: false,
            maxBarThickness: 48
          }
        ]
      }
    },
    chartOptions() {
      return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          }
        },
        scales: {
          x: {
            ticks: { color: '#334155' },
            grid: { display: false }
          },
          y: {
            beginAtZero: true,
            ticks: {
              color: '#64748b',
              stepSize: 1
            },
            grid: {
              color: '#e2e8f0'
            }
          }
        }
      }
    }
  }
}
</script>

<style scoped>
.chart-frame {
  min-height: 300px;
}

.chart-empty {
  min-height: 300px;
  display: grid;
  place-items: center;
  color: #64748b;
}
</style>
