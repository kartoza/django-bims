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
            'Password must contain at least six characters, including: <ul>' +
        '<li> lower case letter </li>' +
        '<li> upper case letter </li>'+
        '<li> numeric character </li></ul>'+
        '</div>';
    $(passwordMessage).insertBefore('#id_password1');
});
