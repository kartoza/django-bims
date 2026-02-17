let filterParametersJSON = {
    'taxon': {
        'label': 'Taxon',
        'type': 'comma'
    },
    'search': {
        'label': 'Search Query',
        'type': 'unicode'
    },
    'yearFrom': {
        'label': 'Year From',
        'type': 'string'
    },
    'yearTo': {
        'label': 'Year To',
        'type': 'string'
    },
    'months': {
        'label': 'Month',
        'type': 'comma'
    },
    'siteId': {
        'label': 'Site Id',
        'type': 'comma'
    },
    'ecosystemType': {
        'label': 'Ecosystem Type',
        'type': 'comma'
    },
    'collector': {
        'label': 'Collector',
        'type': 'json'
    },
    'category': {
        'label': 'Category',
        'type': 'json',
        'rename': {
            'alien': 'Non-Native',
            'indigenous': 'Native'
        }
    },
    'sourceCollection': {
        'label': 'Data Source',
        'type': 'json',
        'font': 'uppercase'
    },
    'reference': {
        'label': 'Reference',
        'type': 'json'
    },
    'referenceCategory': {
        'label': 'Reference Category',
        'type': 'json'
    },
    'endemic': {
        'label': 'Endemic',
        'type': 'json'
    },
    'conservationStatus': {
        'label': 'Conservation Status',
        'type': 'json'
    },
    'userBoundary': {
        'label': 'User Boundary',
        'type': 'json'
    },
    'boundary': {
        'label': 'Boundary',
        'type': 'json'
    },
    'validated': {
        'label': 'Validation Status',
        'type': 'json'
    },
    'spatialFilter': {
        'label': 'Spatial filter',
        'type': 'spatial_filter'
    },
    'tags': {
        'label': 'Taxon tags',
        'type': 'json'
    }
};

let spatialFilterData = null;
let spatialFilterPromise = null;

function getUrlVars() {
    let vars = [], hash;
    let hashes = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');
    for (let i = 0; i < hashes.length; i++) {
        hash = hashes[i].split('=');
        vars.push(hash[0]);
        vars[hash[0]] = hash[1];
    }
    return vars;
}

function getSpatialFilterData () {
    if (spatialFilterData) {
        return $.Deferred().resolve(spatialFilterData).promise();
    }
    if (!spatialFilterPromise) {
        spatialFilterPromise = $.ajax({
            type: 'GET',
            url: '/api/spatial-scale-filter-list/',
            dataType: 'json',
            success: function (data) {
                spatialFilterData = data;
            },
            error: function () {
                spatialFilterPromise = null;
            }
        });
    }
    return spatialFilterPromise;
}

