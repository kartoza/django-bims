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
    let url = new URLSearchParams(window.location.search);
    let params = url.toString();
    let search = url.get('search');
    let siteId = url.get('siteId');
    if (params && url.has('taxon')) {
        previousUrl += '#search/';
        if (search) {
            previousUrl += search;
        }
        previousUrl += '/';
        previousUrl += params;
    }
    if (!previousUrl || previousUrl.indexOf('add-source-reference') > -1) {
        try {
            previousUrl = '/map/#site/siteIdOpen=' + siteId;
        } catch (e) {
            previousUrl = '/map/';
        }
    } else {
        if (siteId) {
            previousUrl = '/map/#site/siteIdOpen=' + siteId;
        }
    }
    if (window.document.referrer.indexOf('/map/') > -1 && window.document.referrer.indexOf(window.location.origin) > -1) {
        window.history.back();
    } else {
        window.location.href = previousUrl;
    }
}

$(function () {
   $('.dashboard-close').click(dashboardClose);
});
