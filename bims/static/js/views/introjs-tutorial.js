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
                element: "#filter-control",
                intro: "and the versatile FILTER.",
                position: 'right'
              },
                {
                    element: '.layer-switcher',
                    intro: 'Visualize your data clearly with our' +
                        ' LAYER-SELECTOR,'
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
                intro: "...or PRINT, exactly what you need, quickly.",
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
          intro.start();
}
