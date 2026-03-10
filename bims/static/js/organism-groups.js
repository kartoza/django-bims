/* organism-groups.js
 * Renders "Available organism groups" cards on the landing page.
 * Requires jQuery. Call renderOrganismGroups() or fetchAndRenderOrganismGroups()
 * after defining window.organismGroupsConfig with theme values.
 */
(function () {
    'use strict';

    function getNumberWithCommas(n) {
        try {
            return n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        } catch (e) {
            return '';
        }
    }

    function buildCard(key, summaryData, config) {
        var totalValidated = summaryData['total_validated'] || 0;
        if (!summaryData['icon'] || totalValidated <= 0) return null;

        config = config || {};

        var $card = $('<div class="organism-group-card text-center"></div>');

        var $logoWrapper = $('<div class="organism-group-logo-wrapper"></div>');
        $logoWrapper.append(
            $('<img />').attr('src', summaryData['icon']).attr('alt', key)
        );
        $card.append($logoWrapper);

        var $name = $('<div class="organism-group-name"></div>').text(key);
        if (config.nameFontSize)   $name.css('font-size',       config.nameFontSize);
        if (config.nameColor)      $name.css('color',           config.nameColor);
        if (config.fontFamily)     $name.css('font-family',     config.fontFamily);
        if (config.textTransform)  $name.css('text-transform',  config.textTransform);
        $card.append($name);

        var $count = $('<div class="organism-group-count"></div>');
        if (config.countFontSize)  $count.css('font-size',  config.countFontSize);
        if (config.countColor)     $count.css('color',      config.countColor);
        if (config.fontFamily)     $count.css('font-family', config.fontFamily);
        $count.html(
            '<span class="organism-group-number">' +
            getNumberWithCommas(totalValidated) +
            '</span> species'
        );
        $card.append($count);

        return $card;
    }

    /**
     * Render organism group cards from already-fetched module summary data.
     * @param {Object} data     - Response from /api/module-summary
     * @param {string} listId   - CSS selector for the list container
     * @param {Object} config   - Theme config (nameFontSize, countFontSize, nameColor, countColor, fontFamily, textTransform)
     */
    function renderOrganismGroups(data, listId, config) {
        var $list = $(listId);
        $list.find('.organism-groups-loading').hide();
        var hasGroups = false;

        $.each(data, function (key, summaryData) {
            var $card = buildCard(key, summaryData, config);
            if ($card) {
                hasGroups = true;
                $list.append($card);
            }
        });

        if (hasGroups) {
            $list.closest('.organism-groups-section').show();
        }
    }

    /**
     * Fetch /api/module-summary, poll while processing, then render organism groups.
     * @param {string} listId  - CSS selector for the list container
     * @param {Object} config  - Theme config
     */
    function fetchAndRenderOrganismGroups(listId, config) {
        var pollAttempts = 0;
        var maxPollAttempts = 60;

        function doFetch() {
            $.get('/api/module-summary').then(function (data) {
                if (data.status === 'processing') {
                    pollAttempts++;
                    if (pollAttempts < maxPollAttempts) {
                        setTimeout(doFetch, 1000);
                    } else {
                        $(listId).find('.organism-groups-loading').hide();
                    }
                    return;
                }
                renderOrganismGroups(data, listId, config);
            }).fail(function () {
                $(listId).find('.organism-groups-loading').hide();
            });
        }

        doFetch();
    }

    window.renderOrganismGroups       = renderOrganismGroups;
    window.fetchAndRenderOrganismGroups = fetchAndRenderOrganismGroups;
})();
