(function () {
  'use strict';

  if (typeof Chart === 'undefined') {
    return;
  }

  var dataEl = document.getElementById('climate-dashboard-data');
  if (!dataEl) {
    return;
  }

  var parsedData;
  try {
    parsedData = JSON.parse(dataEl.textContent);
  } catch (err) {
    console.error('Unable to parse dashboard payload', err);
    return;
  }

  if (!parsedData || !parsedData.labels || !parsedData.labels.length) {
    return;
  }

  var defaultOptions = {
    maintainAspectRatio: false,
    responsive: true,
    legend: {
      display: true,
      position: 'bottom'
    },
    tooltips: {
      intersect: false,
      mode: 'index'
    },
    scales: {
      xAxes: [{
        ticks: { autoSkip: false }
      }],
      yAxes: [{
        ticks: {
          beginAtZero: false
        }
      }]
    }
  };

  var temperatureCtx = document.getElementById('temperature-chart');
  if (temperatureCtx && parsedData.temperature) {
    new Chart(temperatureCtx.getContext('2d'), {
      type: 'line',
      data: {
        labels: parsedData.labels,
        datasets: [
          {
            label: 'Min (°C)',
            data: parsedData.temperature.min,
            borderColor: '#3F51B5',
            backgroundColor: 'rgba(63,81,181,0.15)',
            lineTension: 0.2,
            spanGaps: true,
            fill: false
          },
          {
            label: 'Ave (°C)',
            data: parsedData.temperature.avg,
            borderColor: '#009688',
            backgroundColor: 'rgba(0,150,136,0.15)',
            lineTension: 0.2,
            spanGaps: true,
            fill: false
          },
          {
            label: 'Max (°C)',
            data: parsedData.temperature.max,
            borderColor: '#E91E63',
            backgroundColor: 'rgba(233,30,99,0.15)',
            lineTension: 0.2,
            spanGaps: true,
            fill: false
          }
        ]
      },
      options: defaultOptions
    });
  }

  var humidityCtx = document.getElementById('humidity-chart');
  if (humidityCtx && parsedData.humidity) {
    new Chart(humidityCtx.getContext('2d'), {
      type: 'line',
      data: {
        labels: parsedData.labels,
        datasets: [
          {
            label: 'Min (%)',
            data: parsedData.humidity.min,
            borderColor: '#5C6BC0',
            backgroundColor: 'rgba(92,107,192,0.15)',
            spanGaps: true,
            fill: false
          },
          {
            label: 'Ave (%)',
            data: parsedData.humidity.avg,
            borderColor: '#26A69A',
            backgroundColor: 'rgba(38,166,154,0.15)',
            spanGaps: true,
            fill: false
          },
          {
            label: 'Max (%)',
            data: parsedData.humidity.max,
            borderColor: '#FF7043',
            backgroundColor: 'rgba(255,112,67,0.15)',
            spanGaps: true,
            fill: false
          }
        ]
      },
      options: defaultOptions
    });
  }

  var rainfallCtx = document.getElementById('rainfall-chart');
  if (rainfallCtx && parsedData.rainfall) {
    new Chart(rainfallCtx.getContext('2d'), {
      type: 'bar',
      data: {
        labels: parsedData.labels,
        datasets: [
          {
            label: 'Total rainfall (mm)',
            data: parsedData.rainfall.total,
            backgroundColor: '#4FC3F7',
            borderColor: '#039BE5',
            borderWidth: 1
          }
        ]
      },
      options: Object.assign({}, defaultOptions, {
        scales: {
          xAxes: [{
            ticks: { autoSkip: false },
            gridLines: { display: false }
          }],
          yAxes: [{
            ticks: {
              beginAtZero: true
            }
          }]
        }
      })
    });
  }
})();
