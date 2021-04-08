function insertParam(key, value, resetPage = true) {
    key = encodeURIComponent(key);
    value = encodeURIComponent(value);
    // kvp looks like ['key1=value1', 'key2=value2', ...]
    var kvp = document.location.search.substr(1).split('&');
    let i = 0;
    let j = 0;
    for (; i < kvp.length; i++) {
        if (kvp[i].startsWith(key + '=')) {
            let pair = kvp[i].split('=');
            pair[1] = value;
            kvp[i] = pair.join('=');
            break;
        }
    }

    if (resetPage)  {
        for (; j < kvp.length; j++) {
            console.log(kvp)
            if (kvp[j].startsWith('page=')) {
                let pair = kvp[j].split('=');
                pair[1] = '';
                kvp[j] = pair.join('=');
                break;
            }
        }
    }
    if (i >= kvp.length) {
        kvp[kvp.length] = [key, value].join('=');
    }
    // can return this or...
    let params = kvp.join('&');
    // reload page with new params
    document.location.search = params;
}
