define(['backbone', 'utils/class'], function (Backbone, UtilClass) {
    return UtilClass.extend({
        initialize: function () {
        },
        // CASE
        // 1.  -> anchor/param=paramVal
        // 2. # -> anchor/param=paramVal
        // 3. #anchor/param=notParamVal -> anchor/param=paramVal
        // 4. #notAnchor/notParam=1&param=notParamVal -> notAnchor/notParam=1&param=paramVal
        updateUrlParams: function (url, anchor, param, paramVal) {
            url = url.split('#');
            if (url.length > 1) {
                if (url[1] === '') {
                    url = '';
                } else {
                    url = '#' + url[1];
                }
            } else {
                url = '';
            }

            if (url === '') { // CASE 1 & 2
                return anchor + '/' + param + '=' + paramVal;
            }

            if (url.indexOf(param) > -1 && url.indexOf('&') > -1) {
                let regex = new RegExp("(" + param + "=).*(&)");
                let newUrl = url.replace(regex, '$1' + paramVal + '$2');
                if (newUrl.indexOf('#') > -1) { // http://test.com/#anchor/param=paramVal
                    newUrl = newUrl.split('#')[1]; // anchor/param=paramVal
                }
                return newUrl
            }

            return anchor + '/' + param + '=' + paramVal;
        }
    });
});
