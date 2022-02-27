function dashboardClose(e) {
    let closeDestination = $(e.target).data('destination');
    let previousUrl = window.document.referrer;
    if (closeDestination) {
        if (previousUrl.indexOf('map') > -1) {
            window.history.back();
            return;
        }
        previousUrl = closeDestination;
    }
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
    if (!previousUrl) previousUrl = '/map';
    window.location.href = previousUrl;
    return false;
}

$(function () {
   $('.dashboard-close').click(dashboardClose);
});
