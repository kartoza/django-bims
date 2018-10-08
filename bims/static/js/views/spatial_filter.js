define([
    'backbone',
    'underscore',
    'jquery',
    'shared',
    'ol',
    'jquery.fileupload',
    'jquery.fileupload-process',
    'jquery.fileupload-validate'], function (Backbone, _, $, Shared, ol) {
    return Backbone.View.extend({
        template: _.template($('#spatial-filter-panel').html()),
        events: {
            'click .close-button': 'close',
            'click #spatial-filter-panel-upload': 'panelUploadClicked',
            'click .close-upload-boundary-modal': 'closeModal',
            'click .btn-boundary-upload': 'btnUploadClicked',
            'click .boundary-list-item': 'boundaryListClicked',
            'click .spatial-apply-filter': 'applyFilter',
            'click .spatial-clear-filter': 'clearFilter',
            'click .spatial-scale-apply-filter': 'applyFilter',
            'click .spatial-scale-clear-filter': 'clearSpatialFilter',
            'click #spatial-scale-container input': 'spatialScaleInputClicked'
        },
        initialize: function () {
            Shared.Dispatcher.on('spatialFilter:clearSelected', this.clearSelected, this);
        },
        render: function () {
            var self = this;

            self.$el.html(this.template());
            self.$el.find('.map-control-panel-box').hide();
            self.fileupload = self.$el.find('#fileupload');
            self.uploadButton = self.$el.find('.btn-boundary-upload');
            self.progress = self.$el.find('.process-shapefile');
            self.boundaryListContainer = self.$el.find('.boundary-list');
            self.boundaryInputText = self.$el.find('input#boundary-input-name.form-control');
            self.applyFilterButton = self.$el.find('.spatial-apply-filter');
            self.clearFilterButton = self.$el.find('.spatial-clear-filter');
            self.applyScaleFilterButton = self.$el.find('.spatial-scale-apply-filter');
            self.clearScaleFilterButton = self.$el.find('.spatial-scale-clear-filter');
            self.spatialScaleContainer = self.$el.find('#spatial-scale-container');

            self.applyFilterButton.prop('disabled', true);
            self.clearFilterButton.prop('disabled', true);

            self.getUserBoundary();
            self.getAdministrativeFilter();

            self.progress.hide();

            self.fileupload.fileupload({
                acceptFileTypes: /(\.|\/)(shp|shx|dbf)$/i,
                dataType: 'json',
                done: function (e, data) {
                    if (data.result.is_valid) {
                        self.fileupload = $(this);
                        self.$el.find("#file-list tbody").prepend(
                            "<tr><td><a href='" + data.result.url + "'>" +
                            data.result.name + "</a></td></tr>"
                        )
                    }
                }
            });

            self.fileupload.bind('fileuploadprogress', function (e, data) {
                self.uploadButton.hide();
                self.progress.html('Uploading...');
                self.progress.show();
                self.$el.find('#file-list tbody').html('');
            });

            self.fileupload.bind('fileuploadstop', function (e) {
                self.uploadButton.show();
                self.progress.html('Processing...');
                self.progress.show();
                var userBoundaryName = self.boundaryInputText.val();
                $.ajax({
                    url: '/process_user_boundary_shapefiles/',
                    data: {
                        token: csrfmiddlewaretoken,
                        name: userBoundaryName
                    },
                    dataType: 'json',
                    success: function (data) {
                        self.boundaryInputText.val('');
                        self.uploadButton.prop('disabled', true);
                        self.progress.html(data.message);
                        if (data.message === 'User boundary added') {
                            self.getUserBoundary();
                        }
                    }
                })
            });

            self.boundaryInputText.on('input', function (e) {
                var input = $(this);
                var val = input.val();

                if(val.length >= 3) {
                    self.uploadButton.prop('disabled', false);
                } else {
                    self.uploadButton.prop('disabled', true);
                }

            });

            return this;
        },
        getUserBoundary: function () {
            var self = this;
            if(!is_logged_in) {
                return false;
            }
            $.ajax({
                url: '/api/list-user-boundary/',
                dataType: 'json',
                success: function (data) {
                    Shared.UserBoundaries = data;
                    self.boundaryListContainer.html(' ');
                    $.each(data['features'], function (index, feature) {
                        var name = feature['properties']['name'];
                        var id = feature['id'];
                        var selected = '';
                        var indexOf = Shared.UserBoundarySelected.indexOf(id);
                        if (indexOf !== -1) {
                            selected = 'spatial-selected';
                        }
                        var div = $('<div class="boundary-list-item '+selected+'" data-id="'+id+'">'+
                            feature['properties']['name']+'</div>');
                        self.boundaryListContainer.append(div);
                    })
                }
            })
        },
        getAdministrativeFilter: function () {
            var self = this;
            var $wrapper = self.spatialScaleContainer;
            $.ajax({
                type: 'GET',
                url: listBoundaryAPIUrl,
                dataType: 'json',
                success: function (data) {
                    self.$el.find('.spatial-scale-menu .subtitle').click();
                    for (var i = 0; i < data.length; i++) {
                        if (data[i]['top_level_boundary']) {
                            if ($('#boundary-' + data[i]['top_level_boundary']).length > 0) {
                                $wrapper = $('#boundary-' + data[i]['top_level_boundary']);
                            }
                        }
                        $wrapper.append(
                            '<div>' +
                            '<input type="checkbox" id="'+data[i]['id']+'" name="boundary-value" value="' + data[i]['id'] + '" data-level="' + data[i]['type__level'] + '">' +
                            '&nbsp;<label for="'+data[i]['id']+'">' + data[i]['name'] + '</label>' +
                            '<div id="boundary-' + data[i]['id'] + '" style="padding-left: 15px"></div>' +
                            '</div> ');
                    }
                }
            });
        },
        spatialScaleInputClicked: function (e) {
            var $target = $(e.target);
            var child = $('#boundary-' + $target.val());
            var level = $target.data('level');
            if ($target.is(':checked')) {
                $(child).find('input:checkbox:not(:checked)[data-level="' + (level + 1) + '"]').click();
            } else {
                $(child).find('input:checkbox:checked[data-level="' + (level + 1) + '"]').click();
            }
            this.updateChecked();
        },
        updateChecked: function() {
            var checked = this.$el.find('input:checkbox:checked');
            if (checked.length > 0) {
                this.applyScaleFilterButton.prop('disabled', false);
                this.clearScaleFilterButton.prop('disabled', false);
            } else {
                this.applyScaleFilterButton.prop('disabled', true);
                this.clearScaleFilterButton.prop('disabled', true);
            }
        },
        boundaryListClicked: function (e) {
            var self = this;
            var id = $(e.target).data('id');
            var boundary = {};

            var selected = $(e.target).hasClass('spatial-selected');
            var addFeature = false;

            if (selected) {
                $(e.target).removeClass('spatial-selected');
                var index = Shared.UserBoundarySelected.indexOf(id);
                if (index !== -1) Shared.UserBoundarySelected.splice(index, 1);
            } else {
                $(e.target).addClass('spatial-selected');
                addFeature = true;
                Shared.UserBoundarySelected.push(id);
            }

            if (Shared.UserBoundarySelected.length > 0) {
                self.applyFilterButton.prop('disabled', false);
                self.clearFilterButton.prop('disabled', false);
            } else {
                self.applyFilterButton.prop('disabled', true);
                self.clearFilterButton.prop('disabled', true);
            }

            $.each(Shared.UserBoundaries['features'], function (index, feature) {
                if (feature['id'] === id) {
                    boundary = feature;
                    return true;
                }
            });

            var feature = new ol.format.GeoJSON().readFeatures(
                boundary, {
                    featureProjection: 'EPSG:3857'
                }
            );

            for (var i=0; i<feature.length;i++) {
                feature[i].setProperties({'id': 'userBoundary-'+id});
            }

            if (addFeature) {
                if (Shared.UserBoundarySelected.length === 1 && Shared.AdminAreaSelected.length === 0) {
                    Shared.Dispatcher.trigger('map:switchHighlightPinned', feature, true);
                } else {
                    Shared.Dispatcher.trigger('map:addHighlightPinnedFeature', feature[0]);
                }
            } else {
                Shared.Dispatcher.trigger('map:removeHighlightPinnedFeature', 'userBoundary-'+id);
            }

            if (Shared.UserBoundarySelected.length > 0) {
                Shared.Dispatcher.trigger('map:zoomToHighlightPinnedFeatures');
            }

        },
        isOpen: function () {
            return !this.$el.find('.map-control-panel-box').is(':hidden');
        },
        show: function () {
            this.$el.find('.map-control-panel-box').show();
        },
        close: function () {
            this.hide();
        },
        hide: function () {
            this.$el.find('.map-control-panel-box').hide();
        },
        panelUploadClicked: function (e) {
            // Show upload modal
            Shared.Dispatcher.trigger('mapControlPanel:clickSpatialFilter');
            this.$el.find('#file-list tbody').html('');
            this.boundaryInputText.val('');
            this.progress.html('');
            this.progress.hide();
            this.uploadButton.prop('disabled', true);
            this.$el.find('.modal').show();
        },
        closeModal: function (e) {
            this.$el.find('.modal').hide();
        },
        btnUploadClicked: function (e) {
            this.fileupload.click();
        },
        applyFilter: function (e) {
            Shared.Dispatcher.trigger('search:doSearch');
        },
        clearSelected: function (e) {
            this.applyFilterButton.prop('disabled', true);
            this.clearFilterButton.prop('disabled', true);
            $.each(Shared.UserBoundarySelected, function (index, id) {
                Shared.Dispatcher.trigger('map:removeHighlightPinnedFeature', 'userBoundary-'+id);
            });
            Shared.UserBoundarySelected = [];
            $.each(this.boundaryListContainer.children(), function (index, div) {
                var select = $(div);
                if(select.hasClass('spatial-selected')) {
                   select.removeClass('spatial-selected');
                }
            });
        },
        clearFilter: function (e) {
            this.clearSelected();
            if (Shared.SearchMode) {
                Shared.Dispatcher.trigger('search:doSearch');
            }
        },
        clearSpatialFilter: function (e) {
            var target = $(e.target);
            target.closest('.row').find('input:checkbox:checked').prop('checked', false);
            if (Shared.SearchMode) {
                Shared.Dispatcher.trigger('search:doSearch');
            }
        }
    })
});
