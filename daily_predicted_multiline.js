//multiline graph

//actual hourly tempurature in Fahrenheit for the day
//forecasted 1 day in advance hourly temperature Farhenheit
//forecasted 3 days in advance hourly temperature Farhenheit

//columns : 

//actual TempF, Hour, 1 day forecasted tempF by hour, 3 day forecasted tempF by hour

// Step 0: Set up our chart
//= ================================
var svgWidth = 960;
var svgHeight = 500;

var margin = { top: 20, right: 40, bottom: 60, left: 50 };

var width = svgWidth - margin.left - margin.right;
var height = svgHeight - margin.top - margin.bottom;

// Create an SVG wrapper, append an SVG group that will hold our chart, and shift the latter by left and top margins.
var svg = d3
  .select("body")
  .append("svg")
  .attr("width", svgWidth)
  .attr("height", svgHeight)
  .append("g")
  .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

// Import data from the mojoData.csv file
d3.csv("mojoData.csv", function(error, mojoData) {
  if (error) throw error;

  // console.log(mojoData)
  // console.log([mojoData])
  // Create a function to parse hour 
  var parseTime = d3.timeParse("%-I:%M %p");

  // Format the data
  mojoData.forEach(function(data) {
    data.hour = parseTime(data.hour);
    data.today = +data.today;
    data.yesterdayPredict = +data.yesterdayPredict;
    data.threeDayPredict = +data.threeDayPredict;
  });

  // Set the ranges with scaling functions
  var xTimeScale = d3.scaleTime().range([0, width]);

  var yLinearScale = d3.scaleLinear().range([height, 0]);

  // Functions to create axes
  var bottomAxis = d3.axisBottom(xTimeScale);
  var leftAxis = d3.axisLeft(yLinearScale);

  // Step 1: Set up the x-axis and y-axis domains
  //= =============================================
  var todayMax = d3.max(mojoData, function(data) {
    return data.today;
  });
  var yesterdayPredictMax = d3.max(mojoData, function(data) {
    return data.yesterdayPredict;
  });
  var threeDayPredictMax = d3.max(mojoData, function(data) {
    return data.threeDayPredict;
  });

  //var yMax = todayMax > yesterdayPredictMax  ? todayMax : yesterdayPredictMax;
  var yMax = Math.max(todayMax,yesterdayPredictMax,threeDayPredictMax)
  console.log(yMax)
  // Scale the domain
  xTimeScale.domain(
    d3.extent(mojoData, function(data) {
      return data.hour;
    })
  );

  // Use the yMax value to set the yLinearScale domain
  yLinearScale.domain([0, yMax]);

  /* Comments:
1. var todayMax = d3.max(mojoData, function(data){return data.today});
    var yesterdayPredictMax = d3.max(mojoData, function(data){return data.today});
In order to set up our leftAxis domain, we need to obtain the largest value in each of today and yesterdayPredict columns.

2. var yMax = todayMax > yesterdayPredictMax ? todayMax : yesterdayPredictMax;
We then assign the larger of the two to the yMax variable.
The line is called a ternary operator and is a shorthand for the following if/else statement:
var yMax;
if (todayMax > yesterdayPredictMax){
  yMax = todayMax;
}
else {
  yMax = yesterdayPredictMax
}

3. yLinearAxis.domain([0, yMax]);
We set the y-axis domain to [0, yMax].
*/

  // Step 2: Set up two line generators and append two SVG paths
  //= =============================================
  // Line generators for each line
  var line1 = d3
    .line()
    .x(function(data) {
      return xTimeScale(data.hour);
    })
    .y(function(data) {
      return yLinearScale(data.threeDayPredict);
    });

  var line2 = d3
    .line()
    .x(function(data) {
      return xTimeScale(data.hour);
    })
    .y(function(data) {
      return yLinearScale(data.yesterdayPredict);
    });

   var line3 = d3
    .line()
    .x(function(data) {
      return xTimeScale(data.hour);
    })
    .y(function(data) {
      return yLinearScale(data.today);
    });

  // Append a path for line1
  svg
    .append("path")
    .data([mojoData])
    .attr("d", line1)
    .attr("class", "line green");

  // Append a path for line2
  svg
    .append("path")
    .data([mojoData])
    .attr("d", line2)
    .attr("class", "line orange");

  // Append a path for line3
  svg
    .append("path")
    .data([mojoData])
    .attr("d", line3)
    .attr("class", "line blue");

  // Add x-axis
  svg
    .append("g")
    .attr("class", "grid")
    .attr("transform", "translate(0, " + height + ")")
    .call(bottomAxis);


  // Add y-axis
  svg
    .append("g")
    .attr("class", "grid")
    .call(leftAxis);

  /* Comments:
1. svg.append('path')
    .data([mojoData])
Note the square brackets in .data([mojoData]).
Here, data() is the function that binds external data to onscreen SVG elements.
[data] is the data retrieved from the external CSV file.
Unlike in previous examples, however, data is wrapped in square brackets.
A fuller explanation is available below, but a brief summary is that, when working with more complex forms of data, we need to wrap the 'data' argument in brackets, e.g. .data([data]).

http://stackoverflow.com/questions/41310542/d3-data-binding-when-to-put-brackets-around-data

2. The only other notable difference here from the previous examples is that we now have two line generator functions, one for each line. We, of course, also append an SVG path for each line, where the line function is called.
*/
});
