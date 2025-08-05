import {
    Button,
    ButtonGroup,
    Form,
    FormGroup,
    Input,
    Label,
    Modal,
    ModalBody,
    ModalFooter,
    ModalHeader
} from "reactstrap";
import React, {useEffect, useRef, useState} from "react";
import axios from "axios";


const LayerGroupForm = (props) => {
    const [layerType, setLayerType] = useState('native_layer');
    const [name, setName] = useState('');
    const [wmsUrl, setWmsUrl] = useState('https://maps.kartoza.com/geoserver/wms');
    const [wmsLayerName, setWmsLayerName] = useState('');
    const inputRef = useRef(null);
    const layerInputRef = useRef(null);

    const [testResult, setTestResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false)
    const [description, setDescription] = useState('');

    useEffect(() => {
        if (props.selectedGroup) {
            setName(props.selectedGroup.name)
            setDescription(props.selectedGroup.description)
        } else {
            setName('')
            setDescription('')
        }
    }, [props.selectedGroup])

    const handleAddGroup = async () => {
        setSaving(true)
        let layerData = {
            'name': name,
            'description': description
        }
        try {
            const response = await axios.post('/api/layer-group/', layerData, {
                headers: {
                    'X-CSRFToken': props.csrfToken,
                    'Content-Type': 'application/json'
                }
            });
            console.log("New group created successfully:", response.data.filter);
        } catch (error) {
            console.error("Failed to create new group:", error);
        } finally {
            setSaving(false);
            setName('');
            props.toggle();
            props.onAdded();
        }
    };

    const handleSaveGroup = async () => {
        let layerData = props.selectedGroup;
        layerData['description'] = description;
        layerData['name'] = name;
        try {
            const response = await axios.put('/api/layer-group/', layerData, {
                headers: {
                    'X-CSRFToken': props.csrfToken,
                    'Content-Type': 'application/json'
                }
            });
            console.log("Group updated successfully:", response.data.filter);
        } catch (error) {
            console.error("Failed to update a grup:", error);
        } finally {
            setSaving(false);
            setName('');
            setDescription('');
            props.toggle();
            props.onAdded();
        }
    }

    return (
        <Modal isOpen={props.isOpen} toggle={props.toggle}>
            <ModalHeader>Layer Group Form</ModalHeader>
            <ModalBody>
                <Form>
                    <FormGroup>
                        <Label for="name">
                            Name
                        </Label>
                        <Input value={name} onChange={(e) => setName(e.target.value)}/>
                    </FormGroup>
                    <FormGroup>
                        <Label for="styleSelect">Description</Label>
                        <Input value={description} onChange={(e) => setDescription(e.target.value)} type={'textarea'}/>
                    </FormGroup>
                </Form>
            </ModalBody>
            <ModalFooter>
                <Button color='primary' onClick={props.selectedGroup ? handleSaveGroup : handleAddGroup} disabled={!name}>
                    {props.selectedGroup ? 'Save' : 'Add'}
                </Button>
            </ModalFooter>
        </Modal>
    )
}

export default LayerGroupForm;
