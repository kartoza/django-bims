import {
    Button, Form, FormGroup, Input, Label, Modal, ModalBody, ModalFooter, ModalHeader} from "reactstrap";
import React, {useEffect, useState} from "react";


export const ContextGroupDetailModal = ({ show, handleClose, group, handleSave }) => {
    const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
    const [groupValues, setGroupValues] = useState({
        id: '',
        layer_name: '',
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
                        !group.is_native_layer || (
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
                        <Label for="groupKey">Service Key</Label>
                        <Input
                            type="text"
                            id="groupKey"
                            value={groupValues.key}
                            onChange={(e) => updateValue(e.target.value, 'key')}
                        />
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
                        !group.is_native_layer || (
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