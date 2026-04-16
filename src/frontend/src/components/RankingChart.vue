<template>
  <div class="chart-frame">
    <Bar v-if="hasData" :data="chartData" :options="chartOptions" />
    <div v-else class="chart-empty">No ranking data for the current filters.</div>
  </div>
</template>

<script>
import { BarElement, CategoryScale, Chart as ChartJS, Legend, LinearScale, Tooltip } from 'chart.js'
import { Bar } from 'vue-chartjs'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

export default {
  name: 'RankingChart',
  components: { Bar },
  props: {
    items: {
      type: Array,
      default: () => []
    },
    color: {
      type: String,
      default: '#ff7a18'
    }
  },
  computed: {
    hasData() {
      return this.items.length > 0
    },
    chartData() {
      return {
        labels: this.items.map(item => item.label),
        datasets: [
          {
            label: 'Views',
            data: this.items.map(item => item.count),
            backgroundColor: this.color,
            borderRadius: 12,
            borderSkipped: false
          }
        ]
      }
    },
    chartOptions() {
      return {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: context => {
                const item = this.items[context.dataIndex]
                return `${item.count} views, ${item.avg_confidence}% avg confidence`
              }
            }
          }
        },
        scales: {
          x: {
            beginAtZero: true,
            ticks: { color: '#64748b', stepSize: 1 },
            grid: { color: '#e2e8f0' }
          },
          y: {
            ticks: {
              color: '#334155',
              callback: (_, index) => {
                const label = this.items[index]?.label || ''
                return label.length > 22 ? `${label.slice(0, 22)}...` : label
              }
            },
            grid: { display: false }
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
