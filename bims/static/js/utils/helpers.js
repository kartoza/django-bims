// Helper function to get element by ID
function getById(id) {
    return document.getElementById(id);
}

// Helper function to add event listener to an element
function addEvent(element, eventType, callback) {
    element.addEventListener(eventType, callback);
}
