define(['backbone', 'utils/class'], function (Backbone, UtilClass) {
    let TaxonImagesUtil = UtilClass.extend({
        initialize: function () {
        },
        renderAttribution: function (media) {
            let div = '<p>';
            if (media['rightsHolder']) {
                div += `©&nbsp;${media['rightsHolder']}`;
            }
            if (media['license']) {
                if (!div.endsWith('<p>')) div += ', ';
                if (media['license'].startsWith('http')) {
                    if (!media['license'].toLowerCase().includes('all right')) {
                        div += `<a href="${media['license']}">some rights reserved</a>`;
                    } else {
                        div += 'all rights reserved';
                    }
                } else {
                    div += media['license'];
                }
            }
            if (media['creator']) {
                if (!div.endsWith('<p>')) div += ', ';
                div += `uploaded by ${media['creator']}`;
            }
            div += '</p>'
            return div;
        },
        renderTaxonImages: function (gbifId, taxonId) {
            let self = this;
            let $thirdPartyData = $('<div>');
            let template = _.template($('#third-party-template').html());
            $thirdPartyData.append(template({}));
            let $wrapper = $thirdPartyData.find('.third-party-wrapper');
            let mediaFound = false;
            let $fetchingInfoDiv = $thirdPartyData.find('.third-party-fetching-info');
            let $rowWrapper = $('<div id="gbif-images-row" class="gbif-images-row gbif-images-row-fsdd"></div>');
            $.get({
                url: '/api/taxon-images/' + taxonId,
                dataType: 'json',
                success: function (data) {
                    if (data.length > 0) {
                        mediaFound = true;
                        data.forEach(function (image) {
                            $rowWrapper.append('<div class="taxon-image"><a target="_blank" href="' + image['url'] + '">' +
                                '<img title="' + image['source'] + '" src="' + image['url'] + '"/></a>' +
                                (image['source'] ? `<p> ${image['source']} </p>` : '') +
                                '</div>');
                            $fetchingInfoDiv.hide();
                        });
                        $wrapper.append($rowWrapper);
                    }
                    if (gbifId) {
                        $.get({
                            url: 'https://api.gbif.org/v1/occurrence/search?taxonKey=' + gbifId + '&limit=4',
                            dataType: 'json',
                            success: function (data) {
                                var results = data['results'];
                                var result = {};
                                for (let result_id in results) {
                                    result = results[result_id];
                                    if (!result.hasOwnProperty('media')) {
                                        continue;
                                    }
                                    if (result['media'].length === 0) {
                                        continue;
                                    }
                                    var media = result['media'][0];
                                    if (!media.hasOwnProperty('identifier')) {
                                        continue;
                                    }
                                    mediaFound = true;
                                    if (mediaFound) {
                                        $fetchingInfoDiv.hide();
                                    }
                                    $rowWrapper.append('<div class="taxon-image"><a target="_blank" href="' + media['references'] + '">' +
                                        '<img title="Source: ' + media['publisher'] + '" alt="' + media['rightsHolder'] + '" src="' + media['identifier'] + '"/></a>' +
                                        self.renderAttribution(media) +
                                        '</div>');
                                }
                                $wrapper.append($rowWrapper);
                                if (!mediaFound) {
                                    $fetchingInfoDiv.html('Media not found');
                                }
                            }
                        });
                    } else {
                        if (!mediaFound) {
                            $fetchingInfoDiv.html('Media not found');
                        }
                    }
                }
            });
            return $thirdPartyData;
        }
    });
    return TaxonImagesUtil;
});