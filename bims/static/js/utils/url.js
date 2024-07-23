define(['backbone', 'utils/class'], function (Backbone, UtilClass) {
    return UtilClass.extend({
        initialize: function () {
        },
        updateUrlParams: function (url, anchor, param, paramVal) {
            let parts = url.split('#');
            let baseUrl = parts[0];
            let hash = parts[1] || '';

            let newAnchor = anchor;
            let paramString = param + '=' + paramVal;

            if (hash) {
                let anchorParts = hash.split('/');
                if (anchorParts[0] === anchor) {
                    // CASE 3: #anchor/param=notParamVal -> anchor/param=paramVal
                    let paramsPart = anchorParts[1] || '';
                    let paramsArray = paramsPart.split('&');
                    let paramFound = false;

                    for (let i = 0; i < paramsArray.length; i++) {
                        if (paramsArray[i].startsWith(param + '=')) {
                            paramsArray[i] = paramString;
                            paramFound = true;
                            break;
                        }
                    }

                    if (!paramFound) {
                        paramsArray.push(paramString);
                    }

                    newAnchor += '/' + paramsArray.join('&');
                } else {
                    // CASE 4: #notAnchor/notParam=1&param=notParamVal -> notAnchor/notParam=1&param=paramVal
                    let paramsArray = hash.split('&');
                    let paramFound = false;

                    for (let i = 0; i < paramsArray.length; i++) {
                        if (paramsArray[i].startsWith(param + '=')) {
                            paramsArray[i] = paramString;
                            paramFound = true;
                            break;
                        }
                    }

                    if (!paramFound) {
                        paramsArray.push(paramString);
                    }

                    newAnchor = paramsArray.join('&');
                }
            } else {
                // CASE 1 & 2
                newAnchor = anchor + '/' + paramString;
            }

            return newAnchor;
        }
    });
});
