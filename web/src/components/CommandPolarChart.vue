<template>
  <div class="container">
    <h3 class="chart-title">현재 작업 명령어 분석</h3>
    <div v-if="hasData" class="chart-wrapper">
      <canvas ref="polarChart"></canvas>
    </div>
    <div v-else class="no-data">
      <p>진행 중인 작업이 없습니다</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from "vue";
import { Chart } from "chart.js/auto";

const props = defineProps({
  labels: Array,
  data: Array,
});

const polarChart = ref(null);
let chartInstance = null;

const hasData = computed(() => {
  return props.labels && props.labels.length > 0 && props.data && props.data.length > 0;
});

const createChart = () => {
  if (!hasData.value || !polarChart.value) return;
  
  const ctx = polarChart.value.getContext("2d");
  
  if (chartInstance) {
    chartInstance.destroy();
  }
  
  chartInstance = new Chart(ctx, {
    type: "polarArea",
    data: {
      labels: props.labels,
      datasets: [
        {
          label: "명령어 실행 횟수",
          data: props.data,
          backgroundColor: [
            "rgba(255, 99, 132, 0.6)",
            "rgba(54, 162, 235, 0.6)",
            "rgba(255, 206, 86, 0.6)",
            "rgba(75, 192, 192, 0.6)",
            "rgba(153, 102, 255, 0.6)",
            "rgba(255, 159, 64, 0.6)",
            "rgba(201, 203, 207, 0.6)",
            "rgba(255, 99, 255, 0.6)",
          ],
          borderColor: [
            "rgba(255, 99, 132, 1)",
            "rgba(54, 162, 235, 1)",
            "rgba(255, 206, 86, 1)",
            "rgba(75, 192, 192, 1)",
            "rgba(153, 102, 255, 1)",
            "rgba(255, 159, 64, 1)",
            "rgba(201, 203, 207, 1)",
            "rgba(255, 99, 255, 1)",
          ],
          borderWidth: 2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            boxWidth: 12,
            padding: 10,
          },
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const label = context.label || '';
              const value = context.parsed || 0;
              return `${label}: ${value}회`;
            },
            title: function(context) {
              return '명령어 실행 횟수';
            }
          }
        },
      },
      scales: {
        r: {
          beginAtZero: true,
          ticks: {
            display: true,
            stepSize: 1,
          },
        },
      },
    },
  });
};

watch(
  () => [props.labels, props.data],
  () => {
    if (hasData.value) {
      if (chartInstance) {
        chartInstance.data.labels = props.labels;
        chartInstance.data.datasets[0].data = props.data;
        chartInstance.update();
      } else {
        createChart();
      }
    } else if (chartInstance) {
      chartInstance.destroy();
      chartInstance = null;
    }
  },
  { deep: true }
);

onMounted(() => {
  if (hasData.value) {
    createChart();
  }
});
</script>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  height: 100%;
  padding: 1rem;
}

.chart-title {
  color: #8D98A6;
  margin-bottom: 1rem;
  text-align: center;
  font-size: 1.1rem;
}

.chart-wrapper {
  width: 100%;
  height: 80%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.no-data {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
  color: #8D98A6;
  font-size: 1.1rem;
}

canvas {
  max-width: 280px;
  max-height: 280px;
}
</style>