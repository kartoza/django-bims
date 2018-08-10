module.exports = function(grunt) {

    // Project configuration.
    grunt.initConfig({
        pkg: grunt.file.readJSON('/package.json'),

        requirejs: {
            compile: {
                options: {
                    baseUrl: '/usr/src/bims/bims/static/js',
                    mainConfigFile: '/usr/src/bims/bims/static/js/app.js',
                    name: 'libs/almond/almond',
                    include: ['app.js'],
                    out: '/usr/src/bims/bims/static/js/optimized.js'
                }
            }
        }

    });

    // Load plugins here.
    grunt.loadNpmTasks('grunt-contrib-concat');
    grunt.loadNpmTasks('grunt-contrib-uglify');
    grunt.loadNpmTasks('grunt-contrib-requirejs');

    // Register tasks here.
    grunt.registerTask('default', ['requirejs']);
};
