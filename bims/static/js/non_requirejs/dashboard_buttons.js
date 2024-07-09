function dashboardClose(e, storageKey = '') {
    let button = $(e.target);
    if (!button.hasClass('dashboard-close')) {
        button = button.parent();
    }
    if (storageKey) {
        let lastMap = localStorage.getItem(storageKey);
        localStorage.removeItem(storageKey);
        if (lastMap) {
            window.location.href = lastMap;
            return
        }
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
    if (params && url.searchParams.has('taxon') && !params.includes('taxa-management')) {
        previousUrl += '/#site-detail/';
        previousUrl += params;
        let regex = new RegExp("&page=\\d+|page=\\d+")
        previousUrl = previousUrl.replace(regex,'');
        window.location.href = previousUrl;
        return true;
    }
    if (previousUrl === '') {
        if (params.includes('next=')) {
            window.location.href = url.searchParams.get('next');
            return
        }
        try {
            window.location.href = '/map/#site/siteIdOpen=' + siteId;
        } catch (e) {
            window.location.href = '/map/';
        }
    } else if (previousUrl.indexOf('/abiotic/?') > -1) {
        window.history.go(-6);
    } else {
        window.history.back();
    }
}

$(function () {
    $('.dashboard-close').click((e) => dashboardClose(e, ''));
    $('.site-form-close').click((e) => dashboardClose(e, ''));
    $('.sass-form-edit-close').click((e) => dashboardClose(e, 'site-visit-list'));
    $('.upload-form-close').click((e) => dashboardClose(e, 'last-map-upload'));
});