async function renderFilterList($div, asTable = true) {
    let urlParams = getUrlVars();
    let tableData = {};
    if (asTable) {
        $div.html('<div class="row" style="font-weight: bold;">' +
            '<div class="col-4">Category</div><div class="col-8">Selection</div></div>');
    }

    await getSpatialFilterData();

    $.each(filterParametersJSON, function (key, data) {
        if (urlParams[key]) {
            if (data['type'] === 'comma') {
                tableData[data['label']] = decodeURIComponent(urlParams[key]).split(',');
            } else if (data['type'] === 'string') {
                tableData[data['label']] = urlParams[key];
            } else if (data['type'] === 'spatial_filter') {
                let spatialFilterContainer = $('.spatial-filter-container');
                let json_data = JSON.parse(decodeURIComponent(urlParams[key]));
                let table_data = '';

                $.each(json_data, function (index, spatial_filter) {
                    let spatial_filter_values = spatial_filter.split(',');
                    let spatial_filter_name = spatial_filter_values[1];
                    spatial_filter_name = spatialFilterContainer.find(`input[name ="${spatial_filter_name}"]`).next().html();

                    if (typeof spatial_filter_name === 'undefined') {
                        let spatialFilterKey = spatial_filter_values[1];
                        for (let _sfData of spatialFilterData) {
                            if (!_sfData.children) continue;
                            let found = _sfData.children.find(child => child.key === spatialFilterKey);
                            spatial_filter_name = found ? found.name : spatialFilterKey;
                        }
                    }

                    let spatial_filter_value = 'All';
                    if (spatial_filter_values[0] === 'value') {
                        spatial_filter_value = spatial_filter_values[2];
                    }
                    table_data += spatial_filter_name + ' : ' + spatial_filter_value;
                    table_data += '<br/>';
                });
                tableData[data['label']] = table_data;
            } else if (data['type'] === 'unicode') {
                tableData[data['label']] = decodeURIComponent(urlParams[key]);
            } else if (data['type'] === 'json') {
                let json_data = '';
                try {
                    json_data = JSON.parse(decodeURIComponent(urlParams[key]));
                } catch (e) {
                    json_data = JSON.parse(decodeURIComponent(decodeURIComponent(urlParams[key])));
                }

                try {
                    if (typeof json_data !== 'undefined' && json_data.length > 0) {
                        // special case: taxon tags -> resolve IDs to names
                        if (key === 'tags') {
                            // json_data here is array of IDs like [17,4,9] (numbers or strings)
                            // we'll call /api/taxon-tag-autocomplete/?ids=17,4,9
                            let tagNames = [];
                            $.ajax({
                                url: '/api/taxon-tag-autocomplete/',
                                dataType: 'json',
                                async: false, // block until we have names
                                data: {
                                    ids: json_data.join(',')
                                },
                                success: function (resp) {
                                    // resp is [{id:17,name:"Terrestrial"}, ...]
                                    $.each(resp, function (idx, tagObj) {
                                        if (!tagObj || !tagObj.name) {
                                            return true;
                                        }
                                        tagNames.push(tagObj.name);
                                    });
                                },
                                error: function () {
                                    // fallback: if request fails, just show raw IDs
                                    $.each(json_data, function (idx, rawId) {
                                        tagNames.push(rawId);
                                    });
                                }
                            });

                            // Build pretty string, capitalized first letter of each name
                            if (tagNames.length > 0) {
                                tableData[data['label']] = '';
                                $.each(tagNames, function (idx, nm) {
                                    if (!nm) {
                                        return true;
                                    }
                                    let label = nm;
                                    // keep same visual treatment as others: uppercase first char
                                    label = label.charAt(0).toUpperCase() + label.slice(1);
                                    tableData[data['label']] += label;
                                    if (idx < tagNames.length - 1) {
                                        tableData[data['label']] += ', ';
                                    }
                                });
                            }
                        } else {
                            // default behavior for normal json arrays (collector, sourceCollection, etc.)
                            tableData[data['label']] = '';
                            $.each(json_data, function (index, json_label) {
                                if (typeof json_label === 'undefined') {
                                    return true;
                                }
                                let label = json_label;

                                // Custom font transform (e.g. uppercase for Data Source)
                                if (data.hasOwnProperty('font')) {
                                    if (data['font'] === 'uppercase' && typeof label === 'string') {
                                        label = label.toUpperCase();
                                    }
                                }

                                // Rename map (e.g. alien → Non-Native)
                                if (data.hasOwnProperty('rename') && typeof label === 'string') {
                                    if (data['rename'].hasOwnProperty(label)) {
                                        label = data['rename'][label];
                                    }
                                }

                                // Capitalize first letter for display, if it's still a string
                                if (typeof label === 'string' && label.length > 0) {
                                    label = label.charAt(0).toUpperCase() + label.slice(1);
                                }

                                tableData[data['label']] += label;

                                if (index < json_data.length - 1) {
                                    tableData[data['label']] += ', ';
                                }
                            });
                        }
                    }
                } catch (e) {
                    // swallow
                }
            }
        }
    });

    $.each(tableData, function (key, data) {
        if (key.toLowerCase().includes('conservation status')) {
            const consCategories = data.split(',');
            const consCategory = {
                national: [],
                global: []
            }
            for (const category of consCategories) {
                if (category.startsWith('N__')) {
                    consCategory.national.push(category.replace('N__', ''))
                } else {
                    consCategory.global.push(category)
                }
            }
            data = '';
            if (consCategory.national.length > 0) {
                data += `National: ${consCategory.national.join()}`
            }
            if (consCategory.global.length > 0) {
                if (data) {
                    data += '; '
                }
                data += `Global: ${consCategory.global.join()}`
            }
        }

        if (asTable) {
            let $tr = $('<div class="row">');
            $tr.append('<div class="col-4">' + key + '</div>');
            $tr.append('<div class="col-8">' + data + '</div>');
            $div.append($tr);
        } else {
            $div.append(`<div class="filter-title">${key}</div>`);
            $div.append(`<div class="filter-value">${data}</div>`);
        }
    });
}

function numberWithCommas(x) {
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}