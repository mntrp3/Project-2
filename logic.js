createMap();
var data = {};
//Read in CSV of data for plotting to map
d3.csv("sevendaydata_filtered.csv", function(error, data) {
  if (error) {
    console.log(error);
  } else {
    console.log("file load successful");
    for (var i = 1; i<data.length; i++) {
      var data = data[i];
      var lat = +data.latitude;
      var lon = +data.longitude;
      var temp = +data.temp;
      var date = data.day;
      var icon = data.icon;
      var weatherIcon = L.icon({
        iconUrl: icon,
        iconSize: [38, 95],
      });
      var marker = L.marker([lat, lon], {icon: weatherIcon})
      .bindPopup("<h3>Temperature  " + temp + "<h3>Date:  " + date + "</h3>")
      .addTo(myMap);

//    lat = +data.latitude;
  //  lon = +data.longitude;

//    L.geoJson(data).addTo(myMap);
  }
};
console.log(data[0]);

  // L.circleMarker([lat, lon], {
  //   fillOpacity: 1,
  //   color: "black",
  //   fillColor: "blue",
  //   radius: markerSize(temp)
  // }).bindPopup("<h3>Temperature  " + temp + "<h3>Date:  " + date + "</h3>")
  // .addTo(myMap);
});

function createMap() {
// Here we create a variable to store our url to mapbox to pull in the light map
      var light = L.tileLayer("https://api.mapbox.com/styles/v1/mapbox/light-v9/tiles/256/{z}/{x}/{y}?" +
      "access_token=pk.eyJ1IjoiYm9nb3Jkb244NiIsImEiOiJjamViam45ZWIwZ3NhMnhsYWV2MXJscXBiIn0.vkP7IgE8o4eX6nIZeVtV0Q");

      var dark = L.tileLayer("https://api.mapbox.com/styles/v1/mapbox/dark-v9/tiles/256/{z}/{x}/{y}?" +
      "access_token=pk.eyJ1IjoiYm9nb3Jkb244NiIsImEiOiJjamViam45ZWIwZ3NhMnhsYWV2MXJscXBiIn0.vkP7IgE8o4eX6nIZeVtV0Q");
// Darkmap layer
      var outdoors = L.tileLayer("https://api.mapbox.com/styles/v1/mapbox/outdoors-v10/tiles/256/{z}/{x}/{y}?" +
      "access_token=pk.eyJ1IjoiYm9nb3Jkb244NiIsImEiOiJjamViam45ZWIwZ3NhMnhsYWV2MXJscXBiIn0." +
      "vkP7IgE8o4eX6nIZeVtV0Q");

      var baseMaps = {
        "Light": light,
        "Dark": dark,
        "Outdoors": outdoors,
      };

// Creating map object
      var myMap = L.map("map", {
        center: [38.91, -77.036],
        zoom: 11,
        layers: outdoors
      });

      L.control.layers(baseMaps).addTo(myMap);
}
