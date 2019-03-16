let filterParametersJSON = {
    'taxon': {
        'label': 'Taxon',
        'type': 'comma'
    },
    'search': {
        'label': 'Search Query',
        'type': 'string'
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
        'type': 'json'
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

function renderFilterList($table) {
    let urlParams = getUrlVars();
    let tableData = {};
    $table.html('<tr><th>Name</th><th>Value</th></tr>');

    $.each(filterParametersJSON, function (key, data) {
        if (urlParams[key]) {
            if (data['type'] === 'comma') {
                tableData[data['label']] = urlParams[key].split(',');
            } else if (data['type'] === 'string') {
                tableData[data['label']] = urlParams[key];
            } else if (data['type'] === 'json') {
                tableData[data['label']] = JSON.parse(decodeURIComponent(urlParams[key]));
            }
        }
    });

    $.each(tableData, function (key, data) {
        let $tr = $('<tr>');
        $tr.append('<td>' + key + '</td>');
        $tr.append('<td>' + data + '</td>');
        $table.append($tr);
    });
}
