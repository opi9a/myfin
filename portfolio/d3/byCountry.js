
function initByCountry() {
// Initializes the country chart
    // todo make update function take no parameters
    // - instead, directly set the chart object's chartData,
    //   dataSource and mode first, before calling update

    byCountry = {
        svgHeight: 180,
        svgWidth: 465,
        margin: {"top": 35, "bottom": 20, "left": 45, "right":5},

        totalAmt: 1,
        dataSource: 'none yet',
        currentMode: 'none',
        setData: setCountryData,
        update: updateCountryChart,

        chartData: {
            byAmt: [],
            byPercent: [],
        },

        mouseData: {
            byAmt: [],
            byPercent: [],
        },
    };

    byCountry.chartWidth = byCountry.svgWidth
        - (byCountry.margin.left + byCountry.margin.right);
    byCountry.chartHeight = byCountry.svgHeight
        - (byCountry.margin.top + byCountry.margin.bottom);


    // svg, scales, empty axes and button
    byCountry['svg'] = d3.select("#chart1").append("svg")
              .attr("width", byCountry.svgWidth)
              .attr("height", byCountry.svgHeight)

    byCountry['yScale'] = d3.scaleLinear()
                .domain([0, 100])
                .range([byCountry.svgHeight - byCountry.margin.bottom,
                        byCountry.margin.top])

    byCountry['xScale'] = d3.scaleBand()
                .range([0, byCountry.chartWidth])
                .align(0)
                .padding(0.05)

    byCountry['yAxis'] = d3.axisLeft().scale(byCountry.yScale)
                .ticks(6)
                .tickSizeOuter(0)

    byCountry['xAxis'] = d3.axisBottom().scale(byCountry.xScale)
                .tickSize(0)

    byCountry.svg.append('g')
        .attr('class', 'xAxis')
        .attr('transform', 'translate(' + (byCountry.margin.left) + ', '
                                        + (byCountry.chartHeight
                                            + byCountry.margin.top) + ')')
        .call(byCountry.xAxis)
            .selectAll('text')
            .attr('transform', 'translate(0, 5)')

    byCountry.svg.append('g')
        .attr('class', 'yAxis')
        .attr('transform', 'translate(' + (byCountry.margin.left - 1) + ', 0)')
        .call(byCountry.yAxis);

    byCountry.svg.append('text')
        .attr("class", "chart-title")
        .attr("transform", "translate(43, 20)")
        .text("Countries");

    return byCountry;
};

function setCountryData(newData, dataSource, maxColumns=12) {
    this.coreData = newData;
    this.dataSource = dataSource;

    // create chartData byAmt and byPercent
    var orderedData = orderCountries(newData, maxColumns);
    console.log('orderedData in set country', orderedData);
    this.totalAmt = sumObj(sumAssetsAcrossArea(orderedData)) / 2; // div 2 as countrySums in there
    this.chartData.byAmt = flatten(orderedData, 'country');
    this.chartData.byPercent = getPercents(this.chartData.byAmt);

    // create mouseData byAmt and byPercent
    this.mouseData.byAmt = orderedData;

    x = {};
    for (country in orderedData) {
        if (!Object.keys(x).includes(country)) {
            x[[country]] = {};
        };

        for (elem in orderedData[country]) {
            x[country][elem] = 100 * orderedData[country][elem] 
                        /  this.totalAmt;
        };
    };

    this.mouseData.byPercent = x;

};

