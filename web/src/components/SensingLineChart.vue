<template>
    <div class="container">
      <h2 class="num-title">{{ title || 'AGV 작업 히스토리' }}</h2>
      <canvas ref="lineChart"></canvas>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted, watch } from "vue";
  import { Chart } from "chart.js/auto";
  
  const props = defineProps({
    labels: Array,
    num1Data: Array,
    num2Data: Array,
    workIds: Array,
    title: String,
  });
  
  const lineChart = ref(null);
  let chartInstance = null;
  const totalDuration = 1500;
  
  const createChart = () => {
    const ctx = lineChart.value.getContext("2d");
  
    if (chartInstance) {
      chartInstance.destroy();
    }
  
    const delayBetweenPoints = totalDuration / (props.num1Data?.length || 1);
  
    const previousY = (ctx) =>
      ctx.index === 0
        ? ctx.chart.scales.y.getPixelForValue(100)
        : ctx.chart
            .getDatasetMeta(ctx.datasetIndex)
            .data[ctx.index - 1].getProps(["y"], true).y;
  
    const animation = {
      x: {
        type: "number",
        easing: "linear",
        duration: delayBetweenPoints,
        from: NaN,
        delay(ctx) {
          if (ctx.type !== "data" || ctx.xStarted) return 0;
          ctx.xStarted = true;
          return ctx.index * delayBetweenPoints;
        },
      },
      y: {
        type: "number",
        easing: "linear",
        duration: delayBetweenPoints,
        from: previousY,
        delay(ctx) {
          if (ctx.type !== "data" || ctx.yStarted) return 0;
          ctx.yStarted = true;
          return ctx.index * delayBetweenPoints;
        },
      },
    };
  
    chartInstance = new Chart(ctx, {
      type: "line",
      data: {
        labels: props.labels || [],
        datasets: [
          {
            label: "작업 소요 시간 (초)",
            borderColor: "#e74c3c",
            backgroundColor: "rgba(231, 76, 60, 0.1)",
            borderWidth: 3,
            radius: 6,
            data: props.num1Data || [],
            tension: 0.4,
            yAxisID: 'y',
          },
          {
            label: "충돌 횟수",
            borderColor: "#3498db",
            backgroundColor: "rgba(52, 152, 219, 0.1)",
            borderWidth: 3,
            radius: 6,
            data: props.num2Data || [],
            tension: 0.4,
            yAxisID: 'y1',
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation,
        interaction: {
          mode: 'index',
          intersect: false,
        },
        plugins: {
          legend: {
            display: true,
            position: 'top',
            labels: {
              usePointStyle: true,
              padding: 20,
            },
          },
          tooltip: {
            mode: 'index',
            intersect: false,
            callbacks: {
              title: function(context) {
                const index = context[0].dataIndex;
                const workId = props.workIds && props.workIds[index] ? props.workIds[index] : '';
                const timeLabel = context[0].label;
                return workId ? `작업 ID: ${workId}\n완료시간: ${timeLabel}` : `완료시간: ${timeLabel}`;
              },
              label: function(context) {
                let label = context.dataset.label || '';
                if (label) {
                  label += ': ';
                }
                if (context.datasetIndex === 0) {
                  label += context.parsed.y + '초';
                } else {
                  label += context.parsed.y + '회';
                }
                return label;
              }
            }
          },
        },
        scales: {
          x: {
            display: true,
            title: {
              display: true,
              text: '작업 완료 시간',
              font: {
                size: 14,
                weight: 'bold'
              }
            },
            grid: {
              display: true,
              color: 'rgba(0, 0, 0, 0.1)'
            },
            ticks: {
              maxRotation: 45,
              minRotation: 0
            }
          },
          y: {
            type: 'linear',
            display: true,
            position: 'left',
            title: {
              display: true,
              text: '작업 소요 시간 (초)',
              color: '#e74c3c',
              font: {
                size: 14,
                weight: 'bold'
              }
            },
            beginAtZero: true,
            grid: {
              display: true,
              color: 'rgba(231, 76, 60, 0.1)'
            },
            ticks: {
              color: '#e74c3c',
              font: {
                weight: 'bold'
              }
            }
          },
          y1: {
            type: 'linear',
            display: true,
            position: 'right',
            title: {
              display: true,
              text: '충돌 횟수',
              color: '#3498db',
              font: {
                size: 14,
                weight: 'bold'
              }
            },
            beginAtZero: true,
            grid: {
              drawOnChartArea: false,
            },
            ticks: {
              color: '#3498db',
              font: {
                weight: 'bold'
              },
              stepSize: 1
            }
          },
        },
      },
    });
  };
  
  onMounted(() => {
    createChart();
  });
  
  watch(
    () => [props.labels, props.num1Data, props.num2Data],
    () => {
      if (chartInstance) {
        chartInstance.data.labels = props.labels || [];
        chartInstance.data.datasets[0].data = props.num1Data || [];
        chartInstance.data.datasets[1].data = props.num2Data || [];
        chartInstance.update();
      } else {
        createChart();
      }
    },
    { deep: true }
  );
  </script>
  
  <style scoped>
  .container {
    width: 95%;
    height: 95%;
    display: flex;
    flex-direction: column;
    padding: 1rem;
  }
  
  .num-title {
    color: #8D98A6;
    margin-bottom: 1rem;
    text-align: center;
    font-size: 1.2rem;
    font-weight: bold;
  }
  
  canvas {
    width: 100% !important;
    height: 85% !important;
  }
  </style>