$(function () {
    console.log('test');
});

function dashboardClose(e) {
    let button = $(e.target);
    if (!button.hasClass('dashboard-close')) {
        button = button.parent();
    }
    let closeDestination = button.data('destination');
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
    if (params && url.searchParams.has('taxon')) {
        previousUrl += '/#site-detail/';
        previousUrl += params;
        let regex = new RegExp("&page=\\d+|page=\\d+")
        previousUrl = previousUrl.replace(regex,'');
        window.location.href = previousUrl;
        return true;
    }
    if (previousUrl === '') {
        try {
            window.location.href = 'map/#site/siteIdOpen=' + siteId;
        } catch (e) {
            window.location.href = '/map/';
        }
    } else if (previousUrl.indexOf('source-reference-form') > -1) {
        window.history.href = '/map/';
    } else {
        window.history.back();
    }
}

$(function () {
   $('.dashboard-close').click(dashboardClose);
});
