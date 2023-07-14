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

function fetchThreshold() {
    let url = `/api/water-temperature-threshold/?location_site=${siteId}`;
    $.ajax({
        type: 'GET',
        url: url,
        success: function (data) {
            $('.loading-threshold').hide();
            $('.threshold_data').prop("disabled", false);
            $('#maximum_threshold').val(data['maximum_threshold'])
            $('#minimum_threshold').val(data['minimum_threshold'])
            $('#mean_threshold').val(data['mean_threshold'])
            $('#record_length').val(data['record_length'])
            $('#degree_days').val(data['degree_days'])
        },
        error: function () {
            console.error('Error fetching threshold');
        }
    })
}

$('.edit-threshold').click(function () {
    fetchThreshold();
})


$(function () {
    createDashboardMap(map, coordinates);
    renderWaterTemperatureChart()
    renderSourceReferences()
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

    $('#threshold-form').on('submit', function(e) {
        e.preventDefault();  // Prevent the form from submitting normally
        $('.threshold_data').prop("disabled", true);
        const postData = {
            'maximum_threshold': $('#maximum_threshold').val(),
            'minimum_threshold': $('#minimum_threshold').val(),
            'mean_threshold': $('#mean_threshold').val(),
            'record_length': $('#record_length').val(),
            'degree_days': $('#degree_days').val(),
        }
        $.ajax({
            url: $(this).attr('action'),  // Get the action attribute from the form
            type: 'POST',
            headers: {"X-CSRFToken": csrfToken},
            data: postData,
            success: function(data) {
                // Redirect to the current page
                location.reload();
            },
            error: function(jqXHR, textStatus, errorThrown) {
                // Handle any errors
                console.log(errorThrown);
                location.reload()
            }
        });
    });
});