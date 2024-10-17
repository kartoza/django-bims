import React, { useState, useEffect, useRef } from 'react';
import {
    Button, Form, FormGroup, Input, Label, Modal, ModalBody, ModalFooter, ModalHeader} from "reactstrap";
import axios from "axios";


export const AutocompleteInput = ({ groupValues, updateValue, url }) => {
    const [autocompleteResults, setAutocompleteResults] = useState([]);
    const [inputValue, setInputValue] = useState('')
    const inputRef = useRef(null);

    useEffect(() => {
        setInputValue(groupValues.native_layer_name)
    }, [groupValues.native_layer_name])

    const handleAutocompleteInputChange = async (e) => {
        const query = e.target.value;
        setInputValue(query)
        if (query.length > 2) {
            try {
                const response = await axios.get(`${url}?q=${query}`);
                setAutocompleteResults(response.data);
            } catch (error) {
                console.error("Error fetching autocomplete results:", error);
            }
        } else {
            setAutocompleteResults([]);
        }
    };

    const handleInputSelect = () => {
        if (inputRef.current) {
            inputRef.current.focus();
            inputRef.current.select();
        }
    }

    const handleAutocompleteSelect = (layer) => {
        updateValue(layer.unique_id, 'key');
        updateValue(layer.unique_id, 'geocontext_group_key');
        updateValue(layer.name, 'native_layer_name')
        setInputValue(layer.name)

        setAutocompleteResults([]);
    };

    return (
        <div style={{ position: 'relative' }}>
            <Input
                type="text"
                id="groupKey"
                value={inputValue}
                onChange={handleAutocompleteInputChange}
                onClick={handleInputSelect}
                placeholder="Start typing to search..."
                innerRef={inputRef}
            />
            {autocompleteResults.length > 0 && (
                <ul className="autocomplete-results">
                    {autocompleteResults.map((layer) => (
                        <li
                            key={layer.id}
                            onClick={() => handleAutocompleteSelect(layer)}
                            className="autocomplete-item"
                        >
                            {layer.name}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
};


export const ContextGroupDetailModal = ({ show, handleClose, group, handleSave }) => {
    const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
    const [groupValues, setGroupValues] = useState({
        id: '',
        layer_name: '',
        native_layer_name: '',
        name: '',
        key: '',
        active: false,
        wms_url: '',
        layer_identifier: '',
        geocontext_group_key: ''
    });

    useEffect(() => {
        if (group) {
            setGroupValues({
                id: group.id,
                layer_name: group.layer_name ? group.layer_name : '',
                native_layer_name: group.native_layer_name,
                name: group.name,
                key: group.key,
                active: group.active,
                wms_url: group.wms_url,
                layer_identifier: group.layer_identifier,
                geocontext_group_key: group.geocontext_group_key
            })
        }
    }, [group])

    const updateValue = (value, groupKey) => {
        setGroupValues((prevGroupValues) => ({
          ...prevGroupValues,
          [groupKey]: value,
        }));
        setHasUnsavedChanges(true);
    }

    const toggleActiveStatus = () => {
        updateValue(!groupValues.active, 'active');
    }

    if (!group) {
        return null;
    }

    return (
        <Modal isOpen={show} toggle={handleClose}>
            <ModalHeader toggle={handleClose}>{group.name}</ModalHeader>
            <ModalBody>
                <Form>
                    <FormGroup>
                        <Label for="groupKey">Name</Label>
                        <Input
                            type="text"
                            id="groupKey"
                            value={groupValues.name}
                            onChange={(e) => updateValue(e.target.value, 'name')}
                        />
                    </FormGroup>
                     {
                        !group.is_native_layer && (
                            <FormGroup>
                                <Label for="groupKey">GeoContext Group Key</Label>
                                <Input
                                    type="text"
                                    id="groupKey"
                                    value={groupValues.geocontext_group_key}
                                    onChange={(e) => updateValue(e.target.value, 'geocontext_group_key')}
                                />
                            </FormGroup>
                        )
                     }

                    <FormGroup>
                        <Label for="groupKey">{group.is_native_layer ? 'Layer':'Service Key'}</Label>
                        {group.is_native_layer ? (
                            <AutocompleteInput
                                groupValues={groupValues}
                                updateValue={updateValue}
                                url={'/api/cloud-native-layer-autocomplete/'}/>
                        ) : (
                            <Input
                                type="text"
                                id="groupKey"
                                value={groupValues.key}
                                onChange={(e) => updateValue(e.target.value, 'key')}
                            />
                        )}
                    </FormGroup>

                    <FormGroup>
                        <Label for="groupStatus">Status</Label>
                        <div className="custom-control custom-switch">
                            <Input
                                type="checkbox"
                                className="custom-control-input"
                                id="groupStatus"
                                checked={groupValues.active}
                                onChange={toggleActiveStatus}
                            />
                            <Label className="custom-control-label" htmlFor="groupStatus">
                                {groupValues.active ? 'Active' : 'Inactive'}
                            </Label>
                        </div>
                    </FormGroup>
                    {
                        !group.is_native_layer && (
                            <>
                            <FormGroup>
                                <Label for="layerName">Layer Name</Label>
                                <Input
                                    type="text"
                                    id="layerName"
                                    value={groupValues.layer_name}
                                    onChange={(e) => updateValue(e.target.value, 'layer_name')}
                                />
                            </FormGroup>
                            <FormGroup>
                                <Label for="wmsUrl">WMS URL</Label>
                                <Input
                                    type="text"
                                    id="wmsUrl"
                                    value={groupValues.wms_url}
                                    onChange={(e) => updateValue(e.target.value, 'wms_url')}
                                />
                            </FormGroup>
                            </>
                        )
                    }
                    <FormGroup>
                        <Label for="attribute">Attribute</Label>
                        <Input
                            type="text"
                            id="attribute"
                            value={groupValues.layer_identifier}
                            onChange={(e) => updateValue(e.target.value, 'layer_identifier')}
                        />
                    </FormGroup>
                </Form>
            </ModalBody>
            <ModalFooter>
                <Button color="secondary" onClick={handleClose}>
                    Close
                </Button>
                <Button color="primary" onClick={() => handleSave(groupValues)} disabled={!hasUnsavedChanges}>
                    Save
                </Button>
            </ModalFooter>
        </Modal>
    );
};