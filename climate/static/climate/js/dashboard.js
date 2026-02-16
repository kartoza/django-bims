(function () {
  'use strict';

  var dataEl = document.getElementById('climate-dashboard-data');
  if (!dataEl) {
    return;
  }

  var allData;
  try {
    allData = JSON.parse(dataEl.textContent);
  } catch (err) {
    console.error('Unable to parse dashboard payload', err);
    return;
  }

  if (!allData) {
    return;
  }

  function exportWithPopup(chart, exportType, mimeType) {
    var chartTitle = chart.options.yAxis[0].title.text || 'chart';
    var filename = chartTitle.replace(/[^a-z0-9]/gi, '_').toLowerCase();

    var doExport = function() {
      if (exportType === 'CSV') {
        chart.downloadCSV();
      } else {
        chart.exportChartLocal({
          type: mimeType,
          filename: filename
        });
      }
    };

    if (typeof showDownloadPopup === 'function') {
      showDownloadPopup('IMAGE', chartTitle, function() {
        doExport();
      }, true, null, false);
    } else {
      doExport();
    }
  }

  var exportingOptions = {
    fallbackToExportServer: false,
    menuItemDefinitions: {
      downloadPNG: {
        text: 'Download PNG',
        onclick: function() {
          exportWithPopup(this, 'PNG', 'image/png');
        }
      },
      downloadSVG: {
        text: 'Download SVG',
        onclick: function() {
          exportWithPopup(this, 'SVG', 'image/svg+xml');
        }
      },
      downloadCSV: {
        text: 'Download CSV',
        onclick: function() {
          exportWithPopup(this, 'CSV', 'text/csv');
        }
      }
    },
    buttons: {
      contextButton: {
        menuItems: ['downloadPNG', 'downloadSVG', 'separator', 'downloadCSV'],
        y: -35
      }
    }
  };

  var charts = {
    temperature: null,
    humidity: null,
    rainfall: null
  };

  var rainfallTitles = {
    daily: 'Daily total rainfall',
    monthly: 'Monthly total rainfall',
    annual: 'Annual total rainfall'
  };

  function renderCharts(granularity) {
    var data = allData[granularity];
    if (!data || !data.labels || !data.labels.length) {
      return;
    }

    // Update rainfall chart title
    var rainfallTitle = document.getElementById('rainfall-chart-title');
    if (rainfallTitle) {
      rainfallTitle.textContent = rainfallTitles[granularity] || 'Total rainfall';
    }

    // Temperature Chart (Stock chart with navigator for zoom)
    var temperatureContainer = document.getElementById('temperature-chart');
    if (temperatureContainer && data.temperature) {
      if (charts.temperature) {
        charts.temperature.destroy();
      }
      charts.temperature = Highcharts.stockChart('temperature-chart', {
        chart: {
          type: 'line',
          spacingTop: 40
        },
        title: {
          text: ''
        },
        rangeSelector: {
          enabled: false
        },
        navigator: {
          enabled: true
        },
        scrollbar: {
          enabled: true
        },
        xAxis: {
          categories: data.labels,
          title: {
            text: ''
          },
          labels: {
            rotation: -45,
            style: {
              fontSize: '10px'
            }
          }
        },
        yAxis: {
          title: {
            text: 'Temperature (°C)'
          },
          opposite: false
        },
        legend: {
          enabled: true,
          layout: 'horizontal',
          align: 'center',
          verticalAlign: 'bottom'
        },
        plotOptions: {
          line: {
            marker: {
              enabled: granularity !== 'daily',
              radius: 3
            },
            connectNulls: true
          }
        },
        exporting: exportingOptions,
        series: [
          {
            name: 'Min (°C)',
            data: data.temperature.min,
            color: '#3F51B5'
          },
          {
            name: 'Ave (°C)',
            data: data.temperature.avg,
            color: '#009688'
          },
          {
            name: 'Max (°C)',
            data: data.temperature.max,
            color: '#E91E63'
          }
        ]
      });
    }

    var humidityContainer = document.getElementById('humidity-chart');
    if (humidityContainer && data.humidity) {
      if (charts.humidity) {
        charts.humidity.destroy();
      }
      charts.humidity = Highcharts.stockChart('humidity-chart', {
        chart: {
          type: 'line',
          spacingTop: 40
        },
        title: {
          text: ''
        },
        rangeSelector: {
          enabled: false
        },
        navigator: {
          enabled: true
        },
        scrollbar: {
          enabled: true
        },
        xAxis: {
          categories: data.labels,
          title: {
            text: ''
          },
          labels: {
            rotation: -45,
            style: {
              fontSize: '10px'
            }
          }
        },
        yAxis: {
          title: {
            text: 'Humidity (%)'
          },
          opposite: false
        },
        legend: {
          enabled: true,
          layout: 'horizontal',
          align: 'center',
          verticalAlign: 'bottom'
        },
        plotOptions: {
          line: {
            marker: {
              enabled: granularity !== 'daily',
              radius: 3
            },
            connectNulls: true
          }
        },
        exporting: exportingOptions,
        series: [
          {
            name: 'Min (%)',
            data: data.humidity.min,
            color: '#5C6BC0'
          },
          {
            name: 'Ave (%)',
            data: data.humidity.avg,
            color: '#26A69A'
          },
          {
            name: 'Max (%)',
            data: data.humidity.max,
            color: '#FF7043'
          }
        ]
      });
    }

    var rainfallContainer = document.getElementById('rainfall-chart');
    if (rainfallContainer && data.rainfall) {
      if (charts.rainfall) {
        charts.rainfall.destroy();
      }
      charts.rainfall = Highcharts.chart('rainfall-chart', {
        chart: {
          type: 'column',
          zoomType: 'x',
          spacingTop: 40
        },
        title: {
          text: ''
        },
        xAxis: {
          categories: data.labels,
          title: {
            text: ''
          },
          labels: {
            rotation: -45,
            style: {
              fontSize: '10px'
            }
          }
        },
        yAxis: {
          min: 0,
          title: {
            text: 'Rainfall (mm)'
          }
        },
        legend: {
          layout: 'horizontal',
          align: 'center',
          verticalAlign: 'bottom'
        },
        plotOptions: {
          column: {
            borderRadius: 3
          }
        },
        exporting: exportingOptions,
        series: [
          {
            name: 'Total rainfall (mm)',
            data: data.rainfall.total,
            color: '#4FC3F7'
          }
        ]
      });
    }
  }

  renderCharts('monthly');
  var granularitySelect = document.getElementById('granularity-select');
  if (granularitySelect) {
    granularitySelect.addEventListener('change', function () {
      renderCharts(this.value);
    });
  }
})();
