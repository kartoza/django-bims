import React, { useState, useEffect } from 'react';
import axios from "axios";
import SortableList, {SortableItem, SortableKnob} from "react-easy-sort";
import { arrayMoveImmutable } from "array-move";
import "bootstrap-icons/font/bootstrap-icons.css";
import {Button, FormGroup, Input, Label, Modal, ModalBody, ModalFooter, ModalHeader} from "reactstrap";
import AddContextGroup from "./AddContextGroup";


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

        updateOrder(updatedFilters, childContextGroups)
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

    const filteredContextFilters = contextFilters.filter(group =>
        group.title.toLowerCase().includes(filterText.toLowerCase())
    );

    const toggleAddNewGropModal = () => {
        setIsAddNewGroupModalOpen(!isAddNewGroupModalOpen)
    }

    const handleAddNewGroup = (e, contextFilter) => {
         e.stopPropagation();
         toggleAddNewGropModal();
         if (contextGroups.length === 0) {
             fetchContextGroups();
         }
         setSelectedFilter(contextFilter);
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
                                </div>
                                {expandedGroups[contextFilter.id] && (
                                    <SortableList onSortEnd={( oldIndex, newIndex ) => onSortChild(contextFilter.id, oldIndex, newIndex)} draggedItemClassName={'dragged'}>
                                        <div className="context-group-box">
                                            {childContextGroups[contextFilter.id]?.map((contextGroup) => (
                                                <SortableItem key={contextGroup.id}>
                                                    <div key={contextGroup.id}
                                                         className="context-group-item"
                                                    >
                                                        <SortableKnob>
                                                            <span><i className="bi bi-grip-vertical"></i></span>
                                                        </SortableKnob>
                                                        {contextGroup.group.name}
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

        </div>
    );
}

export default ContextFilterView;
