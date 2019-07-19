function dashboardClose(e) {
    let previousUrl = '/map/';
    let url = new URL(window.location.href);
    let params = url.searchParams.toString();
    let search = url.searchParams.get('search');
    if (params && url.searchParams.has('taxon')) {
        previousUrl += '#search/';
        if (search) {
            previousUrl += search;
        }
        previousUrl += '/';
        previousUrl += params;
    }
    window.location.href = previousUrl;
    return false;
}

$(function () {
   $('.dashboard-close').click(dashboardClose);
});
