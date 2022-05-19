let chartConfigs = {};

function renderChemGraph (chartContainer, chemicalRecords) {
    chartContainer.html('');
    listChemChartNames = [];

    $.each(chemicalRecords, function (key, value) {
        let id_canvas = key + '-chem-chart';
        let canvas = '<canvas class="chem-bar-chart" id="' + id_canvas + '"></canvas>';
        chartContainer.append(canvas);
        let ctx = document.getElementById(id_canvas).getContext('2d');
        let datasets = [];
        let yLabel;
        let xLabelData = [];
        $.each(value, function (idx, val) {
            let key_item = Object.keys(val)[0];
            if(key_item.toLowerCase().indexOf('max') === -1 && key_item.toLowerCase().indexOf('min') === -1){
                let unit = '';
                if (val[key_item]['name'].toLowerCase() !== 'ph') {
                    unit = ' (' + val[key_item]['unit'] + ')';
                }
                yLabel = val[key_item]['name'] + unit;
            }
            let value_data = val[key_item]['values'];
            let graph_data = [];
            for(let i=0; i<value_data.length; i++){
                graph_data.push({
                    y: value_data[i]['value'],
                    x: value_data[i]['str_date']
                });
                xLabelData.push(value_data[i]['str_date'])
            }
            datasets.push({
                label: key_item,
                data: graph_data,
                backgroundColor: '#cfdeea',
                borderColor: '#cfdeea',
                borderWidth: 2,
                fill: false
            })
        });

        xLabelData.sort(function(a, b) {
            a = new Date(a);
            b = new Date(b);
            return a < b ? -1 : a > b ? 1 : 0;
        });
        let _data = {
            labels: xLabelData,
            datasets: datasets
        };
        let options= {
            responsive: true,
            hoverMode: 'index',
            stacked: false,
            title: {
                display: false
            },
            legend: {
                display: false
            },
            scales: {
                yAxes: [{
                    scaleLabel: {
                        display: true,
                        labelString: yLabel
                    },
                    type: 'linear',
                    display: true,
                    position: 'left',
                    ticks: {
                        beginAtZero: true
                    }
                }]
            }
        };
        let chartConfig = {
            type: 'bar',
            data: _data,
            options: options
        };
        new Chart(ctx, chartConfig);
        chartConfigs[key] = chartConfig;
        listChemChartNames.push(key);
    });
    
    return listChemChartNames;
}

function getCsvName(title, identifier) {
    if (identifier) {
        title += ` for ${identifier}`;
    }
    return title;
}

function onDownloadChemCSVClicked(e) {
    let downloadButton = $(e.target);
    let csv_name = getCsvName('Chem data', downloadButton.data('identifier'));
    let currentUrl = window.location.href;
    let queryString = currentUrl ? currentUrl.split('?')[1] : window.location.search.slice(1);
    let url = '/api/chemical-record/download/?' + queryString;
    downloadButton.html("Processing...");
    downloadButton.prop("disabled", true);
    downloadCSV(url, downloadButton, csv_name);
}

function onDownloadChemChart(e) {
    let target = $(e.target);
    if (target.hasClass('processing')) {
        return;
    } else {
        target.addClass('processing');
    }
    let title = target.data('download-title');
    let charts = target.data('download-chart').split(',');
    if (charts[0] === 'chem-graph') {
        charts = listChemChartNames;
        title = '';
    } else {
        if (charts.length > 1) {
            title +=  ' - ';
        }
    }
    let maxRetry = 10;
    let retry = 0;
    while (!target.hasClass('chart-container') && retry < maxRetry)  {
        target = target.parent();
        retry += 1;
    }
    for (let i=0; i < charts.length; i++) {
        let chart = charts[i];
        let chartTitle = title;
        if (charts.length > 1) {
            chartTitle += chart.replace(/-/g, ' ').charAt(0).toUpperCase() + chart.replace(/-/g, ' ').slice(1);
        }
        svgChartDownload(chartConfigs[chart], chartTitle);
        $(e.target).removeClass('processing');
    }
}
