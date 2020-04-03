function svgChartDownload(chartConfig, title) {
    // Create c2s chart, download it
    let browserZoomLevel = Math.round(window.devicePixelRatio * 100);
    let canvasScale = 100 / browserZoomLevel;
    let c2s = C2S(1000 , 600 );
    c2s.scale(canvasScale, canvasScale);

    chartConfig.options['animation'] = false;
    chartConfig.options['responsive'] = false;
    if (!chartConfig.options.hasOwnProperty('legend')) {
        chartConfig.options['legend'] = {display: true};
    }
    chartConfig.options['title'] = {
        display: true,
        text: title,
        fontSize: 20
    };
    new Chart(c2s, chartConfig);
    // Download the chart
    let svg = c2s.getSerializedSvg(true);
    // Convert svg source to URI data scheme.
    let link = document.createElement('a');
    link.href = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
    link.download = `${title}.svg`;
    link.dispatchEvent(new MouseEvent('click'));
}
