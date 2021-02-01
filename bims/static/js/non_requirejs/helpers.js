const speciesAutoComplete = (inputDiv, additionalFilters = "") => {
    return new Promise(function (resolve, reject) {
        inputDiv.autocomplete({
            source: function (request, response) {
                $.ajax({
                    url: (
                        `/species-autocomplete/?` +
                        `term=${encodeURIComponent(request.term)}` +
                        `${additionalFilters}`
                    ),
                    type: 'get',
                    dataType: 'json',
                    success: function (data) {
                        response($.map(data, function (item) {
                            return {
                                label: item.species,
                                value: item.id
                            }
                        }));
                    }
                });
            },
            minLength: 3,
            open: function (event, ui) {
                setTimeout(function () {
                    $('.ui-autocomplete').css('z-index', 9999)
                }, 0);
            },
            select: function (e, u) {
                e.preventDefault();
                console.log('clicked');
                inputDiv.val(u.item.label)
                resolve(u.item.value)
            }
        })
    })
}
