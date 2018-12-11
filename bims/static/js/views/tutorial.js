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
                intro: "This is a tooltip.",

              },
              {
                element: "#filter-control",
                intro: "Ok, wasn't that fun?",
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