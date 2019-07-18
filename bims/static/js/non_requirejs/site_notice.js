function showSiteNotice() {
    if(isSiteNoticeAvailable) {
        let siteNoticeRead = getCookie('siteNoticeRead');
        if (!siteNoticeRead) {
            let siteNoticeModal = $('#siteNoticeModal');
            siteNoticeModal.modal({
                'keyboard': false,
                'backdrop': 'static'
            });
            siteNoticeModal.on('hidden.bs.modal', function () {
                setCookie('siteNoticeRead', true);
            });
        }
    }
}