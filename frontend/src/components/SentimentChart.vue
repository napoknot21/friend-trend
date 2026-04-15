<template>
  <div class="chart-frame">
    <Doughnut v-if="hasData" :data="chartData" :options="chartOptions" />
    <div v-else class="chart-empty">No sentiment data for the current filters.</div>
  </div>
</template>

<script>
import { ArcElement, Chart as ChartJS, Legend, Tooltip } from 'chart.js'
import { Doughnut } from 'vue-chartjs'

ChartJS.register(ArcElement, Tooltip, Legend)

export default {
  name: 'SentimentChart',
  components: { Doughnut },
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
            data: this.items.map(item => item.count),
            backgroundColor: ['#34d399', '#fb7185', '#fbbf24'],
            borderColor: ['#6ee7b7', '#fda4af', '#fcd34d'],
            borderWidth: 2,
            hoverOffset: 8
          }
        ]
      }
    },
    chartOptions() {
      return {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '62%',
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              color: '#334155',
              padding: 18,
              usePointStyle: true,
              pointStyle: 'circle'
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
