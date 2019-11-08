
let fontAwesomeIcon = function (iconName, color = null) {
    let _color = '';
    if (color) {
        _color = `color: ${color}`;
    }
    return `<i class="fa fa-${iconName}" aria-hidden="true" style="${_color}"/>`;
};
