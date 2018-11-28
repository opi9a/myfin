// general variables
var dur = 1500
    f = d3.format(".1f")
    minBarH = 15
    numberOfCountries = 14;

// unless declare these globally, they aren't updated in the mousovers (??)
var countryData, zoneData;

// set up input table and buttons
var inputTable = d3.select('#input_table tbody')
var inputRows = d3.selectAll('.fundAmt')

var addRowBtn = d3.select('#addRow-btn')
              .on("click", function() { addFundRow() });

var updateBtn = d3.select('#update-btn')

var removeBtns = d3.selectAll('.remove-btn')
                   .on('click', function() { this.parentNode
                                                 .parentNode.remove() });

// initialize country chart
var byAsset = initByAsset();
var byCountry = initByCountry();
var byZone = initByZone();

// MAIN ACTION - ON UPDATE
// inputTable.on("change", function() {
updateBtn.on('click', function() {
    console.log('changed table');
    portfolio = parseInputTable();
    portfolioDistribution = getPortfolioDistribution(portfolio, funds);
    updateAssetChart(portfolioDistribution, byAsset);
    updateCountryChart(portfolioDistribution, byCountry);
    updateZoneChart(portfolioDistribution, byZone);
});

// FUNCTION DEFINITIONS

function initByAsset() {
    console.log('initializing asset chart');

    var byAsset = {
        svgHeight: 150,
        svgWidth: 200,
    }

    byAsset.radius = Math.min(byAsset.svgHeight, byAsset.svgWidth) / 2;


    byAsset['svg'] = d3.select("#chart2").append("svg")
           .attr("width", byAsset.svgWidth)
           .attr("height", byAsset.svgHeight)
             .append("g")
                 .attr("transform",
                       "translate(" + byAsset.svgWidth/2
                                 + "," + byAsset.svgHeight/2 +")");

    byAsset['arc'] = d3.arc()
                        .outerRadius(byAsset.radius - 30)
                        .innerRadius(5);

    return byAsset;

};

function updateAssetChart(portfolioDistribution, chartObj) {
    console.log('updating asset chart');

    let svg = chartObj.svg;
    let arc = chartObj.arc;

    var pieData = [];
    Object.keys(portfolioDistribution.assets).forEach( a => {
        if (a != 'countrySum') {
            console.log('hey');
            // pieData.push(a);
            let row = {asset: a, value: portfolioDistribution.assets[a]};
            pieData.push(row);
        };
    });

    var pie = d3.pie()
        .value(function(d) { return d.value; })(pieData);

    var g = svg.selectAll("arc")
                .data(pie, d => d.data.asset)
                .enter()
                .append("g")
                .attr("class", "arc");

    g.append("path")
        .attr("d", arc)
        .transition()
        .duration(dur)
        .style("fill", d => colors[d.data.asset])
        .style("fill-opacity", d => {
            if (d.data.asset == 'bond') {
                return 0.5
            } else { return 0.85 };
        });

    return pieData;

    
};

function initByZone() {
// Initializes the zone chart

    byZone = {
        svgHeight: 150,
        svgWidth: 340,
        margin: {"top": 15, "bottom": 20, "left": 45, "right":5},
    };

    byZone.chartWidth = byZone.svgWidth
        - (byZone.margin.left + byZone.margin.right);
    byZone.chartHeight = byZone.svgHeight
        - (byZone.margin.top + byZone.margin.bottom);


    // svg, scales, empty axes and button
    byZone['svg'] = d3.select("#chart3").append("svg")
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

    return byZone;
};



