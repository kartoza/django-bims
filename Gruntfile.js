module.exports = function(grunt) {

    // Project configuration.
    grunt.initConfig({
        pkg: grunt.file.readJSON('/package.json'),

        requirejs: {
            compile: {
                options: {
                    optimize: 'none',
                    out: function(text, sourceMapText) {
                        grunt.file.write('/home/web/django_project/bims/static/js/optimized.js', text);
                    },
                    baseUrl: '/home/web/django_project/bims/static/js',
                    mainConfigFile: '/home/web/django_project/bims/static/js/app.js',
                    name: 'libs/almond/almond',
                    include: ['app.js'],
                }
            }
        },
        terser: {
            options: {
                compress: true,
            },
            main: {
                files: {
                    '/home/web/django_project/bims/static/js/optimized.js': ['/home/web/django_project/bims/static/js/optimized.js'],
                }
            }
        }

    });

    // Load plugins here.
    grunt.loadNpmTasks('grunt-terser');
    grunt.loadNpmTasks('grunt-contrib-concat');
    grunt.loadNpmTasks('grunt-contrib-requirejs');

    // Register tasks here.
    grunt.registerTask('default', ['requirejs', 'terser']);
};
