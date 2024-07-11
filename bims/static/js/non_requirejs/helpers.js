const speciesAutoComplete = (inputDiv, additionalFilters = "") => {

    const parseAdditionalFilters = (filterString) => {
        const params = new URLSearchParams(filterString);
        let filterObject = {};
        for (const [key, value] of params.entries()) {
            filterObject[key] = value;
        }
        return filterObject;
    };
    return new Promise((resolve, reject) => {
        // Ensure inputDiv is a jQuery object
        const $inputDiv = $(inputDiv);

        if (typeof $inputDiv.select2 !== 'function') {
            console.error('Select2 is not loaded.');
            return reject(new Error('Select2 is not loaded.'));
        }

        const filters = parseAdditionalFilters(additionalFilters);

        $inputDiv.select2({
            ajax: {
                url: '/species-autocomplete/',
                dataType: 'json',
                delay: 250,
                data: (params) => ({
                    term: params.term,
                    ...filters
                }),
                processResults: (data) => ({
                    results: data.map(item => ({
                        id: item.id,
                        text: item.species
                    }))
                }),
                cache: true
            },
            minimumInputLength: 3,
            templateResult: (item) => item.text,
            templateSelection: (item) => item.text
        }).on('select2:select', (e) => {
            resolve(e.params.data.id);
        }).on('select2:open', () => {
            setTimeout(() => {
                $('.select2-results').css('z-index', 9999);
            }, 0);
        });
    });
};
