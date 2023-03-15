let map = null;

function renderWaterTemperatureChart(){
    let startDate = $('#startDate').val();
    let endDate = $('#endDate').val();
    let url = '/api/thermal-data/?site-id='+ siteId  + '&year=' + year + '&startDate=' + startDate + '&endDate=' + endDate
    fetch(url).then(
      response => response.json()
    ).then((data =>{

        for (let i = 0; i < data['date_time'].length; i++) {
            const timestamp = new Date(data['date_time'][i]).getTime()
            for (let dataKey in data) {
                if (dataKey !== 'date_time' && dataKey !== 'days') {
                    if (data[dataKey][i]) {
                        data[dataKey][i] = [timestamp, data[dataKey][i]]
                    }
                }
            }
        }

        Highcharts.Series.prototype.drawPoints = function() { };
        const chartTitle = `Water Temperature - ${year}`
        const chart = new Highcharts.stockChart('water-temperature', {
            title: {
                text: '',
            },
            xAxis: {
                type: 'datetime',
                ordinal: true,
                title: {
                    text: year
                },
                labels: {
                    formatter: function () {
                        return Highcharts.dateFormat('%b %y', this.value)
                    },
                }
            },
            yAxis: {
                title: {
                    text: 'Water Temperature (°C)'
                }
            },
            plotOptions: {
                series: {
                    marker: {
                        enabled: true, radius: 6
                    }
                }
            },
            legend: {
                layout: 'horizontal',
                enabled: true,
                verticalAlign: 'top',
                symbolWidth: 30,
            },
            exporting: {
                filename: chartTitle,
                menuItemDefinitions: {
                    downloadPNG: {
                        onclick: function () {
                            let that = this;
                            showDownloadPopup('CHART', chartTitle, function () {
                                that.exportChart({
                                    type: 'image/png'
                                });
                            })
                        },
                        text: 'Download PNG image'
                    },
                    downloadPDF: {
                        onclick: function () {
                            let that = this;
                            showDownloadPopup('CHART', chartTitle, function () {
                                that.exportChart({
                                    type: 'application/pdf'
                                });
                            })
                        },
                        text: 'Download PDF image'
                    },
                    downloadSVG: {
                        onclick: function () {
                            let that = this;
                            showDownloadPopup('CHART', chartTitle, function () {
                                that.exportChart({
                                    type: 'image/svg+xml'
                                });
                            })
                        },
                        text: 'Download SVG vector image'
                    },
                    downloadCSV2: {
                        onclick: function () {
                            let that = this;
                            showDownloadPopup('TABLE', chartTitle, function () {
                                that.downloadCSV()
                            })
                        },
                        text: 'Download CSV'
                    },
                },
                buttons: {
                    contextButton: {
                        menuItems: [
                            "downloadPNG",
                            "downloadPDF",
                            "downloadSVG",
                            "separator",
                            "downloadCSV2"]
                    }
                }
            },
            series: [
                {
                    name: 'Mean_7',
                    data: data['mean_7'],
                    color: '#000000'
                },
                {
                    name: '95%_low',
                    data: data['95%_low'],
                    color: '#7f7f7f'
                },
                {
                    name: '95%_up',
                    data: data['95%_up'],
                    color: '#7f7f7f'
                },
                {
                    name: 'L95%_1SD',
                    data: data['L95%_1SD'],
                    color: '#bfbfbf'

                },
                {
                    name: 'U95%_1SD',
                    data: data['U95%_1SD'],
                    color: '#bfbfbf'

                },
                {
                    name: 'L95%_2SD',
                    data: data['L95%_2SD'],
                    color: '#bfbfbf'

                },
                {
                    name: 'U95%_2SD',
                    data: data['U95%_2SD'],
                    color: '#bfbfbf'

                },
                {
                    name: 'Min_7',
                    data: data['min_7'],
                    color: '#0070c0'
                },
                {
                    name: 'Max_7',
                    data: data['max_7'],
                    color: '#ff0000'
                }
            ]
        });
        return chart

    }))
}

function changeYear(selectObject) {
  let value = selectObject.value;
  let url = new URL(window.location);
  window.location.href = `/water-temperature/${siteId}/${value}/${url.search}`;
}

$(function () {
    createDashboardMap(map, coordinates);
    renderWaterTemperatureChart()
    renderSourceReferences()

    $('.download-map').click(function () {
        map.once('postrender', function (event) {
            showDownloadPopup('IMAGE', 'Map', function () {
                var canvas = $('#map');
                html2canvas(canvas, {
                    useCORS: true,
                    background: '#FFFFFF',
                    allowTaint: false,
                    onrendered: function (canvas) {
                        let link = document.createElement('a');
                        link.setAttribute("type", "hidden");
                        link.href = canvas.toDataURL("image/png");
                        link.download = 'map.png';
                        document.body.appendChild(link);
                        link.click();
                        link.remove();
                    }
                });
            })
        });
        map.renderSync();
    })

    $(".date-input").datepicker({
        changeMonth: true,
        changeYear: true,
        dateFormat: 'yy-mm-dd',
        yearRange: `${availableYears[0]}:${availableYears.at(-1)}`
    });

    $('#update-date').click(() => {
        let startDate = $('#startDate').val();
        let endDate = $('#endDate').val();
        let startDateYear = startDate.split('-')[0];
        let endDateYear = endDate.split('-')[0];
        if (startDateYear !== endDateYear) {
            alert('Start and end date must be within the same year');
            return;
        }
        let url = new URL(window.location);
        url.searchParams.set('startDate', startDate)
        url.searchParams.set('endDate', endDate)
        window.location.href = `/water-temperature/${siteId}/${startDateYear}/${url.search}`;
    })
});