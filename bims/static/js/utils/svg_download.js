function svgChartDownload(chartConfig, title) {
    // Create c2s chart, download it
    let browserZoomLevel = Math.round(window.devicePixelRatio * 100);
    let canvasScale = 100 / browserZoomLevel;
    let c2s = C2S(1000 , 600 );
    c2s.scale(canvasScale, canvasScale);

    chartConfig.options['animation'] = false;
    chartConfig.options['responsive'] = false;
    chartConfig.options['legend'] = {
        display: true,
        labels: {
            filter: function(item, chart) {
                // Logic to remove a particular legend item goes here
                return !item.text.includes('hide_this_legend');
            }
        }
    };
    chartConfig.options['title'] = {
        display: true,
        text: title,
        fontSize: 20
    };
    let chart = new Chart(c2s, chartConfig);
    if (chartConfig['type'] === 'pie') {
        if (chart.data.labels.length === 1) {
            chart.data.labels.push('hide_this_legend');
            chart.data.datasets.forEach((dataset) => {
                dataset.data.push(0.001);
            });
            chart.update();
        }
    }
    // Download the chart
    let svg = c2s.getSerializedSvg(true);
    // Convert svg source to URI data scheme.
    let link = document.createElement('a');
    link.href = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
    link.download = `${title}.svg`;
    link.dispatchEvent(new MouseEvent('click'));
}
