/* metagroup-widget.js
 * Renders metagroup (broader organism group) cards on the landing page.
 * Requires jQuery.
 * Call fetchAndRenderMetaGroups(containerId, config) on document ready.
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

    /**
     * Build a single metagroup card element.
     * @param {Object} mg     - Metagroup data from /api/metagroup-summary/
     * @param {Object} config - Theme config (nameFontSize, countFontSize, nameColor, countColor, fontFamily, textTransform)
     * @returns {jQuery|null}
     */
    function buildMetaGroupCard(mg, config) {
        if (!mg.name) return null;

        config = config || {};

        var $card = $('<div class="metagroup-card text-center"></div>');

        if (mg.icon) {
            var $logoWrapper = $('<div class="metagroup-logo-wrapper"></div>');
            $logoWrapper.append(
                $('<img />').attr('src', mg.icon).attr('alt', mg.name)
            );
            $card.append($logoWrapper);
        }

        var $name = $('<div class="metagroup-name"></div>').text(mg.name);
        if (config.nameFontSize)  $name.css('font-size',      config.nameFontSize);
        if (config.nameColor)     $name.css('color',          config.nameColor);
        if (config.fontFamily)    $name.css('font-family',    config.fontFamily);
        if (config.textTransform) $name.css('text-transform', config.textTransform);
        $card.append($name);

        var $stats = $('<div class="metagroup-stats"></div>');
        if (config.countFontSize) $stats.css('font-size',  config.countFontSize);
        if (config.countColor)    $stats.css('color',      config.countColor);
        if (config.fontFamily)    $stats.css('font-family', config.fontFamily);

        $stats.append(
            $('<div class="metagroup-stat"></div>').html(
                '<span class="metagroup-number">' + getNumberWithCommas(mg.total_taxa || 0) + '</span> species'
            )
        );
        $stats.append(
            $('<div class="metagroup-stat"></div>').html(
                '<span class="metagroup-number">' + getNumberWithCommas(mg.total_records || 0) + '</span> records'
            )
        );
        $card.append($stats);

        return $card;
    }

    /**
     * Render metagroup cards from already-fetched data.
     * @param {Array}  data      - Response from /api/metagroup-summary/
     * @param {string} containerId - CSS selector for the container element
     * @param {Object} config    - Theme config
     */
    function renderMetaGroups(data, containerId, config) {
        var $container = $(containerId);
        $container.find('.metagroup-loading').hide();

        var hasCards = false;
        $.each(data, function (i, mg) {
            var $card = buildMetaGroupCard(mg, config);
            if ($card) {
                hasCards = true;
                $container.append($card);
            }
        });

        if (hasCards) {
            $container.closest('.metagroup-section').show();
        }
    }

    /**
     * Fetch /api/metagroup-summary/ then render metagroup cards.
     * @param {string} containerId - CSS selector for the container element
     * @param {Object} config      - Theme config
     */
    function fetchAndRenderMetaGroups(containerId, config) {
        $.get('/api/metagroup-summary/').then(function (data) {
            renderMetaGroups(data, containerId, config);
        }).fail(function () {
            $(containerId).find('.metagroup-loading').hide();
        });
    }

    window.renderMetaGroups         = renderMetaGroups;
    window.fetchAndRenderMetaGroups = fetchAndRenderMetaGroups;
})();
