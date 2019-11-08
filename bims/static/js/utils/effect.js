
// Highlight the div for 1 second
jQuery.fn.highlight = function () {
    if($(this).hasClass('item-highlight')) {
        $(this).removeClass('item-highlight');
    }
    $(this).addClass('item-highlight');
    let element = $(this);
    setTimeout(function(){ element.removeClass('item-highlight');}, 1500);
};

jQuery.fn.scrollHere = function (topMargin = 150) {
    $('html, body').animate({
        scrollTop: $(this).offset().top - topMargin
    }, 'slow');
};
