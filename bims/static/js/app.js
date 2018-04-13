require.config({
    paths: {
        jquery: 'libs/jquery/jquery-3.3.1.min',
        bootstrap: 'libs/bootstrap-4.0.0/js/bootstrap.bundle.min',
        openlayers: 'libs/openlayers-4.6.4/ol',
        underscore: 'libs/underscore-1.8.3/underscore-min',
        backbone: 'libs/backbone-1.3.3/backbone-min',
        jqueryUi: 'libs/jquery-ui-1.12.1/jquery-ui.min'
    },
    shim: {
        openlayers: {
            exports: 'ol'
        },
        underscore: {
            exports: '_'
        },
        backbone: {
            deps: [
                'underscore',
                'jquery'
            ],
            exports: 'Backbone'
        },
        app: {
            deps: ['backbone']
        }
    }
});

require( [
    'views/olmap',
    'views/side_panel',
    'collections/location_site',
    'shared',
    'app'
], function(olmap, side_panel, LocationSiteCollection, Shared, App) {
    // Display the map
    var locationSiteCollection = new LocationSiteCollection();
    var map = new olmap({
        collection: locationSiteCollection
    });

    var panel = new side_panel();
    panel.render();
});
