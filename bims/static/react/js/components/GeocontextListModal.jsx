import React, { useState, useEffect } from 'react';
import {
    Alert,
    Badge,
    Button,
    Card,
    CardText,
    Form,
    FormGroup,
    Input,
    Label,
    Modal,
    ModalBody,
    ModalFooter,
    ModalHeader,
} from "reactstrap";
import axios from "axios";


const GeocontextListModal = (props) => {
    const [contextData, setContextData] = useState([])
    const [loading, setLoading] = useState(false);

    const [isAddKeyModalOpen, setIsAddKeyModalOpen] = useState(false);
    const [newGeocontextKey, setNewGeocontextKey] = useState('');

    const [addNewError, setAddNewError] = useState('')

    const apiUrl = '/api/context-layer-keys/';

    const fetchContextList = async () => {
        setContextData([]);
        try {
            setLoading(true);
            const response = await axios.get(apiUrl);
            setContextData(response.data);
        } catch (error) {
            console.error("Error fetching context data:", error);
        } finally {
            setLoading(false);
        }
    }

    const deleteContextKey = async (key) => {
        try {
            const deleteUrl = `${apiUrl}?key=${key}`;
            await axios.delete(deleteUrl, {
                headers: {
                    'X-CSRFToken': props.csrfToken
                }
            });
            console.log(`Key ${key} deleted successfully.`);
            fetchContextList();
        } catch (error) {
            console.error(`Failed to delete ${key}:`, error);
        }
    };

    const addNewContextKey = async (newKey) => {
        try {
            await axios.post(apiUrl, {
                    'key': newKey
                },
                {
                    headers: {
                        'X-CSRFToken': props.csrfToken
                    }
                }
            );
            setIsAddKeyModalOpen(false)
            fetchContextList();
        } catch (error) {
            console.error(`Failed to add ${newKey}:`, error?.response ? error.response : error);
            if (error.response?.data) {
                setAddNewError(error.response.data.message)
            }
        }
    };

    const handleDeleteContextKey = (e, context) => {
        const isConfirmed = window.confirm(`Are you sure you want to delete "${context.name ? context.name : context.key}"?`);
        if (isConfirmed) {
            deleteContextKey(context.key)
        }
    }
    const handleOpenGeocontext = (e, context) => {
        const url = `${props.geocontextUrl}api/v2/query?registry=group&key=${context.key}&x=0&y=0&outformat=json`
        window.open(url, '_blank');
    }

    const toggleAddKeyModal = () => {
        if (!isAddKeyModalOpen) {
            setNewGeocontextKey('')
            setAddNewError('')
        }
        setIsAddKeyModalOpen(!isAddKeyModalOpen)
    }

    useEffect(() => {
        if (contextData.length === 0) {
            fetchContextList();
        }
    }, [props.isOpen]);

    return (
        <>
            <Modal isOpen={props.isOpen} toggle={props.toggle}>
                <ModalHeader toggle={props.toggle}>
                    GeoContext Keys
                </ModalHeader>
                <ModalBody style={{ maxHeight: '75vh', overflowY: 'auto' }}>
                    {
                        loading && <div>Loading...</div>
                    }
                    {contextData.map(context => (
                         <Card
                            body
                            className="my-2 pt-2 pb-2"
                            style={{
                              width: '100%'
                            }}
                         >
                             <CardText className={'d-flex flex-row'}>
                                 <div>
                                     {
                                         context.name ? context.name : context.key
                                     }
                                     { context.type === 'native_layer' && ` (${context.attribute_used})` }
                                     <br/>
                                     <Badge color={'info'}>
                                         {context.type}
                                     </Badge>
                                 </div>
                                 <div className={'d-flex align-items-center'} style={{marginLeft: 'auto'}}>

                                     { context.type === 'geocontext' && (
                                         <Button size={'sm'} color={'info'} className={'mr-1'} onClick={(e) => handleOpenGeocontext(e, context)}>
                                             <i className="bi bi-send"></i>
                                         </Button>
                                     )}
                                     <Button size={'sm'} color={'danger'} onClick={(e) => handleDeleteContextKey(e, context)}>
                                         <i className="bi bi-trash"></i>
                                     </Button>
                                 </div>
                            </CardText>
                         </Card>
                    ))}
                    <div>

                    </div>
                </ModalBody>
                <ModalFooter>
                    <Button color={'success'} style={{ position: 'absolute', left: 0, marginLeft: '15px'}} size={'sm'} onClick={toggleAddKeyModal}>Add New Key</Button>
                    <Button color="secondary" onClick={props.toggle}>
                        Close
                    </Button>
            </ModalFooter>
            </Modal>

            <Modal isOpen={isAddKeyModalOpen} toggle={toggleAddKeyModal}>
                <ModalHeader toggle={toggleAddKeyModal}>
                    Add new key
                </ModalHeader>
                <ModalBody>
                    {addNewError && <Alert color="danger">
                            {addNewError}
                        </Alert>
                    }
                    <FormGroup>
                        <Label for={'geocontextKey'}>
                            Key
                        </Label>
                        <Input id={'geocontextKey'} value={newGeocontextKey} onChange={(e) => setNewGeocontextKey(e.target.value)}></Input>
                    </FormGroup>
                </ModalBody>
                <ModalFooter>
                    <Button color="primary" onClick={(e) => {
                        addNewContextKey(newGeocontextKey)
                    }} disabled={!newGeocontextKey}>
                        Save
                    </Button>
                </ModalFooter>
            </Modal>
        </>
    )
}

export default GeocontextListModal;