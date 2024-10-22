import React, { useState, useEffect } from 'react';
import axios from "axios";
import SortableList, {SortableItem, SortableKnob} from "react-easy-sort";
import { arrayMoveImmutable } from "array-move";
import "bootstrap-icons/font/bootstrap-icons.css";
import {Button, Form, FormGroup, Input, Label, Modal, ModalBody, ModalFooter, ModalHeader} from "reactstrap";
import AddContextGroup from "./AddContextGroup";
import GeocontextListModal from "./GeocontextListModal";


const ContextFilterView = (props) => {
    const [loading, setLoading] = useState(true);
    const [contextFilters, setContextFilters] = useState([]);
    const [error, setError] = useState(null);
    const [filterText, setFilterText] = useState('');
    const [expandedGroups, setExpandedGroups] = useState({});
    const [childContextGroups, setChildContextGroups] = useState({});
    const [isAddNewGroupModalOpen, setIsAddNewGroupModalOpen] = useState(false);
    const [selectedFilter, setSelectedFilter] = useState(null);
    const [contextGroups, setContextGroups] = useState([]);
    const [isAddNewFilterModalOpen, setIsAddNewFilterModalOpen] = useState(false);
    const [newFilterName, setNewFilterName] = useState('');
    const [savingNewFilter, setSavingNewFilter] = useState(false);
    const [isGeocontextListOpen, setIsGeocontextListOpen] = useState(false);

    const contextLayerFilterAPI = '/api/context-filter/';
    const contextLayerGroupAPI = '/api/context-layer-group/';

    const updateOrder = async (updatedFilters, updatedGroups, refresh=false) => {
        try {
            const data = {
                filters: updatedFilters,
                groups: updatedGroups
            };
            await axios.put(contextLayerFilterAPI, data, {
                headers: {
                    'X-CSRFToken': props.csrfToken,
                    'Content-Type': 'application/json'
                }
            });
            console.log("Order updated successfully.");
            if (refresh) {
                setContextFilters([]);
                fetchContextFilters();
            }
        } catch (error) {
            console.error("Failed to update order:", error);
        }
    };

    const deleteContextFilter = async (filterId) => {
        try {
            const deleteUrl = `${contextLayerFilterAPI}?filter_id=${filterId}`;
            await axios.delete(deleteUrl, {
                headers: {
                    'X-CSRFToken': props.csrfToken
                }
            });
            console.log(`Filter ${filterId} deleted successfully.`);

            // Optionally, refresh the context filters after deletion
            setContextFilters([]);
            fetchContextFilters();
        } catch (error) {
            console.error(`Failed to delete filter ${filterId}:`, error);
        }
    };

    const fetchContextGroups = async () => {
        setContextGroups([])
        try {
            const response = await axios.get(contextLayerGroupAPI);
            setContextGroups(response.data);
        } catch (error) {
            console.error("Error fetching context groups:", error);
            setError("Failed to load context groups");
        } finally {
        }
    };

    const fetchContextFilters = async () => {
        setContextFilters([]);
        try {
            setLoading(true);
            const response = await axios.get(contextLayerFilterAPI);
            setContextFilters(response.data);

            // Default to expanded for all groups
            const defaultExpanded = {};
            const defaultChildGroups = {};
            response.data.forEach(group => {
                defaultExpanded[group.id] = true;
                defaultChildGroups[group.id] = group.location_context_groups;
            });
            setExpandedGroups(defaultExpanded);
            setChildContextGroups(defaultChildGroups);
        } catch (error) {
            console.error("Error fetching context filters:", error);
            setError("Failed to load context filters");
        } finally {
            setLoading(false);
        }
    };

    const createContextFilter = async (newFilter) => {
        try {
            const response = await axios.post(contextLayerFilterAPI, newFilter, {
                headers: {
                    'X-CSRFToken': props.csrfToken,
                    'Content-Type': 'application/json'
                }
            });
            console.log("New filter created successfully:", response.data.filter);

            setIsAddNewFilterModalOpen(false);

            setContextFilters([]);
            fetchContextFilters();
        } catch (error) {
            console.error("Failed to create new filter:", error);
        } finally {
            setSavingNewFilter(false);
        }
    };

    useEffect(() => {
        fetchContextFilters();
    }, []);

    const toggleGroup = (groupId) => {
        setExpandedGroups(prevState => ({
            ...prevState,
            [groupId]: !prevState[groupId]
        }));
    };

    const onSortParent = (oldIndex, newIndex) => {
        const updatedFilters = arrayMoveImmutable(contextFilters, oldIndex, newIndex).map((filter, index) => ({
            id: filter.id,
            display_order: index + 1
        }));

        updateOrder(updatedFilters, {})
        setContextFilters(arrayMoveImmutable(contextFilters, oldIndex, newIndex))
    };

    const onSortChild = (parentId, oldIndex, newIndex) => {
        const updatedGroups = {
            [parentId]: arrayMoveImmutable(childContextGroups[parentId], oldIndex, newIndex).map((group, index) => ({
                id: group.group.id,
                group_display_order: index + 1
            }))
        };
        updateOrder(contextFilters, updatedGroups);
        setChildContextGroups(prevState => ({
            ...prevState,
            [parentId]: arrayMoveImmutable(prevState[parentId], oldIndex, newIndex)
        }));
    };

    const handleFilterChange = (e) => {
        setFilterText(e.target.value);
    };

    const handleSaveAddNewFilter = () => {
        const newFilter = {
            display_order: contextFilters.length + 1,
            location_context_groups: [],
            title: newFilterName
        }
        setSavingNewFilter(true);
        createContextFilter(newFilter);
    }

    const filteredContextFilters = contextFilters.filter(group =>
        group.title.toLowerCase().includes(filterText.toLowerCase())
    );

    const toggleAddNewGropModal = () => {
        setIsAddNewGroupModalOpen(!isAddNewGroupModalOpen)
    }

    const toggleAddNewFilterModal = () => {
        if (!isAddNewFilterModalOpen) {
            setNewFilterName('');
        }
        setIsAddNewFilterModalOpen(!isAddNewFilterModalOpen)
    }

    const toggleGeocontextListModal = () => {
        setIsGeocontextListOpen(!isGeocontextListOpen);
    }

    const handleAddNewGroup = (e, contextFilter) => {
         e.stopPropagation();
         toggleAddNewGropModal();
         if (contextGroups.length === 0) {
             fetchContextGroups();
         }
         setSelectedFilter(contextFilter);
    }

    const handleDeleteFilter = (e, contextFilter) => {
        e.stopPropagation();
        const isConfirmed = window.confirm(`Are you sure you want to delete "${contextFilter.title}"?`);
        if (isConfirmed) {
            deleteContextFilter(contextFilter.id);
        }
    }

    const handleRemoveGroup = (filter, group) => {
        const isConfirmed = window.confirm(`Are you sure you want to delete "${group.group.name}"?`);
        if (!isConfirmed) {
            return;
        }
        let groupId = group.group.id;
        const updatedGroups = {
            [filter.id]: filter.location_context_groups.map((group, index) => ({
                id: group.group.id,
                group_display_order: index + 1,
                remove: group.group.id === groupId
            }))
        };
        updateOrder({}, updatedGroups, true);
    }

    if (loading) {
        return <div>Loading...</div>;
    }

    if (error) {
        return <div>{error}</div>;
    }

    return (
        <div>
            <div className="filter-input">
                <input
                    type="text"
                    placeholder="Filter by name"
                    value={filterText}
                    onChange={handleFilterChange}
                    className="form-control mb-2"
                />
            </div>
            <div style={{ width: '100%' }}>
                <Button color={'success'} size={'sm'} style={{ marginBottom: 5 }} onClick={toggleAddNewFilterModal}>
                    <i className="bi bi-plus"></i> Add new filter section
                </Button>
                <Button color='warning' size={'sm'} style={{ marginBottom: 5, float: 'right' }} onClick={toggleGeocontextListModal}>
                    <i className="bi bi-list"></i> GeoContext keys
                </Button>
            </div>
            <div className="row">
                <SortableList onSortEnd={onSortParent} className='context-filter-list col-md-12' draggedItemClassName={'dragged'}>
                    {filteredContextFilters.map((contextFilter) => (
                        <SortableItem className="col-md-12" key={contextFilter.id}>
                            <div className="item">
                                <div
                                    onClick={() => toggleGroup(contextFilter.id)}
                                    className="context-filter-header"
                                >
                                    <SortableKnob>
                                        <span><i className="bi bi-grip-vertical"></i></span>
                                    </SortableKnob>
                                    {contextFilter.title}
                                    <Button color={'success'} size={'sm'}
                                            outline
                                            onClick={(e) => handleAddNewGroup(e, contextFilter)}
                                            style={{ float: 'right', right: 0, marginTop: -5 }}>
                                        <i className="bi bi-plus"></i>
                                    </Button>
                                    <Button color={'danger'} size={'sm'}
                                            outline
                                            onClick={(e) => handleDeleteFilter(e, contextFilter)}
                                            style={{float: 'right', right: 0, marginTop: -5, marginRight: 5}}>
                                        <i className="bi bi-trash"></i>
                                    </Button>
                                </div>
                                {expandedGroups[contextFilter.id] && (
                                    <SortableList onSortEnd={( oldIndex, newIndex ) => onSortChild(contextFilter.id, oldIndex, newIndex)} draggedItemClassName={'dragged'}>
                                        <div className="context-group-box">
                                            {childContextGroups[contextFilter.id]?.map((contextGroup) => (
                                                <SortableItem key={contextGroup.id}>
                                                    <div key={contextGroup.id}
                                                         className="context-group-item"
                                                    >
                                                        <div>
                                                            <SortableKnob>
                                                                <span><i className="bi bi-grip-vertical"></i></span>
                                                            </SortableKnob>
                                                            {contextGroup.group.name}
                                                            <Button color={'danger'} size={'sm'}
                                                                    style={{float: 'right', right: 0, marginTop: -5}}
                                                                    onClick={(e) => handleRemoveGroup(contextFilter, contextGroup)}
                                                            >
                                                                <i className="bi bi-trash"></i>
                                                            </Button>
                                                        </div>
                                                    </div>
                                                </SortableItem>
                                            ))}
                                        </div>
                                    </SortableList>
                                )}
                            </div>
                        </SortableItem>
                    ))}
                </SortableList>
            </div>

            <AddContextGroup isOpen={isAddNewGroupModalOpen} selectedFilter={selectedFilter} toggle={toggleAddNewGropModal} updateOrder={updateOrder}/>
            <Modal isOpen={isAddNewFilterModalOpen} toggle={toggleAddNewFilterModal}>
                <ModalHeader toggle={toggleAddNewFilterModal}>
                    Add new filter section
                </ModalHeader>
                <ModalBody>
                    <Form>
                        <FormGroup>
                            <Label for="filterName">
                                Filter section name
                            </Label>
                            <Input value={newFilterName} onChange={e => setNewFilterName(e.target.value)}/>
                        </FormGroup>
                    </Form>
                </ModalBody>
                <ModalFooter>
                <Button color="secondary" onClick={toggleAddNewFilterModal} disabled={savingNewFilter}>
                    Close
                </Button>
                <Button color="primary" onClick={handleSaveAddNewFilter} disabled={!newFilterName || savingNewFilter}>
                    {savingNewFilter ? 'Saving...' : 'Save'}
                </Button>
            </ModalFooter>
            </Modal>

            <GeocontextListModal toggle={toggleGeocontextListModal} isOpen={isGeocontextListOpen} csrfToken={props.csrfToken} geocontextUrl={props.geocontextUrl}/>
        </div>
    );
}

export default ContextFilterView;
