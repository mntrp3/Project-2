/**
 * Generates an array of random numbers between 0 and 9
 * @param {integer} n: length of array to generate
 */
function randomNumbersBetween0and9(n) {
  var randomNumberArray = [];
  for (var i = 0; i < n; i++) {
    randomNumberArray.push(Math.floor(Math.random() * 10));
  }
  return randomNumberArray;
}

// Create our first trace
var trace1 = {
  x: [1, 2, 3, 4, 5, 6, 7, 8],
  y: randomNumbersBetween0and9(8),
  name: "Max Temperature: Forecast",
  type: "scatter"
};

// Create our second trace
var trace2 = {
  x: [1, 2, 3, 4, 5, 6, 7, 8],
  y: randomNumbersBetween0and9(8),
  name: "Max Temperature: Actual",
  type: "scatter"
};

var trace3 = {
  x: [1, 2, 3, 4, 5, 6, 7, 8],
  y: randomNumbersBetween0and9(8),
  name: "Percent Accuracy of Forecast",
  type: "scatter"
};
// The data array consists of both traces
var data = [trace1, trace2, trace3];
var layout = {
  title: 'Forecast Vs. Actual Temp',
  xaxis: {
    title: 'Dates',
    titlefont: {
      family: 'Courier New, monospace',
      size: 18,
      color: '#7f7f7f'
    }
  },
  yaxis: {
    title: 'Temperature (F)',
    titlefont: {
      family: 'Courier New, monospace',
      size: 18,
      color: '#7f7f7f'
    }
  }
};
// Note that we omitted the layout object this time
// This will use default parameters for the layout
Plotly.newPlot("plot", data);
