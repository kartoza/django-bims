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


