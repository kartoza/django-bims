const terserOptions = {
    compress: {
        passes: 3,
    },
    ecma: 8,
    output: {
        beautify: false,
    },
    toplevel: true,
};


module.exports = function(grunt) {

    // Project configuration.
    grunt.initConfig({
        pkg: grunt.file.readJSON('/package.json'),

        requirejs: {
            compile: {
                options: {
                    optimize: 'none',
                    out: function(text, sourceMapText) {
                        const terser = require('terser');
                        let contents = terser.minify(text, terserOptions).code();
                        grunt.file.write('/usr/src/bims/bims/static/js/optimized.js', contents);
                    },
                    baseUrl: '/usr/src/bims/bims/static/js',
                    mainConfigFile: '/usr/src/bims/bims/static/js/app.js',
                    name: 'libs/almond/almond',
                    include: ['app.js'],
                }
            }
        }

    });

    // Load plugins here.
    grunt.loadNpmTasks('grunt-contrib-concat');
    grunt.loadNpmTasks('grunt-contrib-requirejs');

    // Register tasks here.
    grunt.registerTask('default', ['requirejs']);
};