// main function for drawing and redrawing chart
function updateCountryChart(mode) {

    var svgWidth = this.svgWidth;
    var svgHeight = this.svgHeight;
    var margin = this.margin;
    var svg = this.svg;
    var xScale = this.xScale;
    var yScale = this.yScale;
    var xAxis = this.xAxis;
    var yAxis = this.yAxis;

    this.currentMode = mode;
    var chartData = this.chartData[mode];

    console.log('country chartData', chartData);
    console.log('mode in update country', mode);

    // make object of data by country, for mouseover on rects
    var mouseData = this.mouseData;

    // update title
    var title = svg.selectAll("text.data-source")
                    .data([this.dataSource], d => d);

    title.enter()
        .text("")
        .append("text")
        .attr("class", "chart-title data-source")
        .attr("transform", "translate(150, 20)")
        .attr("fill", "black")
        .attr("fill-opacity", 0)
        .text(this.dataSource)
        .transition("country title in")
        .delay(dur / 2)
        .duration(dur / 2)
        .attr("fill-opacity", 1)
    ;

    title.exit().transition("chart-title out").remove();


    // update scale domains
    xScale.domain(chartData.map(a => a.country));
    yScale.domain([0, d3.max(chartData, d => Number(d.end))]);
    
    // rebind data
    var bars = svg.selectAll("rect").data(chartData, d => (d.country
                                                         + d.type));
    
    // if there is an update selection, will still have old bar widths
    bars.transition('enterWidth') // need to name this or all breaks
        .duration(dur)
        .attr("width", xScale.bandwidth());
    
    // get enter bar selection - situate at right end, zero size
    newBars = bars.enter();

    newBars.append("rect")
            .attr("class", "bar")
            .attr("class", d => d.type)
            .each(function(d) { d3.select(this).classed(d.country, true) } )
            .attr("x", svgWidth)
            .attr("y", svgHeight - margin.bottom)
            .attr("width", xScale.bandwidth())
            .on("mouseover", function(d) {
                mode = byCountry.currentMode;
                console.log('mode in mouseover', mode);
                let boxSum = sumObj(mouseData[mode][d.country]);
                console.log('boxSum', boxSum);
                var boxH = yScale(0) - yScale(boxSum);
                svg.append("rect")
                      .attr("x", d3.select(this).attr("x") - 1)
                      .attr("width", d3.select(this).attr("width") + 2)
                      .attr("y", yScale(boxSum) - 1)
                      .attr("height", boxH + 2)
                      .attr("class", "tooltip")
                      .attr("fill", "none")
                      .attr("stroke", "black")
                      .attr("stroke-width", "0px")
                      .transition()
                      .duration(300)
                      .attr("stroke-width", "3px")
                var ttList = makeProfile(d.country, mouseData, mode);
                for (i in ttList) {
                    svg.append("text")
                      .attr("x", 0.5*svgWidth).attr("y", margin.top + 5 + i*10)
                      .attr("class", "tooltip")
                      .text(ttList[i]) 
                      .attr("fill-opacity", 0)
                      .transition()
                      .delay(200)
                      .duration(800)
                      .attr("fill-opacity", 1)
                };

               })
            .on("mouseout", function() {
                d3.selectAll('.tooltip')
                    .transition()
                    .duration(200)
                    .remove() } )

    // merge with update and transition all to new sizes
    .merge(bars)
    .transition().duration(dur)
          .style("fill", function(d, i) {
              if (Object.keys(colors).includes(d.country)) {
                  return colors[d.country];
              } else { return 'gray'; };
          })
              
          .attr("fill-opacity", function(d, i) {
              if (d['type'] == 'bond') { return 0.6; };
              if (d['type'] == 'stock') { return 0.8; };
              if (d['type'] == 'cash') { return 0.6; };
              return 1;
          })
          .attr("height", d => svgHeight
                                - yScale(d.end - d.start)
                                - margin.bottom)
          .attr("x", d => xScale(d.country) + margin.left)
          .attr("y", d => yScale(d.end))
          .attr("text", d => d.end - d.start) ;

    // exit old bars stage left, diminishing and going transparent
    bars.exit()
        .transition()
        .duration(dur)
        .attr("fill-opacity", 0)
        // .attr("y", margin.top)
        // .transition()
        // .attr("height", 0)
        // .attr("width", 0)
        .remove();

/* LABELS
    // make enter selection for labels, initiate on right
    labels = svg.selectAll('.barLabels')
                  .data(chartData, d => (d.country + d.type));

    labels.enter().append('text')
        .attr('class', 'barLabels')
        .attr("fill-opacity", 0)
        .attr("x", svgWidth)
        .attr("y", svgHeight - margin.bottom)

    // merge with update selection and transition all labels to right place
        .merge(labels)
        .transition().duration(dur)
          .attr("fill-opacity", 1)
          .attr("x", d => xScale(d.country)
                          + margin.left + (xScale.bandwidth() / 2))

          .attr("y", (d, i) => yScale(d.end) + 10)

          .text(function(d,i) {
            var rectVal = yScale(d.start) - yScale(d.end);
            if (rectVal > minBarH) { return f(d.end - d.start); };
          })

          // .style("font-size", "8px")
          .attr("font-family", "sans-serif")
          .attr("text-anchor", "middle")
          .attr("fill", "white")  ;


    // exit old labels to left
    labels.exit()
            .transition()
            .duration(dur)
            .attr("fill-opacity", 0)
            // .attr("x", svgWidth)
            // .attr("y", svgHeight - margin.bottom)
            // .attr("height", 0)
            // .attr("width", 0)
            .remove();
*/

    // update axes
    svg.select('.xAxis')
        .transition().duration(dur)
            .call(xAxis)
                .selectAll('text')
                    .attr('transform', 'translate(0, 5)');

    svg.select('.yAxis')
        .transition().duration(dur)
            .call(yAxis);

};


