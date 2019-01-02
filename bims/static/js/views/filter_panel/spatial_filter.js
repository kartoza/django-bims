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
        selectedPoliticalRegions: [],
        selectedRiverCatchments: [],
        politicalBoundaryInputName: 'political-boundary-value',
        riverCatchmentInputName: 'river-catchment-value',
        topLevel: 2,
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
            'click .boundary-item-input': 'itemInputClicked',
            'click .boundary-item': 'toggleChildFilters',
            'click .spatial-scale-sub-panel': 'subPanelClicked'
        },
        initialize: function () {
            Shared.Dispatcher.on('spatialFilter:clearSelected', this.clearAllSelected, this);
        },
        render: function () {
            var self = this;

            self.$el.html(this.template());
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
            self.riverCatchmentContainer = self.$el.find('#river-catchment-container');

            self.applyFilterButton.prop('disabled', true);
            self.clearFilterButton.prop('disabled', true);

            self.getUserBoundary();
            self.getAdministrativeFilter();
            self.getRiverCatchmentFilter();

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

                if (val.length >= 3) {
                    self.uploadButton.prop('disabled', false);
                } else {
                    self.uploadButton.prop('disabled', true);
                }

            });

            return this;
        },
        getUserBoundary: function () {
            var self = this;
            if (!is_logged_in) {
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
                        var div = $('<div class="boundary-list-item ' + selected + '" data-id="' + id + '">' +
                            feature['properties']['name'] + '</div>');
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
                    Shared.PoliticalRegionBoundaries = data;
                    self.renderChildTree(data, self.spatialScaleContainer, 1, self.politicalBoundaryInputName);
                }
            });
        },
        getRiverCatchmentFilter: function () {
            var self = this;
            $.ajax({
                type: 'GET',
                url: '/api/river-catchment-list/',
                dataType: 'json',
                success: function (data) {
                    self.renderChildTree(data, self.riverCatchmentContainer, 1, self.riverCatchmentInputName);
                }
            });
        },
        renderChildTree: function (data, wrapper, level, name) {
            var self = this;
            var $itemWrapper = $('<div class="boundary-item-child"></div>');
            if (level > 1) {
                $itemWrapper.hide();
                wrapper.append($itemWrapper);
                wrapper = $itemWrapper;
            }
            for (var i = 0; i < data.length; i++) {
                var label = '';
                if (data[i].hasOwnProperty('name')) {
                    label = data[i]['name'];
                } else {
                    label = data[i]['value'];
                }
                var $item = $('<div class="boundary-item"></div>');
                $item.append('<input class="boundary-item-input" type="checkbox" data-level="' + level + '" name="' + name + '" value="' + data[i]['value'] + '">');
                $item.append('<label> ' + label + '</label>');
                wrapper.append($item);
                if (data[i]['children'].length > 0) {
                    $item.append('<i class="fa fa-plus-square-o pull-right" aria-hidden="true"> </i>');
                    self.renderChildTree(data[i]['children'], $item, level + 1, name);
                }
            }
        },
        itemInputClicked: function (e) {
            var $target = $(e.target);
            var targetName = $target.prop('name');
            var value = $target.val();
            var $wrapper = $target.parent();
            var level = $target.data('level');
            if ($target.is(':checked')) {
                this.addSelectedValue(targetName, value);
                var $children = $wrapper.children().find('input:checkbox:not(:checked)');
                $children.prop('checked', true);
                var $checkedChildren = $wrapper.children().find('input:checkbox:checked');
                for (var j = 0; j < $checkedChildren.length; j++) {
                    var childrenValue = $($checkedChildren[j]).val();
                    this.removeSelectedValue(targetName, childrenValue);
                }
            } else {
                // Uncheck parents
                if (level > 1) {
                    var $parent = $wrapper.parent();
                    for (var i = level - 1; i >= 1; i--) {
                        var $checked = $parent.find('input:checkbox:checked[data-level="' + (i + 1) + '"]');
                        $parent = $parent.parent().find('input:checkbox:checked[data-level="' + (i) + '"]').prop('checked', false);
                        this.removeSelectedValue(targetName, $parent.val());
                        for (var j = 0; j < $checked.length; j++) {
                            var checkedValue = $($checked[j]).val();
                            this.addSelectedValue(targetName, checkedValue);
                        }
                        $parent = $parent.parent().parent();
                    }
                }

                this.removeSelectedValue(targetName, value);
                $wrapper.children().find('input:checkbox:checked').prop('checked', false);
            }
            this.updateChecked();
        },
        addSelectedValue: function (targetName, value) {
            var array = null;
            if (targetName === this.politicalBoundaryInputName) {
                array = this.selectedPoliticalRegions;
            } else {
                array = this.selectedRiverCatchments;
            }
            if (!array.includes(value)) {
                array.push(value);
            }
        },
        removeSelectedValue: function (targetName, value) {
            var array = null;
            if (targetName === this.politicalBoundaryInputName) {
                array = this.selectedPoliticalRegions;
            } else {
                array = this.selectedRiverCatchments;
            }
            var index = array.indexOf(value);
            if (index !== -1) array.splice(index, 1);
        },
        toggleChildFilters: function (e) {
            var $target = $(e.target);
            e.stopPropagation();

            if ($target.is('input')) {
                return true;
            }
            if (!$target.hasClass('boundary-item')) {
                $target = $target.parent();
            }
            var children = $target.children();
            for (var i = 0; i < children.length; i++) {
                var _children = $(children[i]);
                if (_children.hasClass('fa-plus-square-o')) {
                    _children.removeClass('fa-plus-square-o');
                    _children.addClass('fa-minus-square-o');
                }
                else if (_children.hasClass('fa-minus-square-o')) {
                    _children.removeClass('fa-minus-square-o');
                    _children.addClass('fa-plus-square-o');
                }
                else if (_children.hasClass('boundary-item-child')) {
                    _children.toggle();
                }
            }
        },
        updateChecked: function () {
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

            for (var i = 0; i < feature.length; i++) {
                feature[i].setProperties({'id': 'userBoundary-' + id});
            }

            if (addFeature) {
                if (Shared.UserBoundarySelected.length === 1 && Shared.AdminAreaSelected.length === 0) {
                    Shared.Dispatcher.trigger('map:switchHighlightPinned', feature, true);
                } else {
                    Shared.Dispatcher.trigger('map:addHighlightPinnedFeature', feature[0]);
                }
            } else {
                Shared.Dispatcher.trigger('map:removeHighlightPinnedFeature', 'userBoundary-' + id);
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
        clearAllSelected: function (e) {
            this.clearSelected(e);
            this.selectedRiverCatchments = [];
            this.selectedPoliticalRegions = [];
            this.spatialScaleContainer.closest('.row').find('input:checkbox:checked').prop('checked', false);
            this.riverCatchmentContainer.closest('.row').find('input:checkbox:checked').prop('checked', false);
            this.applyScaleFilterButton.prop('disabled', true);
            this.clearScaleFilterButton.prop('disabled', true);
        },
        clearSelected: function (e) {
            this.applyFilterButton.prop('disabled', true);
            this.clearFilterButton.prop('disabled', true);
            $.each(Shared.UserBoundarySelected, function (index, id) {
                Shared.Dispatcher.trigger('map:removeHighlightPinnedFeature', 'userBoundary-' + id);
            });
            Shared.UserBoundarySelected = [];
            $.each(this.boundaryListContainer.children(), function (index, div) {
                var select = $(div);
                if (select.hasClass('spatial-selected')) {
                    select.removeClass('spatial-selected');
                }
            });
        },
        clearFilter: function (e) {
            this.clearSelected();
            if (Shared.CurrentState.SEARCH) {
                Shared.Dispatcher.trigger('search:doSearch');
            }
        },
        clearSpatialFilter: function (e) {
            var target = $(e.target);
            target.closest('.row').find('input:checkbox:checked').prop('checked', false);
            this.clearAllSelected(e);
            if (Shared.CurrentState.SEARCH) {
                Shared.Dispatcher.trigger('search:doSearch');
            }
        },
        subPanelClicked: function (e) {
            var $panel = $($(e.target).next().get(0));
            $panel.toggle();

            var $target = $(e.target);

            if ($target.hasClass('small-subtitle')) {
                $target = $target.children();
                if ($target.hasClass('fa-angle-down')) {
                    $target.removeClass('fa-angle-down');
                    $target.addClass('fa-angle-up');
                } else {
                    $target.removeClass('fa-angle-up');
                    $target.addClass('fa-angle-down');
                }
            }
        },
        getNodesWithoutChildren: function (boundaries, idsArray, isRoot = false) {
            var nodeIds = [];
            var self = this;
            $.each(boundaries, function (index, boundary) {
                if (idsArray.includes(boundary['value'].toString())) {
                    if (boundary['children'].length > 0) {
                        nodeIds.push.apply(nodeIds, self.getNodesWithoutChildren(boundary['children'], idsArray));
                    }
                }
                else if (!isRoot) {
                    nodeIds.push(boundary['value']);
                    if (boundary['children'].length > 0) {
                        nodeIds.push.apply(nodeIds, self.getNodesWithoutChildren(boundary['children'], idsArray));
                    }
                }
            });
            return nodeIds;
        },
    })
});
