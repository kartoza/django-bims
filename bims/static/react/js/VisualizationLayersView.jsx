import React, { useState, useEffect } from 'react';
import '../css/ContextLayers.scss';
import {createRoot} from "react-dom/client";
import VisualizationLayersList from "./components/VisualizationLayersList";


const VisualizationLayersView = (props) => {
    return (
        <VisualizationLayersList csrfToken={props.csrfToken}/>
    )
}

$(function () {
    $("[data-visualizationlayersview]").each(function () {
        let props = $(this).data();
        props.history = history;
        delete props.visualizationlayersview;
        const container = $(this).get(0);
        const root = createRoot(container);
        root.render(<VisualizationLayersView {...props} />);
    });
});
export default VisualizationLayersView;
