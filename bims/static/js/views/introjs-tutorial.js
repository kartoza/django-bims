function startIntro() {
    var intro = introJs();
    intro.setOptions({
        steps: [
            {
                intro: "Welcome! This is the BIMS Tutorial!",

            },
            {
                element: document.querySelector('#map-control-panel-element'),
                intro: "This is the map control panel! Handy little thing...",
            },
            {
                element: document.querySelector('#search-control'),
                intro: "In order to find the data you need use the" +
                    " SEARCH,",
            },
            {
                element: ".map-search-box.map-control-panel-box",
                intro: "with its many filters;",
                position: 'right',
            },
            {
                element: ".map-search-box.map-control-panel-box",
                intro: "such as this versatile DATE widget!",
                position: 'right',
            },
            {
                element: "#filter-control",
                intro: "Visualize your data clearly using the LAYER SELECTOR.",
                position: 'right',
            },
            {
                element: '.layer-switcher',
                intro: 'You can also easily change your BASEMAP,'
            },
            {
                element: '#locate-control',
                intro: 'or get straight to the point with the LOCATE tool.'
            },
            {
                element: "#download-control",
                intro: "We are not stingy with our data either. DOWNLOAD...",
                position: 'right'
            },
            {
                element: "#print-control",
                intro: "...or PRINT, exactly what you need, quickly!",
                position: 'right'
            },
            // {
            //   element: '#step3',
            //   intro: 'More features, more fun.',
            //   position: 'right'
            // },
            // {
            //   element: '#step4',
            //   intro: "Another step.",
            //   position: 'right'
            // },
            // {
            //   element: '#step5',
            //   intro: 'Get it, use it.'
            // }
        ]
    });
    intro.start().onbeforechange(function () {
        if (intro._currentStep == "3") {
            document.getElementById("search-control").click();
        }
        else if (intro._currentStep == "4") {
            document.getElementById("date-filter-subtitle").click();
        }
        else if (intro._currentStep == "5") {
            document.getElementById("date-filter-subtitle").click();
            document.getElementById("search-control").click();
        };
    });

}


function nextButtonClicked() {
    console.log('test');
}

// function createStepEvents(guideObject, eventList) {
//
//     //underscore loop used here, foreach would work just as well
//     _.each(eventList, function (event) {
//
//         //for the guid object's <event> attribute...
//         guideObject[event](function () {
//
//             //get its steps and current step value
//             var steps = this._options.steps,
//                 currentStep = this._currentStep;
//
//             //if it's a function, execute the specified <event> type
//             if (_.isFunction(steps[currentStep][event])) {
//                 steps[currentStep][event]();
//             }
//         });
//
//     }, this);
// }

//setup the events per step you care about for this guide
// createStepEvents(guide, ['onchange', 'onbeforechange']);


