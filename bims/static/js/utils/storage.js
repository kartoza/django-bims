define(['backbone', 'utils/class'], function (Backbone, UtilClass) {
    var LocalStorage = UtilClass.extend({
        initialize: function () {
            
        },
        isStorageSupported: function () {
            return (typeof(Storage) !== 'undefined');
        },
        setItem: function (key, value) {
            if (this.isStorageSupported()) {
                localStorage.setItem(key, value);   
            }
        },
        getItem: function (key) {
            if (this.isStorageSupported()) {
                return JSON.parse(localStorage.getItem(key));
            }
            return null;
        }
    });

    return LocalStorage;
});
