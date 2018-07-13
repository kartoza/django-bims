module.exports = function(grunt) {

    // Project configuration.
    grunt.initConfig({
        pkg: grunt.file.readJSON('/package.json'),

        requirejs: {
            compile: {
                options: {
                    baseUrl: '/home/web/django_project/bims/static/js',
                    mainConfigFile: '/home/web/django_project/bims/static/js/app.js',
                    name: 'libs/almond/almond',
                    include: ['app.js'],
                    out: '/home/web/django_project/bims/static/js/optimized.js'
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
