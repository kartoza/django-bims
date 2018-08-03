define(['shared', 'backbone', 'underscore', 'jqueryUi'], function (Shared, Backbone, _) {
    return Backbone.View.extend({
        className: 'geonode-layer-control-panel',
        template: _.template($('#geonode-layer-control-panel').html()),
        geonodeLayerAPIUrl: '/api/layers',
        geonodeLayers: {},
        events: {
            'click .geonode-layer-control': 'toggleFormat',
            'click .map-search-close': 'closeGeonodeLayerPanel',
            'keyup #geonode-layer-search': 'showLayers'
        },
        initialize: function (options) {
            this.parent = options.parent;
        },
        render: function () {
            this.$el.html(this.template());
            return this;
        },
        toggleFormat: function () {
            if ($('.geonode-layer-search-box').is(":hidden")) {
                this.parent.resetAllControlState();
                this.$el.find('.sub-control-panel').addClass('control-panel-selected');
                $('.geonode-layer-search-box').show();
                this.getGeonodeLayers();
            } else {
                this.$el.find('.sub-control-panel').removeClass('control-panel-selected');
                $('.geonode-layer-search-box').hide();
            }
        },
        closeGeonodeLayerPanel: function () {
             if (!$('.geonode-layer-search-box').is(":hidden")) {
                this.$el.find('.sub-control-panel').removeClass('control-panel-selected');
                $('.geonode-layer-search-box').hide();
            }
        },
        showLayers: function () {
            var self = this;

            // Clear list
            $('#list-geonode-layers').empty("");

            // Filter layer name, put to new temp variable
            if (!jQuery.isEmptyObject(this.geonodeLayers)){
                var filtered_layers = this.filterGeonodeLayers($('#geonode-layer-search').val());
            }
            else {
                $('#list-geonode-layers').append("<li>No layers found" +
                    " from your GeoNode</li>");
                return;
            }
            if (jQuery.isEmptyObject(filtered_layers)){
                $('#list-geonode-layers').append("<li>No layers found from your filter keyword</li>");
                return;
            }

            // Iterate to show them in list-geonode-layers
            var i = 0;
            $.each(filtered_layers, function (index, geonode_layer) {
                            var list_layer_html = "";

                var button_text = null;
                if (geonode_layer['added']){
                    button_text = 'Remove';
                }else {
                    button_text = 'Add';
                }
                button = '    <button type="button" class="btn btn-secondary' +
                    ' btn-sm" id="layer-button-' + geonode_layer['name'] + '">' +  button_text + '</button>';
                list_layer_html = list_layer_html.concat(
                    '<li data-format="' + index + '">'+ geonode_layer['title'] + button + '</li>'
                );

                $('#list-geonode-layers').append(list_layer_html);

                // Remove handler first
                $('#layer-button-' + geonode_layer['name']).off('click');
                $('#layer-button-' + geonode_layer['name']).click(function () {
                        self.toggleLayer(index)
                });
                i ++;
                // Only show the first 5
                if (i > 5){
                    return false;
                }
            });

        },
        getGeonodeLayers: function () {
            var self = this;

            if (this.geonodeLayersXhr){
                this.geonodeLayersXhr.abort()
            }

            this.geonodeLayersXhr = $.get({
                url: this.geonodeLayerAPIUrl,
                dataType: 'json',
                success: function (data) {
                    $.each(data['objects'], function (index, geonode_layer) {
                        self.geonodeLayers[geonode_layer['typename']] = geonode_layer;
                    });

                    self.showLayers();
                },
                error: function (req, err) {
                    console.log(req);
                    console.log(err);
                }
            });
        },
        filterGeonodeLayers: function (keyword) {
            var self = this;

            var filtered_layers = {};
            $.each(self.geonodeLayers, function (index, geonode_layer) {
                if (geonode_layer['title'].toLowerCase().includes(keyword)){
                    filtered_layers[index] = geonode_layer;
                }
            });
            return filtered_layers;
        },
        toggleLayer: function (layerTypename) {
            var self = this;
            if (self.geonodeLayers[layerTypename]['added']){
                self.geonodeLayers[layerTypename]['added'] = false;
                $('#layer-button-' + self.geonodeLayers[layerTypename]['name']).html('Add');
            } else {
                self.geonodeLayers[layerTypename]['added'] = true;
                $('#layer-button-' + self.geonodeLayers[layerTypename]['name']).html('Remove');
            }

        }
    })
});