function initByCountry() {
// Initializes the country chart

    byCountry = {
        svgHeight: 150,
        svgWidth: 500,
        margin: {"top": 15, "bottom": 20, "left": 45, "right":5},
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

    return byCountry;
};


// main function for drawing and redrawing chart
function updateZoneChart(portfolioDistribution, chartObj) {

    var svgWidth = chartObj.svgWidth;
    var svgHeight = chartObj.svgHeight;
    var margin = chartObj.margin;
    var svg = chartObj.svg;
    var xScale = chartObj.xScale;
    var yScale = chartObj.yScale;
    var xAxis = chartObj.xAxis;
    var yAxis = chartObj.yAxis;

    var newData = flatten(portfolioDistribution.zones, 'zone');
    // this assignment is useful just to mirror the country function,
    // which has the extra step of generating a trimmed portfolio, called
    // countryData
    zoneData = portfolioDistribution.zones;
    console.log('newdata', newData);


    // update scale domains
    xScale.domain(newData.map(a => a.zone));
    yScale.domain([0, d3.max(newData, d => Number(d.end))]);
    
    // rebind data
    var bars = svg.selectAll("rect").data(newData, d => (d.zone
                                                         + d.type));
    
    // get enter bar selection - situate at right end, zero size
    bars.enter()
            .append("rect")
            .attr("class", "bar")
            .attr("class", d => d.type)
            .each(function(d) { d3.select(this).classed(d.zone, true) } )
            .attr("x", svgWidth)
            .attr("y", svgHeight - margin.bottom)
            .attr("width", xScale.bandwidth())
            .on("mouseover", function(d) {
                var boxSum = sumObj(zoneData[d.zone]);
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
                var ttList = makeProfile(d.zone, zoneData);
                for (i in ttList) {
                    svg.append("text")
                      .attr("x", 0.82*svgWidth).attr("y", margin.top + 5 + i*10)
                      .attr("class", "tooltip")
                      .text(ttList[i]) 
                      .attr("fill-opacity", 0)
                      .transition()
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

    // make enter selection for labels, initiate on right
    labels = svg.selectAll('.barLabels')
                  .data(newData, d => (d.zone + d.type));

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


// main function for drawing and redrawing chart
function updateCountryChart(portfolioDistribution, chartObj) {

    var svgWidth = chartObj.svgWidth;
    var svgHeight = chartObj.svgHeight;
    var margin = chartObj.margin;
    var svg = chartObj.svg;
    var xScale = chartObj.xScale;
    var yScale = chartObj.yScale;
    var xAxis = chartObj.xAxis;
    var yAxis = chartObj.yAxis;

    countryData = orderCountries(portfolioDistribution,
                                            numberOfCountries);
    var newData = flatten(countryData, 'country');

    // update scale domains
    xScale.domain(newData.map(a => a.country));
    yScale.domain([0, d3.max(newData, d => Number(d.end))]);
    
    // rebind data
    var bars = svg.selectAll("rect").data(newData, d => (d.country
                                                         + d.type));
    
    // get enter bar selection - situate at right end, zero size
    bars.enter()
            .append("rect")
            .attr("class", "bar")
            .attr("class", d => d.type)
            .each(function(d) { d3.select(this).classed(d.country, true) } )
            .attr("x", svgWidth)
            .attr("y", svgHeight - margin.bottom)
            .attr("width", xScale.bandwidth())
            .on("mouseover", function(d) {
                let boxSum = sumObj(countryData[d.country]);
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
                var ttList = makeProfile(d.country, countryData);
                for (i in ttList) {
                    svg.append("text")
                      .attr("x", 0.5*svgWidth).attr("y", margin.top + 5 + i*10)
                      .attr("class", "tooltip")
                      .text(ttList[i]) 
                      .attr("fill-opacity", 0)
                      .transition()
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
        .attr("y", margin.top)
        .transition()
        .attr("height", 0)
        // .attr("width", 0)
        .remove();

    // make enter selection for labels, initiate on right
    labels = svg.selectAll('.barLabels')
                  .data(newData, d => (d.country + d.type));

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



function removeRow(input) {
    input.remove();
}


function addFundRow() {
    fundRow = inputTable.append('tr');
    fundRow.append('td').append('input')
                .attr('type', 'text')
                .attr('value', '?')
                .attr('class', 'fund_row fundName');

    fundRow.append('td').append('input')
                .attr('type', 'number')
                .attr('value', 0)
                .attr('class', 'fund_row fundAmt');

    fundRow.append('td').append('button')
                .text('x')
                .attr('class', 'remove-btn');

    // think I have to repeat this now
    removeBtns = d3.selectAll('.remove-btn')
    removeBtns.on('click', function() { this.parentNode
                                            .parentNode.remove() });
};


function parseInputTable(byPercent = true) {


    var fundSet = Object.keys(funds);
    var out = {};
    var divisor;
    let portfolioSum = 0;
    var names = document.getElementsByClassName('fundName');
    var amts = document.getElementsByClassName('fundAmt');

    for (var i=0; i<names.length; i++) {
        name = names[i].value.toUpperCase();
        amt = amts[i].value;

        if (fundSet.includes(name)) {
          out[name] = Number(amt);
          portfolioSum += Number(amt);
        }
        
        else { alert(name + ' is not in set of funds - ignoring it'); }
    };


    if (byPercent) {
        divisor = portfolioSum / 100;
        console.log('out obj to divide', clone(out));

        Object.keys(out).forEach(x => out[x] /= divisor );
    };

    return out;
}



function getPortfolioDistribution(portfolio, funds) {
    // for an input portfolio of funds, returns the distribution
    // across countries - given a dataset of distributions of each
    // fund across countries (fundsDistribution)

    // create empty object for each country in the portfolio
    var countries = {}; // the output object containing the distribution

    // create empty object for each zone in the portfolio
    var zones = {}; // not used yet

    var assets = {};

    // initialise the fee
    var fee = 0 // not used yet


    // go through each fund in the portfolio
    for (var fund in portfolio) {

        // get type of asset
        var assetType = funds[fund].type;

        // add to total for that asset type, initialising if reqd
        if (!(assetType in assets)) {
            assets[assetType] = 0;
        };

        assets[assetType] += portfolio[fund];

        // go through each country in the fund, finding the
        // amount of the fund in the country, and adding to the running
        // sum for that country
        for (var zone in funds[fund]['zones']) {

            // check if zone already in object - if not, initialise it
            if (!(zone in zones)) {
                zones[zone] = {}
                zones[zone]['zoneSum'] = 0;
            };

            // // check if type already in object, initialise if not
            if (!(assetType in zones[zone])) {
                zones[zone][assetType] = 0;
            };


            // get percentage for that zone in the fund, and weight
            // by multiplying by the amount of that fund in the portfolio 
            // - note values passed are in %, so need div 100
            var percentageOfFund = funds[fund]['zones'][zone] / 100;
            var amtInZone = portfolio[fund];
            var toAdd = percentageOfFund * amtInZone;

            // increment the corresponding country in the output distribution
            zones[zone][assetType] += toAdd;
            zones[zone]['zoneSum'] += toAdd;
        };

        for (var country in funds[fund]['countries']) {

            // check if country already in object - if not, initialise it
            if (!(country in countries)) {
                countries[country] = {}
                countries[country]['countrySum'] = 0;
            };

            // // check if type already in object, initialise if not
            if (!(assetType in countries[country])) {
                countries[country][assetType] = 0;
            };


            // get percentage for that country in the fund, and weight
            // by multiplying by the amount of that fund in the portfolio 
            // - note values passed are in %, so need div 100
            var percentageOfFund = funds[fund]['countries'][country] / 100;
            var amtInCountry = portfolio[fund];
            var toAdd = percentageOfFund * amtInCountry;

            // increment the corresponding country in the output distribution
            countries[country][assetType] += toAdd;
            countries[country]['countrySum'] += toAdd;
        };
    };

    return { countries: countries, zones: zones, assets: assets };
};


function orderCountries(portfolio, numberOfBars) {   

    var outList = [];
    for (var country in portfolio.countries) {
        outList.push({country: country,
                      value: portfolio.countries[country].countrySum} );
    };


    var topRows = outList.sort( (a, b) => b.value - a.value )
                                    .slice(0, numberOfBars);
    var topNames = [];
    topRows.forEach( function(a) { topNames.push(a.country); } );

    // subset of portfolio with just the topN countries
    var trimmedPortfolio = {};

    var assetSums = {};
    var assetKeys = Object.keys(portfolio.assets);

    // add in country sum key, and 'asset', so can track this too
    assetKeys.push('countrySum');
    portfolio.assets['countrySum'] = d3.sum(Object.values(portfolio.assets));

    // initialised asset sums
    assetKeys.forEach( a => assetSums[a] = 0 );

    // for each country in topNames
    topNames.forEach( function(country) {
        // - for each asset in the country (bond, stock gold):
        //   - increment the assetSum
        trimmedPortfolio[country] = portfolio.countries[country];
        assetKeys.forEach( function(asset) {
            var toAdd = portfolio.countries[country][asset];
            if (typeof(toAdd) !== "undefined") {
                assetSums[asset] += toAdd;
            };
        });
        // - copy to trimmed portfolio
        trimmedPortfolio[country] = portfolio.countries[country];
    });
    
    // get residuals for assets
    var assetResiduals = {};
    assetKeys.forEach( function(asset) {
        var toAdd = portfolio.assets[asset] - assetSums[asset];
        assetResiduals[asset] = toAdd;
    });
    // a new 'other' member with sum of each assets for countries outside topN

    trimmedPortfolio['other'] = assetResiduals;

    return trimmedPortfolio

};


// set up colors for likely countries (not all)
var country_list = ['USA', 'FRA', 'DEU',
                    'JPN', 'ITA', 'CAN', 'CHN',
                    'ESP', 'NLD', 'KOR', 'RUS', 'IND', 'BRA']
    colors = {}

    for (var i=0; i<country_list.length; i++) {
        colors[country_list[i]] = d3.schemeCategory20[i];
    }
    
    colors['NoN'] = 'gold';
    colors['GBR'] = 'darkRed';
    colors['uk'] = 'darkRed';
    colors['na'] = colors.USA;
    colors['cn'] = colors.CHN;
    colors['nn'] = colors.NoN;
    colors['eu'] = colors.DEU;
    colors['la'] = colors.BRA;
    colors['as'] = colors.JPN;
    colors['em'] = colors.IND;
    colors['pc'] = colors.RUS;
    colors['bond'] = 'steelBlue';
    colors['stock'] = 'steelBlue';
    colors['gold'] = 'gold';


var portfolio_x = {
    'VFEM': 11.08,
    'AGBP': 27.81,
    'H50E': 22.23,
    'IGLN': 16.67,
    'XDJP': 11.11,
    'XDUS': 11.09,
};

var testPortfolio = {
    xfas: 5,
    xfab: 1,
    xfag: 1,
    xfbs: 1,
    xfbb: 1,
    xfbg: 1,
}

var testFunds = {
    xfas: { countries: { USA: 76, GBR: 20, FRA: 3, NDL: 1 },
            zones: { NA: 76, UK: 20, EU: 4 },
            type: 'bond',
            fee: 0.05 },
    xfab: { countries: { USA: 76, GBR: 20, FRA: 3, NDL: 1 },
            zones: { NA: 76, UK: 20, EU: 4 },
            type: 'stock',
            fee: 0.03 },
    xfag: { countries: { NoN: 100 },
            zones: { nn: 100 },
            type: 'gold',
            fee: 0.07 },

    xfbs: { countries: { USA: 10, GBR: 86, DEU: 3, NDL: 1 },
            zones: { NA: 10, UK: 86, EU: 4 },
            type: 'bond',
            fee: 0.05 },
    xfbb: { countries: { USA: 10, GBR: 86, DEU: 3, NDL: 1 },
            zones: { NA: 10, UK: 86, EU: 4 },
            type: 'stock',
            fee: 0.03 },
    xfbg: { countries: { NoN: 100 },
            zones: { nn: 100 },
            type: 'gold',
            fee: 0.07 },
}


function flatten(areas, areaType) {

    if (!['country', 'zone'].includes(areaType)) {
        alert('areaType passed to flatten needs to be country or zone');
        return 1;
    };


    /* return data in form:
    [
      {country: 'USA', type: 'bond', start: '0', end: '6', key: 'USA-bond'},
      {country: 'USA', type: 'stock', start: '6', end: '8', key: 'USA-stock'},
      {country: 'JPN', type: 'stock', start: '0', end: '3', key: 'JPN-stock'},
      {country: 'JPN', type: 'bond', start: '3', end: '7', key: 'JPN-bond'},
      {country: 'NoN', type: 'gold', start: '0', end: '12', key: 'NoN-gold'},
    ]
        */
    // for each country / zone
    // for each type
    // make an entry
    var out = []; 

    for (var area in areas) {
        var lastEnd = 0;
        delete areas[area].countrySum;
        delete areas[area].zoneSum;
        assets = Object.keys(areas[area]).sort().reverse();

        assets.forEach( function(asset) {
            var row = {};
            row[areaType] = area;
            row['type'] = asset;
            row['start'] = f(lastEnd);
            var amt = areas[area][asset];
            row['end'] = f(lastEnd + amt);
            out.push(row);
            lastEnd += amt;
        });

    };

    return out;
};


function clone(obj) {
    var copy;

    // Handle the 3 simple types, and null or undefined
    if (null == obj || "object" != typeof obj) return obj;

    // Handle Date
    if (obj instanceof Date) {
        copy = new Date();
        copy.setTime(obj.getTime());
        return copy;
    }

    // Handle Array
    if (obj instanceof Array) {
        copy = [];
        for (var i = 0, len = obj.length; i < len; i++) {
            copy[i] = clone(obj[i]);
        }
        return copy;
    }

    // Handle Object
    if (obj instanceof Object) {
        copy = {};
        for (var attr in obj) {
            if (obj.hasOwnProperty(attr)) copy[attr] = clone(obj[attr]);
        }
        return copy;
    }

    throw new Error("Unable to copy obj! Its type isn't supported.");
}


function makeProfile(area, areaData) {

    areaRow = areaData[area];
    out = [];

    var areaName;
    if (( area == 'NoN') || ( area == 'nn')) {
        areaName = 'Not National' }
    else { areaName = area };

    Object.keys(areaRow)
        .forEach(a => {
            if (areaRow[a] > 0.05 ) {
                out.push(a + ": " + f(areaRow[a]));
            }
        })
    out = out.sort()
    out.unshift(areaName);

    return out;
}


function sumObj(inObj) {
    return d3.sum(Object.values(inObj));
}
