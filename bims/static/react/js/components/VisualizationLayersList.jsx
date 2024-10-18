import React, { useState, useEffect } from 'react';
import axios from "axios";
import SortableList, {SortableItem, SortableKnob} from "react-easy-sort";
import { arrayMoveImmutable } from "array-move";
import "bootstrap-icons/font/bootstrap-icons.css";
import {Badge, Button} from "reactstrap";
import VisualizationLayerForm from "./AddVisualizationLayer";


const VisualizationLayersList = (props) => {
    const [loading, setLoading] = useState(true);
    const [contextFilters, setContextFilters] = useState([]);
    const [error, setError] = useState(null);
    const [filterText, setFilterText] = useState('');
    const [isAddNewGroupModalOpen, setIsAddNewGroupModalOpen] = useState(false);
    const [isAddNewFilterModalOpen, setIsAddNewFilterModalOpen] = useState(false);
    const [newFilterName, setNewFilterName] = useState('');
    const [savingNewFilter, setSavingNewFilter] = useState(false);
    const [isFormOpen, setIsFormOpen] = useState(false);
    const [selectedLayer, setSelectedLayer] = useState(null);

    const [visualizationLayers, setVisualizationLayers] = useState([]);

    const api = '/api/visualization-layers/';

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
            const response = await axios.get(api);
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

    useEffect(() => {
        fetchVisualizationLayers();
    }, []);

    const toggleForm = () => {
        setIsFormOpen(!isFormOpen)
    }

    const onSortEnd = (oldIndex, newIndex) => {
        const updatedFilters = arrayMoveImmutable(visualizationLayers, oldIndex, newIndex).map((layer, index) => ({
            id: layer.id,
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
            </div>
            <div className="row">
                <SortableList onSortEnd={onSortEnd} className='context-filter-list col-md-12' draggedItemClassName={'dragged'}>
                    {filteredLayers.map((visualizationLayer) => (
                        <SortableItem className="col-md-12" key={visualizationLayer.id}>
                            <div className="item">
                                <div
                                    className="context-filter-header"
                                >
                                    <SortableKnob>
                                        <span><i className="bi bi-grip-vertical"></i></span>
                                    </SortableKnob>
                                    {visualizationLayer.name}
                                    <Badge color={visualizationLayer.native_layer ? "warning" : "primary"} style={{marginLeft:5}}>
                                        {visualizationLayer.native_layer ? 'Native Layer':'WMS' }
                                    </Badge>
                                    <Button color={'danger'} size={'sm'}
                                            outline
                                            onClick={(e) => handleDeleteLayer(e, visualizationLayer)}
                                            style={{float: 'right', right: 0, marginTop: -5, marginRight: 5}}>
                                        <i className="bi bi-trash"></i>
                                    </Button>
                                    <Button color={'warning'} size={'sm'}
                                            outline
                                            onClick={(e) => handleEditLayer(e, visualizationLayer)}
                                            style={{float: 'right', right: 0, marginTop: -5, marginRight: 5}}>
                                        <i className="bi bi-pencil"></i>
                                    </Button>
                                </div>
                            </div>
                        </SortableItem>
                    ))}
                </SortableList>
            </div>

            <VisualizationLayerForm isOpen={isFormOpen} toggle={toggleForm} csrfToken={props.csrfToken} onAdded={onAdded} selectedLayer={selectedLayer}/>

        </div>
    );
}

export default VisualizationLayersList;
