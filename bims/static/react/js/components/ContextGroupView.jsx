import React, { useState, useEffect } from 'react';
import axios from "axios";
import {ContextGroupDetailModal} from "./ContextGroupDetailModal";
import {ContextGroupCard} from "./ContextGroupCard";
import {Button} from "reactstrap";


const ContextGroupView = (props) => {
    const [loading, setLoading] = useState(true)
    const [contextGroups, setContextGroups] = useState([])
    const [error, setError] = useState(null)
    const [selectedGroup, setSelectedGroup] = useState(null)
    const [showModal, setShowModal] = useState(false)
    const [filterText, setFilterText] = useState('')
    const [showOnlyActive, setShowOnlyActive] = useState(false)

    const contextLayerGroupAPI = '/api/context-layer-group'

    const fetchContextGroups = async () => {
        setContextGroups([])
        try {
            setLoading(true)
            const response = await axios.get(contextLayerGroupAPI);
            setContextGroups(response.data);
        } catch (error) {
            console.error("Error fetching context groups:", error);
            setError("Failed to load context groups");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchContextGroups();
    }, []);

    const handleCardClick = (group) => {
        setSelectedGroup(group);
        setShowModal(true);
    };

    const handleCloseModal = () => {
        setShowModal(false);
        setSelectedGroup(null);
    };

    const handleSaveGroup = async (groupData) => {
        setShowModal(false)
        let url = `/api/context-layer-group/${groupData.id}/`;

        const response = await fetch(url, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': props.csrfToken
            },
            body: JSON.stringify(groupData),
        });

        if (response.ok) {
            const data = await response.json();
            fetchContextGroups()
        } else {
          console.error('Error saving group:', response.statusText);
        }
    }

    const handleFilterChange = (e) => {
        setFilterText(e.target.value);
    };

    const handleShowOnlyActiveChange = (e) => {
        setShowOnlyActive(e.target.checked);
    };

    const filteredGroups = contextGroups.filter(group => {
        const matchesName = group.name.toLowerCase().includes(filterText.toLowerCase());
        const matchesActive = showOnlyActive ? group.active : true;
        return matchesName && matchesActive;
    });

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
            <div className="form-check mb-3">
                <input
                    type="checkbox"
                    className="form-check-input"
                    id="showOnlyActive"
                    checked={showOnlyActive}
                    onChange={handleShowOnlyActiveChange}
                />
                <label className="form-check-label" htmlFor="showOnlyActive">
                    Show only active
                </label>
                <div style={{ position: 'absolute', right: 0, marginTop: -27}}>
                    <Button color={'primary'}>Add new</Button>
                </div>
            </div>
            <div className="row">
                {filteredGroups.map((group) => (
                    <div className="col-md-12" key={group.id}>
                        <ContextGroupCard group={group} onClick={handleCardClick}/>
                    </div>
                ))}
            </div>
            <ContextGroupDetailModal
                show={showModal}
                handleClose={handleCloseModal}
                group={selectedGroup}
                handleSave={handleSaveGroup}
            />
        </div>
    )
}

export default ContextGroupView;
