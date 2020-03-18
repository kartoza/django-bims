module.exports = function(grunt) {

    // Project configuration.
    grunt.initConfig({
        pkg: grunt.file.readJSON('/package.json'),

        requirejs: {
            compile: {
                options: {
                    optimize: 'none',
                    out: function(text, sourceMapText) {
                        grunt.file.write('/usr/src/bims/bims/static/js/optimized.js', text);
                    },
                    baseUrl: '/usr/src/bims/bims/static/js',
                    mainConfigFile: '/usr/src/bims/bims/static/js/app.js',
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
                    '/usr/src/bims/bims/static/js/optimized.js': ['/usr/src/bims/bims/static/js/optimized.js'],
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
