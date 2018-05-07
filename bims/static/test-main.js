var TEST_REGEXP = /(spec|test)\.js$/i;
var allTestFiles = [];

// Get a list of all the test files to include
Object.keys(window.__karma__.files).forEach(function(file) {
    if (TEST_REGEXP.test(file)) {
        // Normalize paths to RequireJS module names.
        // If you require sub-dependencies of test files to be loaded as-is (requiring file extension)
        // then do not normalize the paths
        var normalizedTestModule = file.replace(/^\/base\/|\.js$/g, '');
        allTestFiles.push(normalizedTestModule);
    }
});


require.config({
    baseUrl: "/base",
    paths: {
        jquery: '/base/bims/static/js/libs/jquery/jquery-3.3.1.min',
        bootstrap: '/base/bims/static/js/libs/bootstrap-4.0.0/js/bootstrap.bundle.min',
        openlayers: '/base/bims/static/js/libs/openlayers-4.6.4/ol',
        underscore: '/base/bims/static/js/libs/underscore-1.8.3/underscore-min',
        backbone: '/base/bims/static/js/libs/backbone-1.3.3/backbone-min',
        jqueryUi: '/base/bims/static/js/libs/jquery-ui-1.12.1/jquery-ui.min'
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
        },
        //tests
        backboneValidation: {
            deps: ['backbone']
        },
        backboneValidationBootstrap: {
            deps: ['backbone', 'backboneValidation']
        },
        serialize: {
           deps: ['jquery']
        }
    },
    // dynamically load all test files
    deps: allTestFiles,

    // we have to kickoff jasmine, as it is asynchronous
    callback: window.__karma__.start,
});
