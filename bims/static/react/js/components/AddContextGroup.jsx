import {Button, FormGroup, Input, Label, Modal, ModalBody, ModalFooter, ModalHeader} from "reactstrap";
import React, {useEffect, useRef, useState} from "react";
import axios from "axios";
import Select from "react-select";


const AddContextGroup = (props) => {
    const [contextGroups, setContextGroups] = useState([]);
    const [selectedGroup, setSelectedGroup] = useState(null);
    const contextLayerGroupAPI = '/api/context-layer-group/';

    const fetchContextGroups = async () => {
        setContextGroups([])
        try {
            const response = await axios.get(contextLayerGroupAPI);
            setContextGroups(response.data);
        } catch (error) {
            console.error("Error fetching context groups:", error);
        } finally {
        }
    };

    const handleAddNewContext = (e) => {
        let filterId = props.selectedFilter.id;

        const updatedGroups = {
            [filterId]: props.selectedFilter.location_context_groups.map((group, index) => ({
                id: group.group.id,
                group_display_order: index + 1
            }))
        }
        updatedGroups[filterId].push({
            id: selectedGroup.value,
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

    const onSelectContextGroup = (selectedOption) => {
        setSelectedGroup(selectedOption)
      };


    const contextOptions = contextGroups?.filter(contextGroup => {
          return !props.selectedFilter?.location_context_groups.some(
            group => group.group.id === contextGroup.id
          );
        })
        .map(contextGroup => ({
          value: contextGroup.id,
          label: (
            <>
              <div>{contextGroup.name}</div>
              <div style={{ fontSize: 'smaller', color: 'gray' }}>
                [{contextGroup.geocontext_group_key}]
              </div>
            </>
          ),
          name: contextGroup.name,
          geocontext_group_key: contextGroup.is_native_layer ? contextGroup.native_layer_name : contextGroup.geocontext_group_key,
        }));

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
                    <Select
                        id="contextGroupSelect"
                        options={contextOptions}
                        onChange={onSelectContextGroup}
                        placeholder="Search and select context group"
                        isSearchable
                        getOptionLabel={(option) => option.name}
                        formatOptionLabel={({ name, geocontext_group_key }) => (
                          <div>
                            <div>{name}</div>
                            <div style={{ fontSize: 'smaller', color: 'gray' }}>
                              {geocontext_group_key}
                            </div>
                          </div>
                        )}
                      />
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