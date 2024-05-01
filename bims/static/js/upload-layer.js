export const uploadLayer = (() => {

    const layerNameElm = getById('layer-name')
    const submitBtn = getById('submit-btn')
    const fileInput = getById('layer-file')
    const MAX_FILE_SIZE = 5242880;

    function handleRequiredFieldUpdated(e) {
        const file = fileInput.files[0];
        let isFileSizeValid = true;
        if (file && file.size > MAX_FILE_SIZE) {
            alert("File size must not exceed 5MB.");
            isFileSizeValid = false;
        }
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
