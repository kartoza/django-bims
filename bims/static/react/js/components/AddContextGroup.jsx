import {Button, FormGroup, Input, Label, Modal, ModalBody, ModalFooter, ModalHeader} from "reactstrap";
import React, {useEffect, useRef, useState} from "react";
import axios from "axios";


const AddContextGroup = (props) => {
    const [contextGroups, setContextGroups] = useState([]);
    const inputRef = useRef(null);

    const contextLayerGroupAPI = '/api/context-layer-group/';

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

    const handleAddNewContext = (e) => {
        let groupId = parseInt(inputRef.current.value);
        let filterId = props.selectedFilter.id;

        const updatedGroups = {
            [filterId]: props.selectedFilter.location_context_groups.map((group, index) => ({
                id: group.group.id,
                group_display_order: index + 1
            }))
        }
        updatedGroups[filterId].push({
            id: groupId,
            group_display_order: props.selectedFilter.location_context_groups.length + 1
        })
        props.updateOrder({}, updatedGroups, true);
        props.toggle();
    }

    useEffect(() => {
        if (props.isOpen) {
            if (contextGroups.length === 0) {
                fetchContextGroups();
            }
        }
    }, [props.isOpen])

    return (
        <Modal isOpen={props.isOpen} toggle={props.toggle} size={'lg'}>
            <ModalHeader toggle={props.toggle}>
                Add new context to {props.selectedFilter?.title}
            </ModalHeader>
            <ModalBody>
                <FormGroup>
                    <Label for="contextGroupSelect">
                      Context layer name
                    </Label>
                    <Input
                      id="contextGroupSelect"
                      name="select"
                      type="select"
                      innerRef={inputRef}
                    >

                        {contextGroups?.filter(contextGroup => {
                            for(let i = 0; i < props.selectedFilter?.location_context_groups.length; i++) {
                                if (props.selectedFilter.location_context_groups[i].group.id === contextGroup.id) {
                                    return false
                                }
                            }
                            return true;
                        }).map(contextGroup => (
                            <option id={contextGroup.id} value={contextGroup.id}>
                                {contextGroup.name}
                            </option>
                        ))}
                    </Input>
                  </FormGroup>
            </ModalBody>
            <ModalFooter>
                <Button color='primary' onClick={handleAddNewContext}>
                    Add
                </Button>
            </ModalFooter>
        </Modal>
    )
}

export default AddContextGroup;