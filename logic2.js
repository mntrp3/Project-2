//Setting variables for the two API endpoint calls:
var weatherURL = "static/test_data.json"

//This function calls the URLs above and renders the map using the code below:
renderMap(weatherURL);

function renderMap(weatherURL) {
//There are two seperate URL calls that pass the data into variables and send the Data
//into the createFeatures function
    d3.json(weatherURL, function(data) {
        console.log(weatherURL)
        var weatherData = data;

            createFeatures(weatherData);
        });
    });

    //The functions below run as part of the createFeatures function
    function createFeatures(weatherData) {

        // Creates markers for each earthquake and adds a popup with magnitude, place, & time
        function forEachweatherLayer(feature, layer) {
            return new L.circleMarker([, feature.geometry.coordinates[0]], {
                fillOpacity: 1,
                color: "black",
                weight: 0.75,
                fillColor: "blue",
                radius:  markerSize()
            });
        }
        function forEachEarthquake(feature, layer) {
            layer.bindPopup("<h3>Temperature: " + feature.properties.mag + "</h3><hr><h4>Place: " + feature.properties.place + "</h4><hr><p>" + new Date(feature.properties.time) + "</p>");
        };

        // For each feature, a tectonic plate is mapped via polyline
        function forEachPlate(feature, layer) {
            L.polyline(feature.geometry.coordinates);
        };

        // Converts the earthquake data array to geoJSON
        var quakes = L.geoJSON(earthquakeData, {
            onEachFeature: forEachEarthquake,
            pointToLayer: forEachPlate
        });

        // Creates a Timeline layer from features of earthquake data array and pulls in
        //time data for the timeline.

        var timelineLayer = L.timeline(earthquakeData, {
            getInterval: function(feature) {
                return {
                    start: feature.properties.time,
                    end: feature.properties.time + feature.properties.mag * 10000000
                };
            },
            pointToLayer: forEachQuakeLayer,
            onEachFeature: forEachEarthquake
        });

        // All three layers are now sent to be mapped
        createMap(quakes, plates, timelineLayer);
    };

    // Function to create map
    function createMap(quakes, plates, timelineLayer) {
      // Create variables to store our map tile layers: light, dark, and outdoors
      // Outdoors layer
      var light = L.tileLayer("https://api.mapbox.com/styles/v1/mapbox/light-v9/tiles/256/{z}/{x}/{y}?" +
          "access_token=pk.eyJ1IjoiYm9nb3Jkb244NiIsImEiOiJjamViam45ZWIwZ3NhMnhsYWV2MXJscXBiIn0." +
          "vkP7IgE8o4eX6nIZeVtV0Q");
      // Satellite layer
      var dark = L.tileLayer("https://api.mapbox.com/styles/v1/mapbox/dark-v9/tiles/256/{z}/{x}/{y}?" +
      "access_token=pk.eyJ1IjoiYm9nb3Jkb244NiIsImEiOiJjamViam45ZWIwZ3NhMnhsYWV2MXJscXBiIn0." +
      "vkP7IgE8o4eX6nIZeVtV0Q");
      // Darkmap layer
      var outdoors = L.tileLayer("https://api.mapbox.com/styles/v1/mapbox/outdoors-v10/tiles/256/{z}/{x}/{y}?" +
      "access_token=pk.eyJ1IjoiYm9nb3Jkb244NiIsImEiOiJjamViam45ZWIwZ3NhMnhsYWV2MXJscXBiIn0." +
      "vkP7IgE8o4eX6nIZeVtV0Q");

        // Define a baseMaps object so that we can switch between layers on map
        var baseMaps = {
            "Light": light,
            "Dark": dark,
            "Outdoors": outdoors,
        };

        // Create overlay object to enable turning earthquakes or Fault Lines off
        var overlayMaps = {
            "Earthquakes": quakes,
            "Fault Lines": plates
        };

        // Create map centered on USA and sets up initial layers on load
        var myMap = L.map("map", {
            center: [38.5, -98.0],
            zoom: 4,
            layers: [light, plates],
            scrollWheelZoom: false
        });

        // Create a layer control for baseMaps and overlayMaps
        L.control.layers(baseMaps, overlayMaps, {
            collapsed: true
        }).addTo(myMap);

        // Adds Legend
        var legend = L.control({position: 'bottomright'});
        legend.onAdd = function(myMap) {
            var div = L.DomUtil.create('div', 'info legend'),
                        grades = [0, 1, 2, 3, 4, 5],
                        labels = ["0-1", "1-2", "2-3", "3-4", "4-5", "5+"],
                        color_list = ['#ffffcc', '#c7e9b4', '#7fcdbb', '#41b6c4', '#2c7fb8', '#253494'];
            for (var i = 0; i < grades.length; i++) {
                div.innerHTML += '<i style="background:' + color_list[i] + '; color:' + color_list[i] +
                ';">....</i> ' + grades[i] + (grades[i + 1] ? '&ndash;' + grades[i + 1] + '<br>' : '+');
            }
            return div;
        };
        legend.addTo(myMap);

        // Adds timeline and timeline controls
        var timelineControl = L.timelineSliderControl({
            formatOutput: function(date) {
                return new Date(date).toString();
            }
        });
        timelineControl.addTo(myMap);
        timelineControl.addTimelines(timelineLayer);
        timelineLayer.addTo(myMap);
    };
}

// Pick colors based on magnitude

function pickColors(magnitude) {
  return magnitude >= 5 ? "#253494":
         magnitude >= 4 ? "#2c7fb8":
         magnitude >= 3 ? "#41b6c4":
         magnitude >= 2 ? "#7fcdbb":
         magnitude >= 1 ? "#c7e9b4":
                         "#ffffcc"; //Last one is the default
};

//Sets markers size by magnitude and increases it by 5 for better visibility on map
function markerSize(magnitude) {
    return magnitude * 5;
};
