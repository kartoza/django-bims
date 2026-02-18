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

  function labelToTimestamp(label, granularity) {
    if (granularity === 'daily') {
      return Date.parse(label);
    } else if (granularity === 'annual') {
      return Date.parse(label + '-01-01');
    } else {
      // "Mon YYYY" format
      return Date.parse('01 ' + label);
    }
  }

  function pairedData(labels, values, granularity) {
    var result = [];
    for (var i = 0; i < labels.length; i++) {
      var ts = labelToTimestamp(labels[i], granularity);
      result.push([ts, values[i]]);
    }
    return result;
  }

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
          type: 'datetime',
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
            data: pairedData(data.labels, data.temperature.min, granularity),
            color: '#3F51B5'
          },
          {
            name: 'Ave (°C)',
            data: pairedData(data.labels, data.temperature.avg, granularity),
            color: '#009688'
          },
          {
            name: 'Max (°C)',
            data: pairedData(data.labels, data.temperature.max, granularity),
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
          type: 'datetime',
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
            data: pairedData(data.labels, data.humidity.min, granularity),
            color: '#5C6BC0'
          },
          {
            name: 'Ave (%)',
            data: pairedData(data.labels, data.humidity.avg, granularity),
            color: '#26A69A'
          },
          {
            name: 'Max (%)',
            data: pairedData(data.labels, data.humidity.max, granularity),
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

      let rainfallSeries = [];

      if (granularity === 'monthly' && data.rainfall.historical) {
        rainfallSeries.push({
          name: 'Monthly average over all time',
          data: data.rainfall.historical,
          color: '#146082'
        });
      }

      rainfallSeries.push(
        {
          name: 'Average monthly total rainfall (for dates selected)',
          data: data.rainfall.total,
          color: '#E97132'
        });

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
        series: rainfallSeries
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
