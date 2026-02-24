CKEDITOR.plugins.add('youtube', {
    icons: 'youtube',
    init: function(editor) {
        editor.addCommand('insertYoutube', new CKEDITOR.dialogCommand('youtubeDialog'));

        editor.ui.addButton('Youtube', {
            label: 'Insert YouTube Video',
            command: 'insertYoutube',
            toolbar: 'insert'
        });

        // CKEditor's built-in toolbar_Full uses *explicit* item lists for every group,
        // so buttons registered via addButton() with toolbar:'insert' won't appear
        // automatically. We inject 'Youtube' into whichever toolbar definition will
        // actually be rendered.
        function addToInsertGroup(toolbarDef) {
            if (!Array.isArray(toolbarDef)) return;
            for (var i = 0; i < toolbarDef.length; i++) {
                var group = toolbarDef[i];
                if (group && group.name === 'insert') {
                    group.items = group.items || [];
                    if (group.items.indexOf('Youtube') === -1) {
                        group.items.push('Youtube');
                    }
                    return;
                }
            }
            // No 'insert' group found — append one
            toolbarDef.push({ name: 'insert', items: ['Youtube'] });
        }

        // 1. If a named toolbar (e.g. toolbar_Custom) is explicitly defined, inject there.
        var toolbarName = editor.config.toolbar;
        if (typeof toolbarName === 'string') {
            var key = 'toolbar_' + toolbarName;
            var namedToolbar = editor.config[key] || CKEDITOR.config[key];
            if (namedToolbar) {
                addToInsertGroup(namedToolbar);
            }
        }

        // 2. Always inject into toolbar_Full — CKEditor uses it as the fallback
        //    when no matching named toolbar config is found.
        if (CKEDITOR.config.toolbar_Full) {
            addToInsertGroup(CKEDITOR.config.toolbar_Full);
        }

        // CKEditor 4 ships with CKEDITOR.config.iframe_attributes = {sandbox: ""}
        // which causes the iframe plugin to add sandbox="" to every iframe during
        // HTML output (htmlFilter) and input (dataFilter).  An empty sandbox blocks
        // all scripts, breaking YouTube embeds.  Strip it from YouTube iframes only.
        function removeYoutubeSandbox(el) {
            var src = el.attributes && (el.attributes.src || '');
            if (src.indexOf('youtube.com/embed/') !== -1) {
                delete el.attributes.sandbox;
            }
        }

        editor.dataProcessor.htmlFilter.addRules({ elements: { iframe: removeYoutubeSandbox } });
        editor.dataProcessor.dataFilter.addRules({ elements: { iframe: removeYoutubeSandbox } });

        CKEDITOR.dialog.add('youtubeDialog', function() {
            return {
                title: 'Insert YouTube Video',
                minWidth: 400,
                minHeight: 160,
                contents: [
                    {
                        id: 'tab1',
                        label: 'YouTube Video',
                        elements: [
                            {
                                type: 'text',
                                id: 'url',
                                label: 'YouTube URL (e.g. https://www.youtube.com/watch?v=...)',
                                validate: CKEDITOR.dialog.validate.notEmpty('Please enter a YouTube URL.')
                            },
                            {
                                type: 'text',
                                id: 'width',
                                label: 'Width (px)',
                                'default': '560'
                            },
                            {
                                type: 'text',
                                id: 'height',
                                label: 'Height (px)',
                                'default': '315'
                            }
                        ]
                    }
                ],
                onOk: function() {
                    var url = this.getValueOf('tab1', 'url').trim();
                    var width = this.getValueOf('tab1', 'width') || '560';
                    var height = this.getValueOf('tab1', 'height') || '315';

                    var videoId = null;
                    var match = url.match(
                        /(?:youtube\.com\/(?:watch\?(?:.*&)?v=|embed\/|v\/|shorts\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/
                    );
                    if (match) {
                        videoId = match[1];
                    }

                    if (!videoId) {
                        alert('Could not find a YouTube video ID in the URL you entered.\n\nSupported formats:\n  https://www.youtube.com/watch?v=VIDEO_ID\n  https://youtu.be/VIDEO_ID\n  https://www.youtube.com/shorts/VIDEO_ID');
                        return false;
                    }

                    var embedUrl = 'https://www.youtube.com/embed/' + videoId;
                    var html = '<div class="youtube-embed" style="width: 100%;display:flex;justify-content:center;margin:1em 0;">' +
                        '<iframe width="' + parseInt(width, 10) + '" height="' + parseInt(height, 10) + '"' +
                        ' src="' + embedUrl + '"' +
                        ' frameborder="0"' +
                        ' allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"' +
                        ' referrerpolicy="strict-origin-when-cross-origin"'+
                        ' allowfullscreen></iframe>' +
                        '</div>';

                    editor.insertHtml(html);
                }
            };
        });
    }
});
