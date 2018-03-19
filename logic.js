// Here we create a variable to store our url to mapbox to pull in the light map
var mapbox = "https://api.mapbox.com/styles/v1/mapbox/light-v9/tiles/256/{z}/{x}/{y}?access_token=pk.eyJ1IjoiYm9nb3Jkb244NiIsImEiOiJjamViam45ZWIwZ3NhMnhsYWV2MXJscXBiIn0.vkP7IgE8o4eX6nIZeVtV0Q";

// Creating map object
var myMap = L.map("map", {
  center: [38.91, -77.036],
  zoom: 11
});

// Adding tile layer to the map
L.tileLayer(mapbox).addTo(myMap);

//Read in CSV of data for plotting to map
// d3.csv("sevendaydata.csv", function(err, csvData) {
//   if (err) throw err;
//
//   csvData.forEach(function(data) {
//     data.latitude = +data.latitude;
//     data.longitude = +data.longitude;
//     data.temp = +data.temp;
//   });
