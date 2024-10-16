import React, { useState, useEffect } from 'react';
import '../css/ContextLayers.scss';
import {createRoot} from "react-dom/client";
import ContextGroupView from "./components/ContextGroupView";
import ContextFilterView from "./components/ContextFilterView";


const ContextLayersView = (props) => {
    return (
        <ContextFilterView csrfToken={props.csrfToken}/>
    )
}

$(function () {
    $("[data-contextlayersview]").each(function () {
        let props = $(this).data();
        props.history = history;
        delete props.contextlayersview;
        const container = $(this).get(0);
        const root = createRoot(container);
        root.render(<ContextLayersView {...props} />);
    });
});
export default ContextLayersView;
