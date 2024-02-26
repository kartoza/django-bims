export const uploadLayer = (() => {

    const layerNameElm = getById('layer-name')
    const submitBtn = getById('submit-btn')
    const fileInput = getById('layer-file')

    function handleRequiredFieldUpdated(e) {
        submitBtn.disabled = !layerNameElm.value || !fileInput.value
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
