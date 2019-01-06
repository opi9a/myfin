
function initByZone() {
// Initializes the zone chart

    byZone = {
        svgHeight: 190,
        svgWidth: 324,
        margin: {"top": 55, "bottom": 30, "left": 35, "right":5},

        totalAmt: 1,
        dataSource: 'none yet',
        currentMode: 'none',
        setData: setZoneData,
        update: updateZoneChart,

        chartData: {
            byAmt: [],
            byPercent: [],
        },

        mouseData: {
            byAmt: [],
            byPercent: [],
        },
    };

    byZone.chartWidth = byZone.svgWidth
        - (byZone.margin.left + byZone.margin.right);
    byZone.chartHeight = byZone.svgHeight
        - (byZone.margin.top + byZone.margin.bottom);


    // svg, scales, empty axes and button
    byZone['svg'] = d3.select("#chart3").append("svg")
              .attr("class", "byZone")
              .attr("width", byZone.svgWidth)
              .attr("height", byZone.svgHeight)

    byZone['yScale'] = d3.scaleLinear()
                .domain([0, 100])
                .range([byZone.svgHeight - byZone.margin.bottom,
                        byZone.margin.top])

    byZone['xScale'] = d3.scaleBand()
                .range([0, byZone.chartWidth])
                .align(0)
                .padding(0.05)

    byZone['yAxis'] = d3.axisLeft().scale(byZone.yScale)
                .ticks(6)
                .tickSizeOuter(0)

    byZone['xAxis'] = d3.axisBottom().scale(byZone.xScale)
                .tickSize(0)

    byZone.svg.append('g')
        .attr('class', 'xAxis byZone')
        .attr('transform', 'translate(' + (byZone.margin.left) + ', '
                                        + (byZone.chartHeight
                                            + byZone.margin.top) + ')')
        .call(byZone.xAxis)
            .selectAll('text')
            .attr('transform', 'translate(0, 5)')

    byZone.svg.append('g')
        .attr('class', 'yAxis byZone')
        .attr('transform', 'translate(' + (byZone.margin.left - 1) + ', 0)')
        .call(byZone.yAxis);

    byZone.svg.append('text')
        .attr("class", "chart-title")
        .attr("transform", "translate(35, 20)")
        .text("Zones")

    byZone['update'] = updateZoneChart;

    return byZone;
};


function setZoneData(newData, dataSource) {
    this.coreData = newData;
    this.dataSource = dataSource;

    // create chartData byAmt and byPercent
    this.totalAmt = sumObj(sumAssetsAcrossArea(newData)) / 2; // div 2 as zoneSums in there
    this.chartData.byAmt = flatten(newData, 'zone');
    this.chartData.byPercent = getPercents(this.chartData.byAmt);

    // create mouseData byAmt and byPercent
    this.mouseData.byAmt = newData;

    x = {};
    for (zone in newData) {
        if (!Object.keys(x).includes(zone)) {
            x[[zone]] = {};
        };

        for (elem in newData[zone]) {
            x[zone][elem] = 100 * newData[zone][elem] 
                        /  this.totalAmt;
        };
    };

    this.mouseData.byPercent = x;

};


