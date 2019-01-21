module.exports = function(grunt) {

    // Project configuration.
    grunt.initConfig({
        pkg: grunt.file.readJSON('/package.json'),

        requirejs: {
            compile: {
                options: {
                    optimize: 'none',
                    out: function(text, sourceMapText) {
                        var UglifyJS = require('uglify-es'),
                        uglified = UglifyJS.minify(text);
                        grunt.file.write('/usr/src/bims/bims/static/js/optimized.js', uglified.code);
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
    grunt.loadNpmTasks('grunt-contrib-uglify-es');
    grunt.loadNpmTasks('grunt-contrib-requirejs');

    // Register tasks here.
    grunt.registerTask('default', ['requirejs']);
};
