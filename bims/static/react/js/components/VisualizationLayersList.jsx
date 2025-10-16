import React, { useState, useEffect } from 'react';
import axios from "axios";
import SortableList, {SortableItem, SortableKnob} from "react-easy-sort";
import { arrayMoveImmutable } from "array-move";
import "bootstrap-icons/font/bootstrap-icons.css";
import {Badge, Button} from "reactstrap";
import VisualizationLayerForm from "./AddVisualizationLayer";
import LayerGroupForm from "./AddLayerGroup";


const VisualizationLayersList = (props) => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filterText, setFilterText] = useState('');
    const [isFormOpen, setIsFormOpen] = useState(false);
    const [isGroupFormOpen, setIsGroupFormOpen] = useState(false);
    const [selectedLayer, setSelectedLayer] = useState(null);

    const [visualizationLayers, setVisualizationLayers] = useState([]);

    const api = '/api/visualization-layers/';
    const listApi = '/api/list-non-biodiversity/';
    const layerGroupApi = '/api/layer-group/';

    const updateOrder = async (updatedLayers, refresh=false) => {
        try {
            const data = {
                layers: updatedLayers,
            };
            await axios.put(api, data, {
                headers: {
                    'X-CSRFToken': props.csrfToken,
                    'Content-Type': 'application/json'
                }
            });
            console.log("Order updated successfully.");
            if (refresh) {
                setVisualizationLayers([]);
                fetchVisualizationLayers();
            }
        } catch (error) {
            console.error("Failed to update order:", error);
        }
    };

    const fetchVisualizationLayers = async () => {
        try {
            setLoading(true);
            const response = await axios.get(listApi);
            setVisualizationLayers(response.data);
        } catch (error) {
            console.error("Error fetching layers:", error);
            setError("Failed to load layers");
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteLayer = async (e, layer) => {
        e.stopPropagation();
        const isConfirmed = window.confirm(`Are you sure you want to delete the layer "${layer.name}"?`);
        if (!isConfirmed) {
            return; // Do nothing if the user cancels the confirmation
        }
        let layerId = layer.id;
        try {
            const deleteUrl = `${api}?id=${layerId}`;
            await axios.delete(deleteUrl, {
                headers: {
                    'X-CSRFToken': props.csrfToken
                }
            });
            console.log(`Layer ${layerId} deleted successfully.`);
            fetchVisualizationLayers();
        } catch (error) {
            console.error(`Failed to delete layer ${layerId}:`, error);
        }
    };

    const handleEditGroup = async (e, group) => {
        setSelectedLayer(group)
        setIsGroupFormOpen(true);
    }

    const handleDeleteGroup = async (e, group) => {
        e.stopPropagation();
        const isConfirmed = window.confirm(`Are you sure you want to delete the group "${group.name}"?`);
        if (!isConfirmed) {
            return; // Do nothing if the user cancels the confirmation
        }
        let groupId = group.id;
        try {
            const deleteUrl = `${layerGroupApi}?id=${groupId}`;
            await axios.delete(deleteUrl, {
                headers: {
                    'X-CSRFToken': props.csrfToken
                }
            });
            console.log(`Group ${groupId} deleted successfully.`);
            fetchVisualizationLayers();
        } catch (error) {
            console.error(`Failed to delete group ${groupId}:`, error);
        }
    }

    useEffect(() => {
        fetchVisualizationLayers();
    }, []);

    const toggleForm = () => {
        setIsFormOpen(!isFormOpen)
    }

    const onSortEnd = (oldIndex, newIndex) => {
        const updatedFilters = arrayMoveImmutable(visualizationLayers, oldIndex, newIndex).map((layer, index) => ({
            id: layer.id,
            type: layer.type,
            display_order: index + 1
        }));

        updateOrder(updatedFilters)
        setVisualizationLayers(arrayMoveImmutable(visualizationLayers, oldIndex, newIndex))
    };

    const handleFilterChange = (e) => {
        setFilterText(e.target.value);
    };

    const toggleAddVisualizationLayer = () => {
        setSelectedLayer(null);
        setIsFormOpen(!isFormOpen);
    }

    const toggleAddLayerGroup = () => {
        setSelectedLayer(null);
        setIsGroupFormOpen(!isGroupFormOpen);
    }

    const handleEditLayer = (e, layer) => {
        setSelectedLayer(layer)
        setIsFormOpen(true);
    }

    const filteredLayers = visualizationLayers.filter(group =>
        group.name.toLowerCase().includes(filterText.toLowerCase())
    );

    const onAdded = () => {
        setVisualizationLayers([]);
        fetchVisualizationLayers();
    }

    const onSortEndRoot = (oldIndex, newIndex) => {
        const next = arrayMoveImmutable(visualizationLayers, oldIndex, newIndex);
        setVisualizationLayers(next);
        updateOrder(next.map((l, i) => ({ id: l.id, type: l.type, display_order: i + 1 })));
      };

      const onSortEndGroup = (groupId) => (oldIndex, newIndex) => {
        const next = visualizationLayers.map((g) => {
          if (g.id !== groupId) return g;
          const moved = arrayMoveImmutable(g.layers, oldIndex, newIndex);
          updateOrder(moved.map((l, i) => ({ id: l.id, type: l.type, display_order: i + 1 })));
          return { ...g, layers: moved };
        });
        setVisualizationLayers(next);
      };

    const renderLayersOrGroups = (items, parentId = null) => (
        <SortableList
          onSortEnd={parentId ? onSortEndGroup(parentId) : onSortEndRoot}
          className="context-filter-list col-md-12"
          draggedItemClassName="dragged"
        >
          {items.map((layer) => (
            <SortableItem key={layer.id} className="col-md-12">
              <div className="item">
                <div className="context-filter-header">
                  <SortableKnob>
                    <span>
                      <i className="bi bi-grip-vertical" />
                    </span>
                  </SortableKnob>
                  {layer.name}
                  {layer.type === 'Layer' && (
                    <Badge color={layer.native_layer ? 'warning' : 'primary'} style={{ marginLeft: 5 }}>
                      {layer.native_layer ? 'Native Layer' : 'WMS'}
                    </Badge>
                  )}
                  <Button
                    color="danger"
                    size="sm"
                    outline
                    onClick={(e) =>
                      layer.type === 'Layer' ? handleDeleteLayer(e, layer) : handleDeleteGroup(e, layer)
                    }
                    style={{ float: 'right', right: 0, marginTop: -5, marginRight: 5 }}
                  >
                    <i className="bi bi-trash" />
                  </Button>
                  <Button
                    color="warning"
                    size="sm"
                    outline
                    onClick={(e) =>
                      layer.type === 'Layer' ? handleEditLayer(e, layer) : handleEditGroup(e, layer)
                    }
                    style={{ float: 'right', right: 0, marginTop: -5, marginRight: 5 }}
                  >
                    <i className="bi bi-pencil" />
                  </Button>
                </div>
                {layer.type === 'LayerGroup' && (
                  <div style={{ paddingLeft: 10 }}>{renderLayersOrGroups(layer.layers, layer.id)}</div>
                )}
              </div>
            </SortableItem>
          ))}
        </SortableList>
      );

    if (loading) {
        return <div>Loading...</div>;
    }

    if (error) {
        return <div>{error}</div>;
    }

    return (
        <div style={{paddingBottom: 40}}>
            <div className="filter-input">
                <input
                    type="text"
                    placeholder="Filter by name"
                    value={filterText}
                    onChange={handleFilterChange}
                    className="form-control mb-2"
                />
            </div>
            <div>
                <Button color={'success'} size={'sm'} style={{ marginBottom: 5 }} onClick={toggleAddVisualizationLayer}>
                    <i className="bi bi-plus"></i> Add visualization layer
                </Button>
                <Button color={'success'} size={'sm'} style={{ marginBottom: 5, marginLeft: 10 }} onClick={toggleAddLayerGroup}>
                    <i className="bi bi-plus"></i> Add layer group
                </Button>
            </div>
            <div className="row">
                <SortableList onSortEnd={onSortEnd} className='context-filter-list col-md-12' draggedItemClassName={'dragged'}>
                    {
                        renderLayersOrGroups(filteredLayers)
                    }
                </SortableList>
            </div>

            <VisualizationLayerForm isOpen={isFormOpen} toggle={toggleForm} csrfToken={props.csrfToken} onAdded={onAdded} selectedLayer={selectedLayer}/>
            <LayerGroupForm isOpen={isGroupFormOpen} selectedGroup={selectedLayer} onAdded={onAdded} toggle={() => setIsGroupFormOpen(!isGroupFormOpen)} csrfToken={props.csrfToken}/>

        </div>
    );
}

export default VisualizationLayersList;
