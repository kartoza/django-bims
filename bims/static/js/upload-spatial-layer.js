export const uploadLayer = (() => {

    const layerNameElm = getById('layer-name')
    const submitBtn = getById('submit-btn')
    const fileInput = getById('spatial-layer-file')

    function handleRequiredFieldUpdated(e) {
        const file = fileInput.files[0];
        let isFileSizeValid = true;
        submitBtn.disabled = !layerNameElm.value || !fileInput.value || !isFileSizeValid;
    }

    function init() {
        addEvent(layerNameElm, 'input', handleRequiredFieldUpdated)
        addEvent(fileInput, 'input', handleRequiredFieldUpdated)
    }

    return {
        init,
    }
})()

addEvent(document, 'DOMContentLoaded', uploadLayer.init)
