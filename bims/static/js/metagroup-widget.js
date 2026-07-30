/* metagroup-widget.js
 * Renders metagroup (meta organism group) cards on the landing page.
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
     * Build a single metagroup card using the same layout as module-container cards.
     * @param {Object} mg     - Metagroup data from /api/metagroup-summary/
     * @param {Object} config - Theme config (nameFontSize, countFontSize, nameColor, countColor, fontFamily, textTransform)
     * @returns {jQuery|null}
     */
    function buildMetaGroupCard(mg, config) {
        if (!mg.name) return null;

        config = config || {};

        var $card = $('<div class="col-lg-2 col-md-3 col-sm-12 module-container text-center"></div>');

        var $iconWrapper = $('<div class="chart-icon-wrapper"></div>');
        if (mg.icon) {
            $iconWrapper.append(
                $('<img />').addClass('meta-organism-icon').attr('src', mg.icon).attr('alt', mg.name)
            );
        }
        $card.append($iconWrapper);

        var nameStyle = '';
        if (config.nameFontSize)  nameStyle += 'font-size: ' + config.nameFontSize + ' !important;';
        if (config.nameColor)     nameStyle += 'color: ' + config.nameColor + ';';
        if (config.fontFamily)    nameStyle += 'font-family: ' + config.fontFamily + ';';
        if (config.textTransform) nameStyle += 'text-transform: ' + config.textTransform + ';';
        var $name = $('<h4 class="module-name"></h4>').text(mg.name).attr('style', nameStyle + 'font-weight: bold;');
        $card.append($name);

        var infoStyle = '';
        if (config.countFontSize)  infoStyle += 'font-size: ' + config.countFontSize + ';';
        if (config.countColor)     infoStyle += 'color: ' + config.countColor + ';';
        if (config.fontFamily)     infoStyle += 'font-family: ' + config.fontFamily + ';';
        if (config.textTransform)  infoStyle += 'text-transform: ' + config.textTransform + ';';

        var $infoContainer = $('<div class="module-info-container"></div>');

        $infoContainer.append(
            $('<p class="module-info" style="margin-bottom: 0;' + infoStyle + '"></p>').html(
                '<span class="module-numbers">' + getNumberWithCommas(mg.total_taxa || 0) + '</span> Species'
            )
        );
        $infoContainer.append(
            $('<p class="module-info" style="margin-top: 0; margin-bottom: 0;' + infoStyle + '"></p>').html(
                '<span class="module-numbers">' + getNumberWithCommas(mg.total_records || 0) + '</span> Records'
            )
        );
        if (mg.total_sites) {
            $infoContainer.append(
                $('<p class="module-info" style="margin-top: 0;' + infoStyle + '"></p>').html(
                    '<span class="module-numbers">' + getNumberWithCommas(mg.total_sites) + '</span> Sites'
                )
            );
        }
        $card.append($infoContainer);

        return $card;
    }

    /**
     * Render metagroup cards from already-fetched data.
     * @param {Array}  data        - Response from /api/metagroup-summary/
     * @param {string} containerId - CSS selector for the container element
     * @param {Object} config      - Theme config
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
