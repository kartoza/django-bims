var config = {
    '.chosen-select'           : {},
    '.chosen-select-deselect'  : {allow_single_deselect:true},
    '.chosen-select-no-single' : {disable_search_threshold:10},
    '.chosen-select-no-results': {no_results_text:'Oops, nothing found!'},
    '.chosen-select-width'     : {width:"95%"}
};

for (var selector in config) {
    $(selector).chosen(config[selector]);
}

$(document).ready(function () {

    var passwordMessage = '<div class="alert alert-info password-message" role="alert">' +
            'Password must be <strong>at least 12 characters</strong> and include: <ul>' +
        '<li> a lowercase letter </li>' +
        '<li> an uppercase letter </li>'+
        '<li> a number </li>'+
        '<li> a symbol (e.g. !@#$) </li></ul>'+
        '</div>';
    $(passwordMessage).insertBefore('#id_password1');
});
