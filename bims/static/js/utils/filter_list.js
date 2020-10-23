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
    }
};

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

function renderFilterList($div, asTable = true) {
    let urlParams = getUrlVars();
    let tableData = {};
    if (asTable) {
        $div.html('<div class="row" style="font-weight: bold;"><div class="col-4">Category</div><div class="col-8">Selection</div></div>');
    }

    $.each(filterParametersJSON, function (key, data) {
        if (urlParams[key]) {
            if (data['type'] === 'comma') {
                tableData[data['label']] = urlParams[key].split(',');
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
                let json_data = JSON.parse(decodeURIComponent(urlParams[key]));
                try {
                    if (typeof json_data !== 'undefined' && json_data.length > 0) {
                        tableData[data['label']] = '';
                        $.each(json_data, function (index, json_label) {
                            if (typeof json_label === 'undefined') {
                                return true;
                            }
                            let label = json_label;
                            if (data.hasOwnProperty('font')) {
                                if (data['font'] === 'uppercase') {
                                    label = label.toUpperCase();
                                }
                            }
                            if (data.hasOwnProperty('rename')) {
                                if (data['rename'].hasOwnProperty(label)) {
                                    label = data['rename'][label];
                                }
                            }
                            tableData[data['label']] += label.charAt(0).toUpperCase() + label.slice(1);
                            if (index < json_data.length-1) {
                                tableData[data['label']] += ', ';
                            }
                        });
                    }
                } catch (e) {
                }
            }
        }
    });

    $.each(tableData, function (key, data) {
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