// main function for drawing and redrawing chart
function updateZoneChart(mode) {

    var svgWidth = this.svgWidth;
    var svgHeight = this.svgHeight;
    var margin = this.margin;
    var svg = this.svg;
    var xScale = this.xScale;
    var yScale = this.yScale;
    var xAxis = this.xAxis;
    var yAxis = this.yAxis;

    this.currentMode = mode;

    var mouseData = this.mouseData;
    var chartData = this.chartData[mode];


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
        .attr("fill-opacity", 1) ;

    title.exit().transition("chart-title out").remove();

    // update scale domains
    xScale.domain(chartData.map(a => a.zone));
    yScale.domain([0, d3.max(chartData, d => Number(d.end))]);
    
    // rebind data
    var bars = svg.selectAll("rect").data(chartData, d => (d.zone
                                                         + d.type));
    
    // get enter bar selection - situate at right end, zero size
    var newBars = bars.enter()
        .append("rect")
        .attr("class", "bar")
        .attr("class", d => d.type)
        .each(function(d) { d3.select(this).classed(d.zone, true) } )
        .attr("x", svgWidth)
        .attr("y", svgHeight - margin.bottom)
        .attr("width", xScale.bandwidth());


    var infoBtns = svg.selectAll("g.zone-info")
        .data(chartData, d => d.zone)
        .enter().append("g")
        .attr("class", "zone-info");

    infoBtns.append("rect")
        .attr("x", d => xScale(d.zone) + margin.left + 2)
        .attr("y", svgHeight - 10)
        .transition("infoBtns-zone").delay(dur / 2)
        .attr("width", xScale.bandwidth() - 4)
        .attr("height", 20)
        .attr("fill", "green");

    infoBtns.append("text")
        .text("i") 
        .attr("x", d => xScale(d.zone) + margin.left + xScale.bandwidth()/2)
        .attr("y", svgHeight - 2)
        .attr("font-size", 9)
        .attr("font-family", "sans-serif")
        .attr("cursor", "pointer")
        .attr("fill", "white");

    infoBtns.on("click", function(d) {

        let zoneName = d.zone;

        if (infoBtnActive == zoneName) {
            infoBtnActive = 'none';
            update(portfolio);
            return;
        };

        infoBtnActive = zoneName;
        // names of countries in the zone
        let zoneCountryNames = zonesByCountry[d.zone];
        // empty object to fill with zone country data (amts of each asset)
        let zoneCountries = {};
        // starting data to copy the subset from
        let allCountries = portfolioDistributions.countries;

        zoneCountryNames.forEach(function(d) {
            let key = d.toUpperCase();
            // copy across
            if (Object.keys(allCountries).includes(key)) {
            zoneCountries[key] = allCountries[key];
            } else { console.log('cannot find', key, 'in portfolioDistributions') };
        });

        // update the country chart
        byCountry.setData(zoneCountries,
                          zoneLookup[d.zone] + " zone", maxColumns);
        byCountry.update(mode);

        // update the asset chart
        // want in form like {stock: 150, bond: 53, gold: 25}
        var zoneAssets = {};
        for (var country in zoneCountries) {
            for (var elem in zoneCountries[country]) {
                if (elem == 'countrySum') { continue };
                if (!Object.keys(zoneAssets).includes(elem)) {
                    zoneAssets[elem] = 0;
                };
                zoneAssets[elem] += zoneCountries[country][elem];
            };
        };

        byAsset.setData(zoneAssets);
        byAsset.update(mode);
    });
    


    newBars.on("mouseover", function(d) {
        // need to pass the global variable here, as this assignment is 
        // made only when update function is called - not each mouseover
        // - mode is passed to the update function which this sits in.
        // The key question!! presumably mode gets bound when function declared
        // or something
        mode = byZone.currentMode;

        let boxSum = sumObj(mouseData[mode][d.zone]);
        console.log('boxSum', boxSum);
        var boxH = yScale(0) - yScale(boxSum);
        console.log('boxSum', boxSum);
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
              .attr("stroke-width", "3px");
        var ttList = makeProfile(d.zone, mouseData, mode);
        for (i in ttList) {
            svg.append("text")
              .attr("x", 0.72*svgWidth).attr("y", margin.top + 5 + i*10)
              .attr("class", "tooltip")
              .text(ttList[i]) 
              .attr("fill-opacity", 0)
              .transition()
              .delay(200)
              .duration(800)
              .attr("fill-opacity", 1);
        };
     });

    newBars.on("mouseout", function() {
        d3.selectAll('.tooltip')
            .transition()
            .duration(200)
            .remove()
    });

    // merge with update and transition all to new sizes
    newBars.merge(bars)
          .transition().duration(dur)
          .style("fill", function(d, i) {
              if (Object.keys(colors).includes(d.zone)) {
                  return colors[d.zone];
              } else { return 'gray'; };
          })
              
          .attr("fill-opacity", function(d, i) {
              if (d['type'] == 'bond') { return 0.6; };
              if (d['type'] == 'stock') { return 0.8; };
              return 1;
          })
          .attr("height", d => svgHeight
                                - yScale(d.end - d.start)
                                - margin.bottom)
          .attr("x", d => xScale(d.zone) + margin.left)
          .attr("y", d => yScale(d.end))
          .attr("text", d => d.end - d.start) ;

    // exit old bars stage left, diminishing and going transparent
    bars.exit()
        .transition()
        .duration(dur)
        .attr("fill-opacity", 0)
        .attr("y", margin.top)
        .transition()
        .attr("height", 0)
        // .attr("width", 0)
        .remove();

/* LABELS
    // make enter selection for labels, initiate on right
    labels = svg.selectAll('.barLabels')
                  .data(chartData, d => (d.zone + d.type));

    labels.enter().append('text')
        .attr('class', 'barLabels')
        .attr("fill-opacity", 0)
        .attr("x", svgWidth)
        .attr("y", svgHeight - margin.bottom)

    // merge with update selection and transition all labels to right place
        .merge(labels)
        .transition().duration(dur)
          .attr("fill-opacity", 1)
          .attr("x", d => xScale(d.zone)
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

