function renderSourceReferences() {
    let divWrapper = $('#data-source-list');
    let dataSources = sourceReferences;
    let order = ['Reference Category', 'Author/s', 'Year', 'Title', 'Source', 'DOI/URL', 'Notes'];
    let orderedDataSources = [];
    for (var j=0; j<dataSources.length; j++) {
        orderedDataSources.push({})
        for (var i = 0; i < order.length; i++) {
            orderedDataSources[j][order[i]] = dataSources[j][order[i]];
        }
    }

    var headerDiv = $('<thead><tr></tr></thead>');
    if(orderedDataSources.length > 0) {
        var keys = Object.keys(orderedDataSources[0]);
        for (var i = 0; i < keys.length; i++) {
            headerDiv.append('<th>' + keys[i] + '</th>')
        }
    }
    divWrapper.append(headerDiv);

    var bodyDiv = $('<tbody></tbody>');
    $.each(orderedDataSources, function (index, source) {
        var itemDiv = $('<tr></tr>');
        var keys = Object.keys(source);
        var document = false;
        for(var i=0; i<keys.length; i++){
            if(source[keys[i]] === 'Published report or thesis'){
                document = true
            }

            if(keys[i] === 'DOI/URL' && document){
                itemDiv.append('<td><a href="'+ source[keys[i]] + '" target="_blank">Download</a></td>')
            }else {
                itemDiv.append('<td>' + source[keys[i]] + '</td>')
            }
        }
        bodyDiv.append(itemDiv);
    });
    divWrapper.append(bodyDiv);
}