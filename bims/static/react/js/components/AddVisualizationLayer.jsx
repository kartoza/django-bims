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


const VisualizationLayerForm = (props) => {
    const [layerType, setLayerType] = useState('native_layer');
    const [name, setName] = useState('');
    const [wmsUrl, setWmsUrl] = useState('https://maps.kartoza.com/geoserver/wms');
    const [wmsLayerName, setWmsLayerName] = useState('');
    const [styles, setStyles] = useState([]);
    const [layers, setLayers] = useState([]);
    const [defaultStyle, setDefaultStyle] = useState(null);
    const [selectedLayer, setSelectedLayer] = useState(null);
    const inputRef = useRef(null);
    const layerInputRef = useRef(null);

    const [testResult, setTestResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false)
    const [abstract, setAbstract] = useState('');

    useEffect(() => {
        if (props.selectedLayer) {
            setLayerType(props.selectedLayer.native_layer ? 'native_layer' : 'wms');
            setName(props.selectedLayer.name)
            setWmsLayerName(props.selectedLayer.wms_layer_name)
            setAbstract(props.selectedLayer.native_layer_abstract)
            if (props.selectedLayer.native_layer) {
                handleSelectLayer(props.selectedLayer.native_layer, props.selectedLayer.native_style_id)
            }
        } else {
            setName('')
            setAbstract('')
            setWmsLayerName('')
        }
    }, [props.selectedLayer])

    useEffect(() => {
        if (layers.length === 0) {
            fetchLayers()
        }
    }, [layers]);

    const fetchLayers = async () => {
        try {
            const response = await axios.get('/api/layer/');
            if (response.data.results.length > 0) {
                setLayers(response.data.results);
                let firstLayer = response.data.results[0];
                setStyles(firstLayer.styles)
                if (firstLayer.default_style) {
                    setDefaultStyle(firstLayer.default_style.id);
                }
            }
        } catch (error) {
            console.error("Error fetching layers:", error);
        } finally {
        }
    };

    const handleAddLayer = async () => {
        setSaving(true)

        let layerData = {
            'name': name,
            'layer_type': layerType
        }

        if (layerType === 'wms') {
            layerData['wms_layer_name'] = wmsLayerName;
            layerData['wms_layer_url'] = wmsUrl;
        } else {
            let styleId = parseInt(inputRef.current.value);
            let layerId = parseInt(layerInputRef.current.value);
            layerData['style_id'] = styleId;
            layerData['layer_id'] = layerId;
        }
        layerData['abstract'] = abstract;
        try {
            const response = await axios.post('/api/visualization-layers/', layerData, {
                headers: {
                    'X-CSRFToken': props.csrfToken,
                    'Content-Type': 'application/json'
                }
            });
            console.log("New layer created successfully:", response.data.filter);
        } catch (error) {
            console.error("Failed to create new layer:", error);
        } finally {
            setSaving(false);
            setWmsLayerName('');
            setName('');
            props.toggle();
            props.onAdded();
        }
    };

    const handleSaveLayer = async () => {
        let layerData = props.selectedLayer;
        layerData['layer_type'] = layerType;
        layerData['name'] = name;
        if (layerType === 'wms') {
            layerData['wms_layer_name'] = wmsLayerName;
            layerData['wms_layer_url'] = wmsUrl;
            layerData['native_layer_style'] = null;
            layerData['native_layer'] = null;
        } else {
            let styleId = parseInt(inputRef.current.value);
            let layerId = parseInt(layerInputRef.current.value);
            layerData['native_layer_style'] = styleId;
            layerData['native_layer'] = layerId;
            layerData['wms_layer_url'] = '';
            layerData['wms_layer_name'] = name;
        }
        layerData['abstract'] = abstract;
        try {
            const response = await axios.put('/api/visualization-layers/', layerData, {
                headers: {
                    'X-CSRFToken': props.csrfToken,
                    'Content-Type': 'application/json'
                }
            });
            console.log("New layer created successfully:", response.data.filter);
        } catch (error) {
            console.error("Failed to create new layer:", error);
        } finally {
            setSaving(false);
            setWmsLayerName('');
            setName('');
            props.toggle();
            props.onAdded();
        }
    }


    const testWmsLayer = async () => {
        setLoading(true);
        setTestResult(null);
        const requestUrl = `${wmsUrl}?service=WMS&version=1.1.1&request=GetCapabilities`;
        try {
            const response = await axios.get(requestUrl);
            if (response.data.includes(wmsLayerName)) {
                setTestResult('success');
            } else {
                setTestResult('failure');
            }
        } catch (error) {
            setTestResult('error');
        } finally {
            setLoading(false);
        }
    };

    const handleSelectLayer = (layerId, defaultStyle=null) => {
        let layer = layers.find(({id}) => layerId === id);
        if (layer) {
            setStyles(layer.styles);
            setSelectedLayer(layer.id);
        }
        if (defaultStyle) {
            setDefaultStyle(defaultStyle);
        } else if (layer?.default_style) {
            setDefaultStyle(layer.default_style.id);
        }
    }


    return (
        <Modal isOpen={props.isOpen} toggle={props.toggle}>
            <ModalHeader>Visualization Layer Form</ModalHeader>
            <ModalBody>
                <ButtonGroup style={{marginBottom: 20}}>
                    <Button
                      color="primary"
                      outline
                      onClick={() => setLayerType('wms')}
                      active={layerType === 'wms'}
                    >
                      WMS
                    </Button>
                    <Button
                      color="primary"
                      outline
                      onClick={() => setLayerType('native_layer')}
                      active={layerType === 'native_layer'}
                    >
                      Native Layer
                    </Button>
                </ButtonGroup>
                <Form>
                    <FormGroup>
                        <Label for="name">
                            Name
                        </Label>
                        <Input value={name} onChange={(e) => setName(e.target.value)}/>
                    </FormGroup>
                    {layerType === 'wms' && (
                        <>
                            <FormGroup>
                                <Label for="wms_url">WMS Url</Label>
                                <Input value={wmsUrl} onChange={(e) => setWmsUrl(e.target.value)} />
                            </FormGroup>
                            <FormGroup>
                                <Label for="wms_layer_name">WMS Layer Name</Label>
                                <Input value={wmsLayerName} onChange={(e) => setWmsLayerName(e.target.value)} />
                            </FormGroup>
                            <Button
                                color="success"
                                disabled={!wmsLayerName || !wmsUrl || loading}
                                onClick={testWmsLayer}
                            >
                                {loading ? 'Testing...' : 'Test WMS Layer'}
                            </Button>
                            {testResult && (
                                <div style={{ marginTop: 10 }}>
                                    {testResult === 'success' && (
                                        <div style={{ color: 'green' }}>WMS Layer is valid!</div>
                                    )}
                                    {testResult === 'failure' && (
                                        <div style={{ color: 'red' }}>WMS Layer is not found.</div>
                                    )}
                                    {testResult === 'error' && (
                                        <div style={{ color: 'red' }}>An error occurred during the test.</div>
                                    )}
                                </div>
                            )}
                        </>
                    )}
                    {(layerType === 'native_layer') && (
                        <>
                             <FormGroup>
                                <Label for="layerSelect">Layer</Label>
                                <Input
                                  id="layerSelect"
                                  name="layerSelect"
                                  type="select"
                                  innerRef={layerInputRef}
                                  onChange={(e) => handleSelectLayer(parseInt(e.target.value))}
                                >
                                    {layers?.map(layer => (
                                        <option id={layer.id} value={layer.id} selected={selectedLayer && selectedLayer === layer.id}>
                                            {layer.name}
                                        </option>
                                    ))}
                                </Input>
                            </FormGroup>
                             <FormGroup>
                                <Label for="styleSelect">Style</Label>
                                <Input
                                  id="styleSelect"
                                  name="styleSelect"
                                  type="select"
                                  disabled={styles.length === 0}
                                  innerRef={inputRef}
                                >
                                    {styles?.map(style => (
                                        <option id={style.id} value={style.id} selected={defaultStyle && defaultStyle === style.id}>
                                            {style.name}
                                        </option>
                                    ))}
                                </Input>
                            </FormGroup>
                            <FormGroup>
                                <Label for="styleSelect">Abstract</Label>
                                <Input value={abstract} onChange={(e) => setAbstract(e.target.value)} type={'textarea'}/>
                            </FormGroup>
                        </>
                    )}
                </Form>

            </ModalBody>
            <ModalFooter>
                <Button color='primary' onClick={ props.selectedLayer ? handleSaveLayer : handleAddLayer } disabled={!name || (layerType === 'wms' ? (wmsUrl === '' || wmsLayerName === '') : false)}>
                    { props.selectedLayer ? 'Save' : 'Add' }
                </Button>
            </ModalFooter>
        </Modal>
    )
}

export default VisualizationLayerForm;
