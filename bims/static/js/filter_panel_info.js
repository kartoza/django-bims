(function (window) {
    'use strict';

    var hasStarted = false;

    function bootstrapFilterInfo() {
        if (hasStarted) {
            return;
        }

        if (!window || !window.jQuery) {
            window.setTimeout(bootstrapFilterInfo, 75);
            return;
        }

        hasStarted = true;
        createFilterInfo(window, window.jQuery);
    }

    function createFilterInfo(window, $) {
        var subtitleSelector = '.map-control-panel-box .subtitle';
        var iconLabel = 'Show more information about this filter';
        var iconClass = 'filter-info-icon';
        var observer = null;
        var filterDescriptions = {};
        var descriptionsRequest = null;
        var apiUrl = window.filterPanelInfoAPIUrl || '/api/filter-panel-info/';

        function normalizeTitle(title) {
            return $.trim((title || '')).replace(/\s+/g, ' ').toUpperCase();
        }

        function addDescription(name, description) {
            if (!name || typeof description === 'undefined' || description === null) {
                return;
            }
            var value = (description || '').toString().trim();
            if (!value) {
                return;
            }
            filterDescriptions[normalizeTitle(name)] = value;
        }

        function getDescription(name) {
            var key = normalizeTitle(name);
            if (filterDescriptions.hasOwnProperty(key)) {
                return filterDescriptions[key];
            }
            return '';
        }

        function loadDescriptions() {
            if (descriptionsRequest) {
                return descriptionsRequest;
            }

            descriptionsRequest = $.ajax({
                url: apiUrl,
                method: 'GET',
                dataType: 'json'
            }).then(function (response) {
                filterDescriptions = {};
                if (Array.isArray(response)) {
                    response.forEach(function (item) {
                        if (item && item.title) {
                            addDescription(item.title, item.description);
                        }
                    });
                }
                return filterDescriptions;
            }, function (xhr) {
                // eslint-disable-next-line no-console
                console.warn('Unable to load filter panel info descriptions', xhr);
                return filterDescriptions;
            });

            return descriptionsRequest;
        }

        function extractTitle($subtitle) {
            var $clone = $subtitle.clone();
            $clone.find('.' + iconClass).remove();
            $clone.find('.filter-icon-arrow').remove();
            return $clone.text();
        }

        function findSubtitleElements(context) {
            var $targets = $();
            if (!context) {
                return $(subtitleSelector);
            }

            var nodes = [];
            if (context.jquery) {
                nodes = context.toArray();
            } else if (Array.isArray(context)) {
                nodes = context;
            } else if (context.length && !context.nodeType) {
                nodes = Array.prototype.slice.call(context);
            } else {
                nodes = [context];
            }

            nodes.forEach(function (node) {
                if (!node || node.nodeType !== 1) {
                    return;
                }
                var $node = $(node);
                if ($node.is(subtitleSelector)) {
                    $targets = $targets.add($node);
                }
                $targets = $targets.add($node.find(subtitleSelector));
            });

            return $targets;
        }

        function getPopoverContainer() {
            return $('#map-container').length ? '#map-container' : 'body';
        }

        function attachIcons($elements) {
            if (!$elements || !$elements.length) {
                return;
            }

            $elements.each(function () {
                var $subtitle = $(this);
                if ($subtitle.find('.' + iconClass).length) {
                    return;
                }

                var titleText = extractTitle($subtitle);
                var description = getDescription(titleText);
                if (!description) {
                    return;
                }

                var $icon = $('<span/>', {
                    'class': iconClass,
                    'tabindex': 0,
                    'role': 'button',
                    'aria-label': iconLabel
                }).append(
                    $('<i/>', {
                        'class': 'fa fa-info-circle',
                        'aria-hidden': 'true'
                    })
                );

                var $toggleIcon = $subtitle.find('.filter-icon-arrow').first();
                if ($toggleIcon.length) {
                    $icon.insertBefore($toggleIcon);
                } else {
                    $subtitle.append($icon);
                }

                $icon.popover({
                    trigger: 'hover focus',
                    placement: 'top',
                    container: getPopoverContainer(),
                    content: description
                });
            });
        }

        function init(context) {
            return loadDescriptions().then(function () {
                attachIcons(findSubtitleElements(context));
            });
        }

        function startObserver() {
            if (!window.MutationObserver) {
                return;
            }
            var target = document.querySelector('.right-panel') || document.querySelector('#map-container');
            if (!target) {
                return;
            }

            observer = new window.MutationObserver(function (mutations) {
                var added = [];
                mutations.forEach(function (mutation) {
                    Array.prototype.forEach.call(mutation.addedNodes, function (node) {
                        if (node && node.nodeType === 1) {
                            added.push(node);
                        }
                    });
                });
                if (added.length) {
                    init(added);
                }
            });

            observer.observe(target, {
                childList: true,
                subtree: true
            });
        }

        $(document).ready(function () {
            init().always(function () {
                startObserver();
            });
        });

        window.FilterPanelInfo = {
            init: init,
            addDescription: addDescription,
            getDescriptions: function () {
                return $.extend({}, filterDescriptions);
            }
        };
    }

    bootstrapFilterInfo();
})(window);
