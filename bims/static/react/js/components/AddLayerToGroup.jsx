import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
    Button,
    Form,
    FormGroup,
    Input,
    Label,
    Modal,
    ModalBody,
    ModalFooter,
    ModalHeader,
} from 'reactstrap';


const AddLayerToGroup = ({ isOpen, toggle, group, allLayers, csrfToken, onAdded }) => {
    const [selectedLayerId, setSelectedLayerId] = useState('');
    const [saving, setSaving] = useState(false);

    const existingLayerIds = new Set((group?.layers || []).map((l) => l.id));

    const availableLayers = allLayers.filter((l) => !existingLayerIds.has(l.id));

    useEffect(() => {
        if (isOpen) {
            setSelectedLayerId(availableLayers.length > 0 ? String(availableLayers[0].id) : '');
        }
    }, [isOpen, group]);

    const handleAdd = async () => {
        if (!selectedLayerId || !group) return;
        setSaving(true);
        try {
            await axios.put(
                '/api/layer-group/',
                { id: group.id, add_layer_id: parseInt(selectedLayerId) },
                {
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'Content-Type': 'application/json',
                    },
                }
            );
            toggle();
            onAdded();
        } catch (error) {
            console.error('Failed to add layer to group:', error);
        } finally {
            setSaving(false);
        }
    };

    return (
        <Modal isOpen={isOpen} toggle={toggle}>
            <ModalHeader toggle={toggle}>Add Layer to "{group?.name}"</ModalHeader>
            <ModalBody>
                {availableLayers.length === 0 ? (
                    <p>No layers available to add.</p>
                ) : (
                    <Form>
                        <FormGroup>
                            <Label for="layerSelect">Select Layer</Label>
                            <Input
                                id="layerSelect"
                                type="select"
                                value={selectedLayerId}
                                onChange={(e) => setSelectedLayerId(e.target.value)}
                            >
                                {availableLayers.map((layer) => (
                                    <option key={layer.id} value={layer.id}>
                                        {layer.name}
                                    </option>
                                ))}
                            </Input>
                        </FormGroup>
                    </Form>
                )}
            </ModalBody>
            <ModalFooter>
                <Button
                    color="primary"
                    onClick={handleAdd}
                    disabled={!selectedLayerId || saving || availableLayers.length === 0}
                >
                    {saving ? 'Adding...' : 'Add'}
                </Button>
            </ModalFooter>
        </Modal>
    );
};

export default AddLayerToGroup;
