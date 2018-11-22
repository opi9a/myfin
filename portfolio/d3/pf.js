// set up canvas variables
var svgHeight = 200
    svgWidth = 400
    margin = {"top": 15, "bottom": 25, "left": 45, "right":5}
    chartWidth = svgWidth - (margin.left + margin.right)
    chartHeight = svgHeight - (margin.top + margin.bottom)
    dur = 2000

// set up data variables
var data1 = []
    rand_max = 9
    country_list = ['UK', 'US', 'France', 'Germany',
                    'Japan', 'Italy', 'Canada', 'China',
                    'Spain', 'Russia']
    colors = {}

    for (var i=0; i<country_list.length; i++) {
        colors[country_list[i]] = d3.schemeCategory10[i];
    }


// svg, scales, empty axes and button
var svg = d3.select("#chart1").append("svg")
          .attr("width", svgWidth)
          .attr("height", svgHeight)

yScale = d3.scaleLinear()
            .domain([0, 100])
            .range([svgHeight - margin.bottom, margin.top])

xScale = d3.scaleBand()
            .range([0, chartWidth])
            .align(0)
            .padding(0.05)

yAxis = d3.axisLeft().scale(yScale)
            .ticks(6)

xAxis = d3.axisBottom().scale(xScale)
            .tickSize(0)

svg.append('g')
    .attr('class', 'xAxis')
    .attr('transform', 'translate(' + (margin.left) + ', '
                                    + (chartHeight + margin.top) + ')')
    .call(xAxis)
        .selectAll('text')
        .attr('transform', 'translate(0, 5)')

svg.append('g')
    .attr('class', 'yAxis')
    .attr('transform', 'translate(' + (margin.left) + ', 0)')
    .call(yAxis)


inputTable = d3.select('#input_table tbody')
inputRows = d3.selectAll('.fundAmt')

addRowBtn = d3.select('#addRow-btn')
addRowBtn.on("click", function() { addFundRow() });

updateBtn = d3.select('#update-btn')


// inputTable.on("change", function() {
updateBtn.on('click', function() {
    console.log('changed table');
    portfolio = parseInputTable();
    data1 = get_portfolio_distribution(portfolio, funds_by_country);
    update();
});

var removeBtns

function removeRow(input) {
    input.remove();
}

// FUNCTION DEFINITIONS

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

    removeBtns = d3.selectAll('.remove-btn')
    removeBtns.on('click', function() { this.parentNode.parentNode.remove() });
};


function parseInputTable() {
    var fundSet = Object.keys(funds_by_country);
    var out = {};
    var names = document.getElementsByClassName('fundName');
    var amts = document.getElementsByClassName('fundAmt');
    console.log('names', names);
    console.log('amts', amts);

    for (var i=0; i<names.length; i++) {
        name = names[i].value.toUpperCase();
        amt = amts[i].value;

        if (fundSet.includes(name)) {
          console.log(name, 'is in fundset')
          out[name] = amt;
        }
        
        else { alert(name + ' is not in set of funds - ignoring it'); }
    };

    return out;
}


// main function for drawing and redrawing chart
function update() {

    // update scale domains
    xScale.domain(data1.map(a => a.key));
    yScale.domain([0, d3.max(data1, d => Number(d.value))]);
    
    // rebind data
    console.log(data1);
    var bars = svg.selectAll("rect").data(data1, d => d.key )
    
    // get enter bar selection - situate at right end, zero size
    bars.enter()
            .append("rect")
            .attr("class", "bar")
            .attr("x", svgWidth)
            .attr("y", svgHeight - margin.bottom)
            .attr("width", xScale.bandwidth())

    // merge with update and transition all to new sizes
    .merge(bars)
    .transition().duration(dur)
          .style("fill", d => colors[d.key] )

          .attr("height", function(d, i) {
            return svgHeight - yScale(d.value) - margin.bottom;
          })

          .attr("x", function(d, i) {
            return xScale(d.key) + margin.left;
          })

          .attr("y", function(d, i) {
            return yScale(d.value);
          })

          .attr("text", function(d,i) {
            return d.value;
          });

    // exit old bars stage left, diminishing and going transparent
    bars.exit()
        .attr("fill-opacity", 1)
            .transition()
            .duration(dur)
            .attr("fill-opacity", 0)
            .attr("x", svgWidth)
            .attr("y", svgHeight - margin.bottom)
            .attr("height", 0)
            // .attr("width", 0)
            .remove();

    // make enter selection for labels, initiate on right
    labels = svg.selectAll('.barLabels')
                  .data(data1, d => d.key )

    labels.enter().append('text')
        .attr('class', 'barLabels')
        .attr("x", svgWidth)
        .attr("y", svgHeight - margin.bottom)

    // merge with update selection and transition all labels to right place
        .merge(labels)
        .transition().duration(dur)
          .attr("x", d => xScale(d.key)
                          + margin.left + (xScale.bandwidth() / 2))

          .attr("y", function(d, i) {
            barTop = yScale(d.value);
            if (barTop > svgHeight - margin.bottom - 25) {
              return barTop - 5;
            }
            return barTop + 15;
          })

          .text(function(d,i) {
            return d.value;
          })

          .attr("font-family", "sans-serif")
          .attr("text-anchor", "middle")

          .attr("fill", function(d, i) {
            barTop = yScale(d.value);
            if (barTop > svgHeight - margin.bottom - 25) {
              return "steelBlue";
            }
            return "white";
          });

    // exit old labels to left
    labels.exit()
        .attr("fill-opacity", 1)
            .transition()
            .duration(dur)
            .attr("fill-opacity", 0)
            .attr("x", svgWidth)
            .attr("y", svgHeight - margin.bottom)
            .attr("height", 0)
            .attr("width", 0)
            .remove();

    // update to new x axis
    svg.select('.xAxis')
        .transition().duration(dur)
            .call(xAxis)
                .selectAll('text')
                    .attr('transform', 'translate(0, 5)');

    svg.select('.yAxis')
        .transition().duration(dur)
            .call(yAxis);

};


function make_data() {

    var countries_used = [];
        data_out = [] 
        rand_len = Math.round(Math.random() * rand_max) + 4

    for (var i=0; i < rand_len; i++) {
        var co = country_list[Math.round(Math.random() * rand_max)];
        var val = Math.round(Math.random() * rand_max);
        if (!countries_used.includes(co)) {
          data_out.push({key: co, value: val});
          countries_used.push(co);
          // console.log('added', co, 'value', val, 'index', ind);
        }
    }

    return data_out.sort((a, b) => b.value - a.value);
}


function get_portfolio_distribution(portfolio, fundsDistributions) {
    // for an input portfolio of funds, returns the distribution
    // across countries - given a dataset of distributions of each
    // fund across countries (fundsDistribution)

    var portDistrib = {}, // the output object containing the distribution
        out1 = []
        out2 = []
        toAdd = 0,
        valSum = 0;

    var f = d3.format(".1f");
    var fund, c;

    // go through each fund in the portfolio
    for (fund in portfolio) {

        // go through each country in the fund
        for (c in fundsDistributions[fund]) {

            // check if country already in object - if not, initialise it
            if (!(c in portDistrib)) {
                portDistrib[c] = 0;
            }

            // get percentage for that country in the fund, and weight
            // by multiplying by the amount of that fund in the portfolio 
            toAdd= fundsDistributions[fund][c] * portfolio[fund];

            // increment the corresponding country in the output distribution
            portDistrib[c] += toAdd;

            // and increment the sum for the distribution
            valSum += toAdd;
        }
    }

    // reweight values to 1 using the sum of all values added
    for (c in portDistrib) {
        out1.push({ key: c, value: portDistrib[c] / valSum });
    }

    // sort
    out1 = out1.sort((a, b) => b.value - a.value);

    // take top 8 and sum the rest
    var others_sum = out1.slice(8).map(a => a.value).reduce((a,b) => a + b, 0);
    out2 = out1.slice(0, 8);
    var others_len = out1.length - 8;
    out2.push({ key: "+" + others_len, value: others_sum });
    
    // format to %
    for (var c in out2) {
        out2[c].value = f(100 * out2[c].value);
    }
    
    return out2;
};


var portfolio_x = {
    'VFEM': 11.08,
    'AGBP': 27.81,
    'H50E': 22.23,
    'IGLN': 16.67,
    'XDJP': 11.11,
    'XDUS': 11.09,
};


var funds_by_country = 
{"H50E":{"FRA":36.89,"DEU":30.85,"ESP":10.0,"NLD":9.96,"ITA":4.57,"KOR":2.96,"BEL":2.65,"FIN":1.13,"USA":1.0},"GILI":{"GBR":100.0},"GILS":{"GBR":100.0},"XDUS":{"USA":99.26,"CHE":0.24,"GBR":0.12,"CAN":0.08,"CHN":0.07,"BRA":0.06,"RUS":0.05,"SGP":0.05,"IRL":0.03,"SWE":0.03},"CSP1":{"USA":99.56,"CHE":0.26,"RUS":0.05,"SGP":0.05,"GBR":0.04,"IRL":0.03},"CUKX":{"GBR":91.58,"USA":5.07,"CHE":2.26,"IRL":0.37,"DEU":0.36,"ARE":0.15,"CHN":0.08,"MEX":0.08,"ESP":0.01,"FRA":0.01,"KOR":0.01,"SWE":0.01,"CAN":0.0,"IND":0.0},"MEUD":{"GBR":26.93,"FRA":16.2,"DEU":14.91,"CHE":12.5,"NLD":5.1,"ESP":4.71,"SWE":4.29,"ITA":3.31,"DNK":2.79,"USA":1.96,"BEL":1.76,"FIN":1.75,"NOR":1.13,"KOR":0.94,"AUT":0.44,"IRL":0.44,"PRT":0.27,"RUS":0.18,"SGP":0.15,"CZE":0.08,"LUX":0.08,"ARE":0.05,"MLT":0.03},"ISF":{"GBR":91.58,"USA":5.07,"CHE":2.25,"IRL":0.37,"DEU":0.35,"ARE":0.15,"CHN":0.08,"MEX":0.08,"ESP":0.01,"FRA":0.01,"KOR":0.01,"SWE":0.01,"CAN":0.0,"IND":0.0},"CSH2":{},"VUSA":{"USA":99.55,"CHE":0.26,"SGP":0.06,"RUS":0.05,"GBR":0.04,"IRL":0.03},"IUSA":{"USA":99.56,"CHE":0.26,"RUS":0.05,"SGP":0.05,"GBR":0.04,"IRL":0.03},"HUKX":{"GBR":91.58,"USA":5.07,"CHE":2.26,"IRL":0.37,"DEU":0.35,"ARE":0.15,"CHN":0.08,"MEX":0.08,"ESP":0.01,"FRA":0.01,"KOR":0.01,"SWE":0.01,"CAN":0.0,"IND":0.0},"VUKE":{"GBR":91.59,"USA":5.09,"CHE":2.18,"IRL":0.39,"DEU":0.35,"ARE":0.18,"MEX":0.09,"CHN":0.08,"ESP":0.01,"FRA":0.01,"KOR":0.01,"SWE":0.01,"CAN":0.0,"IND":0.0},"XDPG":{"USA":99.57,"CHE":0.25,"RUS":0.05,"SGP":0.05,"GBR":0.04,"IRL":0.03},"XDDX":{"DEU":100.0},"XDJP":{"JPN":100.0},"SPY5":{"USA":99.55,"CHE":0.25,"RUS":0.06,"SGP":0.06,"GBR":0.04,"IRL":0.03},"ERNS":{"GBR":37.08,"CAN":15.55,"DEU":10.59,"NLD":7.73,"XSN":6.92,"SWE":5.82,"FRA":5.18,"AUS":3.52,"NOR":3.04,"ITA":1.78,"NZL":1.61,"FIN":0.92,"USA":0.2,"HKG":0.02,"SGP":0.02},"XESC":{"FRA":36.92,"DEU":30.72,"NLD":10.01,"ESP":10.0,"ITA":4.66,"KOR":2.9,"BEL":2.67,"FIN":1.12,"USA":0.99},"XUKX":{"GBR":91.58,"USA":5.08,"CHE":2.25,"IRL":0.37,"DEU":0.35,"ARE":0.15,"CHN":0.08,"MEX":0.08,"ESP":0.01,"FRA":0.01,"KOR":0.01,"SWE":0.01,"CAN":0.0,"IND":0.0},"DBXD":{"DEU":100.0},"XESX":{"FRA":36.92,"DEU":30.72,"NLD":10.01,"ESP":10.0,"ITA":4.66,"KOR":2.9,"BEL":2.67,"FIN":1.12,"USA":0.99},"HSPX":{"USA":99.55,"CHE":0.25,"IRL":0.05,"RUS":0.05,"SGP":0.05,"GBR":0.04},"EUE":{"FRA":36.89,"DEU":30.85,"ESP":10.0,"NLD":9.96,"ITA":4.57,"KOR":2.96,"BEL":2.65,"FIN":1.13,"USA":1.0},"EXW1":{"FRA":36.89,"DEU":30.85,"ESP":10.0,"NLD":9.96,"ITA":4.57,"KOR":2.96,"BEL":2.65,"FIN":1.13,"USA":1.0},"CS51":{"FRA":36.88,"DEU":30.85,"ESP":10.0,"NLD":9.96,"ITA":4.57,"KOR":2.96,"BEL":2.65,"FIN":1.13,"USA":1.0},"VMID":{"GBR":89.58,"USA":3.08,"JPN":0.81,"IND":0.78,"CHN":0.77,"CHE":0.63,"IRL":0.55,"RUS":0.48,"DEU":0.36,"FRA":0.34,"EGY":0.31,"KOR":0.23,"VNM":0.23,"TWN":0.2,"NLD":0.17,"HKG":0.16,"BRA":0.14,"ZAF":0.13,"MEX":0.09,"DNK":0.08,"ESP":0.08,"IDN":0.08,"SGP":0.08,"AUS":0.07,"SWE":0.07,"CAN":0.06,"NOR":0.06,"THA":0.06,"ITA":0.05,"BEL":0.03,"PER":0.03,"CHL":0.02,"FIN":0.02,"MYS":0.02,"PHL":0.02,"AUT":0.01,"CZE":0.01,"HUN":0.01,"ISR":0.01,"KAZ":0.01,"KEN":0.01,"MAC":0.01,"NGA":0.01,"NZL":0.01,"PAK":0.01,"ROU":0.01,"TUR":0.01,"VGB":0.01,"ARE":0.0,"ARG":0.0,"COL":0.0,"CYM":0.0,"CYP":0.0,"GHA":0.0,"GRC":0.0,"IRQ":0.0,"ISL":0.0,"KHM":0.0,"LBN":0.0,"LKA":0.0,"LUX":0.0,"MAR":0.0,"MCO":0.0,"MUS":0.0,"POL":0.0,"PRT":0.0,"SAU":0.0,"TZA":0.0},"VNRT":{"USA":94.38,"CAN":4.77,"CHN":0.26,"CHE":0.23,"GBR":0.14,"SGP":0.06,"BRA":0.05,"SWE":0.04,"IRL":0.03,"RUS":0.03},"AGBP":{"USA":39.65,"JPN":16.47,"FRA":6.29,"GBR":5.39,"DEU":4.87,"ITA":3.52,"CAN":3.44,"ESP":2.82,"NLD":2.44,"XSN":2.15,"AUS":1.72,"KOR":1.37,"BEL":1.05,"SWE":0.83,"MEX":0.71,"AUT":0.69,"IDN":0.48,"POL":0.46,"CHE":0.4,"DNK":0.39,"IRL":0.37,"NOR":0.36,"MYS":0.35,"CHN":0.32,"THA":0.31,"FIN":0.3,"SGP":0.29,"PRT":0.28,"HKG":0.24,"RUS":0.2,"ISR":0.16,"NZL":0.16,"CHL":0.15,"CZE":0.13,"SAU":0.11,"HUN":0.1,"SVK":0.1,"QAT":0.09,"ARE":0.08,"COL":0.08,"OMN":0.08,"IND":0.07,"ROU":0.07,"SVN":0.07,"PHL":0.06,"KAZ":0.05,"LUX":0.05,"PAN":0.04,"PER":0.04,"URY":0.04,"LTU":0.03,"BGR":0.02,"BRA":0.01,"ISL":0.01,"JEY":0.01,"KWT":0.01,"LVA":0.01,"MAR":0.01},"TI5G":{"USA":100.0,"AUS":0.0,"CAN":0.0},"VERX":{"FRA":22.13,"DEU":20.93,"CHE":18.03,"NLD":7.2,"ESP":6.6,"SWE":5.96,"ITA":4.47,"DNK":3.71,"FIN":2.51,"BEL":2.38,"NOR":1.56,"KOR":1.25,"USA":0.94,"AUT":0.61,"IRL":0.48,"GBR":0.39,"PRT":0.35,"RUS":0.21,"SGP":0.19,"LUX":0.11},"VEUR":{"GBR":26.16,"FRA":15.92,"DEU":15.14,"CHE":13.56,"NLD":5.18,"ESP":4.75,"SWE":4.29,"ITA":3.22,"DNK":2.67,"USA":2.0,"FIN":1.81,"BEL":1.71,"NOR":1.12,"KOR":0.9,"IRL":0.45,"AUT":0.44,"PRT":0.25,"RUS":0.17,"SGP":0.14,"LUX":0.08,"ARE":0.05,"MEX":0.02},"VGOV":{"GBR":100.0},"VECP":{"FRA":20.59,"USA":18.43,"NLD":16.59,"GBR":10.98,"DEU":8.44,"ITA":4.34,"ESP":4.07,"SWE":3.02,"AUS":2.97,"BEL":2.3,"CHE":1.5,"DNK":1.31,"LUX":0.79,"IRL":0.78,"NOR":0.76,"AUT":0.49,"MEX":0.4,"HKG":0.39,"NZL":0.37,"VGB":0.37,"FIN":0.19,"JPN":0.19,"POL":0.19,"PRT":0.19,"CZE":0.18,"SGP":0.18},"SMEA":{"GBR":26.24,"FRA":16.49,"DEU":15.03,"CHE":13.69,"NLD":4.81,"ESP":4.6,"SWE":3.92,"ITA":2.99,"DNK":2.66,"USA":2.16,"FIN":2.03,"BEL":1.61,"NOR":1.24,"KOR":0.86,"IRL":0.41,"AUT":0.38,"CHN":0.33,"PRT":0.25,"SGP":0.14,"LUX":0.09,"ARE":0.05,"MEX":0.03},"IMEU":{"GBR":26.27,"FRA":16.51,"DEU":15.0,"CHE":13.7,"NLD":4.82,"ESP":4.61,"SWE":3.92,"ITA":3.0,"DNK":2.66,"USA":2.14,"FIN":2.03,"BEL":1.6,"NOR":1.23,"KOR":0.86,"IRL":0.41,"AUT":0.38,"CHN":0.32,"PRT":0.25,"SGP":0.14,"LUX":0.09,"ARE":0.05,"MEX":0.02},"VUCP":{"USA":80.18,"GBR":4.51,"CAN":3.13,"NLD":2.87,"FRA":2.0,"AUS":1.85,"JPN":1.68,"CHE":0.86,"SWE":0.6,"MEX":0.51,"DEU":0.5,"ESP":0.33,"CHL":0.18,"ITA":0.17,"PER":0.11,"CYM":0.09,"IND":0.09,"HKG":0.08,"NOR":0.08,"DNK":0.06,"KOR":0.06,"SGP":0.05},"CEU1":{"FRA":32.29,"DEU":29.19,"NLD":9.44,"ESP":9.05,"ITA":5.86,"FIN":3.26,"BEL":3.14,"USA":2.0,"KOR":1.68,"GBR":0.94,"IRL":0.82,"AUT":0.75,"CHN":0.63,"PRT":0.49,"SGP":0.27,"LUX":0.18},"GLTL":{"GBR":100.0},"VUSC":{"USA":73.36,"GBR":5.2,"AUS":4.42,"CAN":3.6,"NLD":3.16,"JPN":2.32,"FRA":1.94,"SWE":1.83,"CHE":1.81,"HKG":0.61,"DEU":0.53,"SGP":0.4,"COL":0.33,"ESP":0.24,"MEX":0.24},"L100":{"GBR":92.55,"USA":4.37,"CHE":1.93,"IRL":0.39,"DEU":0.35,"ARE":0.18,"MEX":0.09,"CHN":0.08,"ESP":0.01,"FRA":0.01,"KOR":0.01,"SWE":0.01,"CAN":0.0,"IND":0.0},"XSTR":{},"GLTS":{"GBR":100.0},"TRSY":{"USA":100.0},"HMWO":{"USA":62.31,"JPN":8.52,"GBR":5.87,"FRA":3.58,"CAN":3.39,"DEU":3.23,"CHE":3.09,"AUS":2.28,"NLD":1.12,"HKG":1.08,"ESP":0.97,"SWE":0.82,"DNK":0.63,"ITA":0.63,"FIN":0.49,"SGP":0.47,"BEL":0.35,"NOR":0.25,"ISR":0.19,"KOR":0.16,"CHN":0.15,"IRL":0.1,"AUT":0.06,"MAC":0.06,"PRT":0.06,"NZL":0.05,"BRA":0.03,"LUX":0.03,"RUS":0.02,"PHL":0.01},"XUSD":{},"XMCX":{"GBR":89.06,"USA":3.37,"JPN":0.82,"CHN":0.76,"IND":0.74,"CHE":0.64,"IRL":0.52,"RUS":0.47,"ISR":0.37,"DEU":0.33,"EGY":0.33,"FRA":0.33,"VNM":0.25,"KOR":0.22,"TWN":0.2,"HKG":0.15,"NLD":0.15,"BRA":0.14,"ZAF":0.12,"MEX":0.09,"ESP":0.08,"IDN":0.08,"SGP":0.08,"AUS":0.07,"DNK":0.07,"SWE":0.07,"CAN":0.06,"THA":0.06,"ITA":0.05,"NOR":0.05,"BEL":0.03,"PER":0.03,"CHL":0.02,"FIN":0.02,"MYS":0.02,"PHL":0.02,"AUT":0.01,"CZE":0.01,"HUN":0.01,"KAZ":0.01,"KEN":0.01,"MAC":0.01,"NGA":0.01,"NZL":0.01,"PAK":0.01,"ROU":0.01,"TUR":0.01,"VGB":0.01,"ARE":0.0,"ARG":0.0,"COL":0.0,"CYM":0.0,"CYP":0.0,"GHA":0.0,"GRC":0.0,"IRQ":0.0,"ISL":0.0,"KHM":0.0,"LBN":0.0,"LKA":0.0,"LUX":0.0,"MAR":0.0,"MCO":0.0,"MUS":0.0,"POL":0.0,"PRT":0.0,"SAU":0.0,"TZA":0.0},"IITU":{"USA":99.76,"SGP":0.24},"UIFS":{"USA":98.12,"CHE":1.88},"IHCU":{"USA":100.0},"XSPX":{"USA":99.58,"CHE":0.26,"SGP":0.06,"RUS":0.05,"GBR":0.04},"EXS1":{"DEU":100.0},"XD5S":{"FRA":32.32,"DEU":29.05,"NLD":9.46,"ESP":9.07,"ITA":5.93,"FIN":3.29,"BEL":3.16,"USA":2.0,"KOR":1.65,"GBR":0.94,"IRL":0.82,"AUT":0.74,"CHN":0.63,"PRT":0.5,"SGP":0.27,"LUX":0.17},"UB89":{"DEU":100.0},"VEVE":{"USA":59.91,"JPN":9.04,"GBR":5.78,"FRA":3.47,"DEU":3.29,"CHE":3.11,"CAN":3.03,"AUS":2.43,"KOR":1.93,"NLD":1.12,"HKG":1.06,"ESP":1.03,"SWE":0.96,"ITA":0.7,"DNK":0.58,"SGP":0.53,"FIN":0.4,"BEL":0.37,"CHN":0.29,"NOR":0.24,"ISR":0.2,"IRL":0.12,"AUT":0.09,"NZL":0.08,"RUS":0.06,"PRT":0.05,"MAC":0.04,"BRA":0.03,"LUX":0.02,"PNG":0.02,"ARE":0.01,"IDN":0.0,"MEX":0.0,"TWN":0.0},"EMIM":{"CHN":27.91,"KOR":15.53,"TWN":13.15,"IND":9.14,"BRA":5.96,"ZAF":5.63,"RUS":3.34,"MEX":3.21,"THA":2.72,"MYS":2.59,"IDN":2.0,"POL":1.2,"CHL":1.18,"HKG":0.94,"PHL":0.93,"QAT":0.91,"ARE":0.65,"TUR":0.64,"COL":0.44,"PER":0.34,"GRC":0.33,"HUN":0.29,"GBR":0.23,"CZE":0.2,"USA":0.2,"PAK":0.13,"EGY":0.12,"LUX":0.05,"MLT":0.02,"SGP":0.02,"CYP":0.01},"VJPN":{"JPN":100.0},"HMJP":{"JPN":100.0},"CU31":{"USA":100.0},"ISXF":{"GBR":48.14,"USA":15.6,"NLD":12.29,"FRA":10.39,"AUS":2.03,"BEL":1.6,"ESP":1.53,"MEX":1.47,"DEU":1.44,"ITA":1.29,"DNK":0.91,"NOR":0.88,"SWE":0.79,"JPN":0.65,"IRL":0.3,"NZL":0.29,"CAN":0.26,"CYM":0.15,"HKG":0.0,"SGP":0.0},"SJPA":{"JPN":100.0},"SWDA":{"USA":62.2,"JPN":8.45,"GBR":5.79,"FRA":3.59,"CAN":3.44,"DEU":3.27,"CHE":3.16,"AUS":2.29,"NLD":1.07,"HKG":1.05,"ESP":1.0,"SWE":0.86,"ITA":0.65,"DNK":0.58,"SGP":0.53,"FIN":0.45,"BEL":0.35,"NOR":0.27,"KOR":0.19,"CHN":0.16,"ISR":0.14,"IRL":0.11,"AUT":0.08,"NZL":0.07,"PRT":0.06,"MAC":0.04,"BRA":0.03,"RUS":0.03,"LUX":0.02,"PNG":0.02,"ARE":0.01,"MEX":0.01,"PHL":0.01},"IEX5":{"FRA":18.98,"NLD":18.38,"USA":16.99,"DEU":10.79,"GBR":10.44,"ESP":4.28,"ITA":4.12,"SWE":2.7,"AUS":2.61,"BEL":1.93,"AUT":1.07,"MEX":1.01,"CHE":0.89,"DNK":0.87,"IRL":0.87,"SGP":0.65,"LUX":0.57,"CZE":0.47,"FIN":0.35,"CAN":0.34,"PAN":0.28,"PRT":0.25,"JEY":0.22,"BRA":0.18,"CHN":0.17,"HKG":0.16,"BMU":0.14,"HUN":0.14,"JPN":0.14},"HMEU":{"GBR":26.21,"FRA":16.47,"DEU":15.0,"CHE":13.73,"NLD":4.81,"ESP":4.62,"SWE":3.96,"ITA":2.99,"DNK":2.66,"USA":2.13,"FIN":2.03,"BEL":1.61,"NOR":1.24,"KOR":0.86,"IRL":0.42,"AUT":0.38,"CHN":0.32,"PRT":0.25,"SGP":0.14,"LUX":0.09,"ARE":0.05,"MEX":0.03},"IGUS":{"USA":99.55,"CHE":0.26,"RUS":0.06,"SGP":0.05,"GBR":0.04,"IRL":0.04},"IS15":{"GBR":43.55,"NLD":13.42,"USA":13.15,"FRA":7.06,"AUS":4.79,"SWE":4.37,"DEU":4.26,"ITA":2.7,"ESP":1.67,"CAN":1.49,"CHE":1.19,"NZL":0.58,"MEX":0.47,"FIN":0.35,"NOR":0.35,"VGB":0.34,"IRL":0.24,"HKG":0.01,"SGP":0.01},"SUKC":{"GBR":44.53,"NLD":14.31,"USA":13.46,"FRA":6.96,"DEU":4.15,"SWE":4.06,"AUS":3.92,"ITA":2.15,"ESP":1.49,"CAN":1.47,"CHE":0.96,"NZL":0.71,"MEX":0.47,"VGB":0.35,"NOR":0.33,"DNK":0.28,"FIN":0.27,"BEL":0.11},"SDEU":{"DEU":100.0},"UKCO":{"GBR":56.94,"USA":16.25,"NLD":9.7,"FRA":4.88,"AUS":2.72,"DEU":1.8,"SWE":1.31,"BEL":0.96,"ESP":0.92,"MEX":0.9,"ITA":0.86,"CHE":0.59,"CAN":0.56,"JPN":0.43,"IRL":0.35,"NZL":0.15,"VGB":0.12,"DNK":0.11,"FIN":0.11,"LUX":0.11,"NOR":0.09,"SGP":0.09,"CYM":0.06},"FTAL":{"GBR":90.91,"USA":4.72,"CHE":1.9,"IRL":0.41,"DEU":0.39,"CHN":0.24,"IND":0.16,"JPN":0.16,"ARE":0.14,"RUS":0.09,"FRA":0.08,"MEX":0.08,"EGY":0.06,"KOR":0.06,"TWN":0.05,"HKG":0.04,"NLD":0.04,"SGP":0.04,"ZAF":0.04,"AUS":0.03,"BRA":0.03,"ESP":0.03,"MYS":0.03,"SWE":0.03,"VNM":0.03,"CAN":0.02,"DNK":0.02,"IDN":0.02,"ITA":0.02,"KAZ":0.02,"NOR":0.02,"THA":0.02,"BEL":0.01,"FIN":0.01,"PER":0.01,"PHL":0.01,"ARG":0.0,"AUT":0.0,"BGD":0.0,"CHL":0.0,"CIV":0.0,"COL":0.0,"CUW":0.0,"CYM":0.0,"CYP":0.0,"CZE":0.0,"GHA":0.0,"GRC":0.0,"HUN":0.0,"IRQ":0.0,"ISL":0.0,"ISR":0.0,"KEN":0.0,"KHM":0.0,"LBN":0.0,"LKA":0.0,"LUX":0.0,"MAC":0.0,"MAR":0.0,"MCO":0.0,"MUS":0.0,"NGA":0.0,"NZL":0.0,"PAK":0.0,"POL":0.0,"PRT":0.0,"ROU":0.0,"SAU":0.0,"TUR":0.0,"TZA":0.0,"VGB":0.0,"ZWE":0.0},"CRPS":{"USA":55.49,"GBR":8.66,"NLD":6.71,"FRA":6.48,"CAN":5.16,"DEU":2.66,"JPN":2.41,"AUS":2.37,"ESP":1.41,"ITA":1.3,"SWE":1.18,"CHE":0.93,"MEX":0.64,"BEL":0.59,"HKG":0.59,"SGP":0.35,"DNK":0.32,"CHN":0.26,"AUT":0.24,"CHL":0.22,"IRL":0.22,"NOR":0.2,"NZL":0.2,"ARE":0.16,"FIN":0.15,"KOR":0.14,"LUX":0.13,"IND":0.12,"PER":0.1,"THA":0.08,"CZE":0.05,"OMN":0.05,"PRT":0.05,"COL":0.04,"CYM":0.04,"ISL":0.04,"ISR":0.03,"PHL":0.03,"VGB":0.03,"JEY":0.02,"PAN":0.02,"POL":0.02,"QAT":0.02,"SAU":0.02,"BRA":0.01,"BRB":0.01,"HUN":0.01,"LBR":0.01,"LIE":0.01},"MVUS":{"USA":98.2,"CHE":1.2,"GBR":0.6},"IUQF":{"USA":99.63,"GBR":0.21,"RUS":0.14,"CHE":0.02},"IUMF":{"USA":99.34,"BRA":0.21,"SGP":0.19,"GBR":0.18,"SWE":0.08},"IBCX":{"FRA":23.71,"USA":18.22,"NLD":17.67,"GBR":10.57,"DEU":7.49,"ITA":5.0,"ESP":4.13,"CHE":2.33,"AUS":2.26,"SWE":2.24,"BEL":1.97,"NOR":1.1,"JPN":0.54,"MEX":0.44,"DNK":0.42,"SGP":0.39,"FIN":0.38,"AUT":0.36,"CAN":0.31,"JEY":0.22,"HKG":0.17,"CYP":0.05,"LUX":0.04},"CPJ1":{"AUS":56.38,"HKG":25.97,"SGP":11.58,"NZL":1.83,"CHN":1.61,"MAC":0.95,"USA":0.83,"PNG":0.53,"PHL":0.31},"SE15":{"FRA":18.24,"NLD":16.75,"USA":14.84,"GBR":10.73,"DEU":8.76,"ESP":4.62,"SWE":4.51,"ITA":4.34,"AUS":3.3,"CHE":1.95,"BEL":1.82,"NOR":1.43,"DNK":1.36,"AUT":0.93,"FIN":0.88,"CAN":0.84,"IRL":0.72,"JPN":0.67,"LUX":0.57,"SGP":0.52,"MEX":0.49,"NZL":0.31,"CZE":0.27,"CHN":0.16,"PRT":0.16,"JEY":0.14,"PAN":0.13,"ISL":0.12,"HKG":0.11,"POL":0.11,"BMU":0.06,"BRA":0.06,"HUN":0.06,"VGB":0.02},"CU71":{"USA":100.0,"AUS":0.0,"CAN":0.0},"IGLS":{"GBR":100.0,"AUS":0.0,"HKG":0.0,"NLD":0.0,"SGP":0.0,"USA":0.0},"IBTS":{"USA":100.0},"IBGS":{"ITA":33.34,"FRA":29.72,"DEU":26.07,"ESP":10.87,"NLD":0.0,"SWE":0.0,"USA":0.0},"IBGM":{"FRA":27.35,"ESP":24.67,"DEU":23.52,"ITA":17.33,"NLD":7.13,"SWE":0.0,"USA":0.0},"IBTM":{"USA":100.0},"IBGL":{"FRA":29.01,"DEU":26.81,"ITA":24.36,"ESP":11.62,"NLD":8.19},"SEGA":{"FRA":25.36,"ITA":21.94,"DEU":16.82,"ESP":14.4,"BEL":5.94,"NLD":5.07,"AUT":3.64,"PRT":2.18,"IRL":1.92,"FIN":1.53,"SVK":0.53,"SVN":0.4,"LTU":0.09,"LUX":0.09,"LVA":0.07,"SWE":0.01,"USA":0.0},"IEBC":{"FRA":20.53,"USA":17.74,"NLD":16.54,"GBR":10.08,"DEU":8.62,"ESP":4.64,"ITA":4.53,"SWE":3.11,"AUS":2.82,"BEL":2.05,"CHE":1.65,"DNK":0.89,"AUT":0.81,"LUX":0.79,"NOR":0.68,"IRL":0.65,"FIN":0.63,"CAN":0.61,"JPN":0.55,"MEX":0.39,"SGP":0.27,"CZE":0.26,"NZL":0.22,"HKG":0.18,"PRT":0.14,"JEY":0.12,"POL":0.11,"CHN":0.07,"ISL":0.07,"PAN":0.06,"VGB":0.06,"BMU":0.04,"BRA":0.04,"HUN":0.04,"CYP":0.03},"EEXF":{"FRA":19.29,"NLD":19.27,"USA":19.14,"GBR":10.04,"DEU":9.55,"ITA":4.64,"ESP":3.93,"BEL":2.58,"AUS":2.25,"SWE":2.11,"AUT":0.86,"CHE":0.84,"DNK":0.69,"IRL":0.66,"MEX":0.66,"LUX":0.65,"CZE":0.43,"CAN":0.41,"SGP":0.38,"FIN":0.25,"HKG":0.24,"PRT":0.19,"JEY":0.18,"PAN":0.14,"JPN":0.13,"VGB":0.09,"BMU":0.08,"BRA":0.08,"NZL":0.08,"HUN":0.07,"CYP":0.06,"POL":0.04},"SAAA":{"USA":20.12,"DEU":20.1,"GBR":10.01,"FRA":10.0,"BEL":7.37,"AUS":6.33,"NLD":6.2,"CAN":6.17,"AUT":4.53,"DNK":1.88,"FIN":1.87,"CHE":1.38,"SGP":1.3,"SWE":1.13,"NOR":0.72,"NZL":0.65,"LUX":0.13,"HKG":0.12},"IBGX":{"DEU":28.32,"ITA":25.89,"FRA":20.47,"ESP":19.09,"NLD":6.23,"SWE":0.0,"USA":0.0},"XSX6":{"GBR":26.05,"FRA":16.45,"DEU":14.75,"CHE":13.48,"NLD":4.92,"ESP":4.62,"SWE":4.45,"ITA":3.12,"DNK":2.8,"USA":2.17,"FIN":1.8,"BEL":1.71,"NOR":1.13,"KOR":0.86,"IRL":0.45,"AUT":0.44,"PRT":0.27,"RUS":0.17,"SGP":0.14,"LUX":0.09,"CZE":0.08,"ARE":0.06},"LQDE":{"USA":84.89,"GBR":6.29,"NLD":2.46,"JPN":1.69,"CAN":1.68,"AUS":0.89,"ESP":0.61,"FRA":0.57,"DEU":0.41,"NOR":0.28,"CHE":0.22},"SLXX":{"GBR":45.0,"USA":21.26,"NLD":12.68,"FRA":7.14,"AUS":2.99,"SWE":2.18,"BEL":1.51,"DEU":1.46,"ESP":1.44,"MEX":1.11,"CHE":0.78,"NOR":0.7,"DNK":0.69,"ITA":0.31,"CAN":0.26,"LUX":0.22,"CYM":0.13,"IRL":0.13,"HKG":0.0,"SGP":0.0},"IGLT":{"GBR":99.99,"AUS":0.01,"HKG":0.0,"NLD":0.0,"SGP":0.0,"USA":0.0},"XASX":{"GBR":90.6,"USA":4.76,"CHE":1.99,"IRL":0.4,"DEU":0.38,"JPN":0.23,"CHN":0.19,"IND":0.18,"ARE":0.13,"FRA":0.1,"MEX":0.1,"RUS":0.08,"KOR":0.07,"TWN":0.07,"EGY":0.06,"ISR":0.06,"HKG":0.05,"SGP":0.05,"VNM":0.05,"AUS":0.04,"NLD":0.04,"SWE":0.04,"BRA":0.03,"ESP":0.03,"IDN":0.03,"THA":0.03,"ZAF":0.03,"CAN":0.02,"DNK":0.02,"ITA":0.02,"MYS":0.02,"AUT":0.01,"BEL":0.01,"FIN":0.01,"LKA":0.01,"NOR":0.01,"NZL":0.01,"PHL":0.01,"ARG":0.0,"BGD":0.0,"BMU":0.0,"CHL":0.0,"CIV":0.0,"COL":0.0,"CYP":0.0,"CZE":0.0,"GRC":0.0,"HUN":0.0,"ISL":0.0,"KAZ":0.0,"KEN":0.0,"KHM":0.0,"LBN":0.0,"LIE":0.0,"LUX":0.0,"MAC":0.0,"MAR":0.0,"MCO":0.0,"MUS":0.0,"NGA":0.0,"PAK":0.0,"PER":0.0,"POL":0.0,"PRT":0.0,"ROU":0.0,"SAU":0.0,"TUR":0.0,"VGB":0.0},"ICOV":{"FRA":24.25,"DEU":13.8,"ESP":12.98,"ITA":6.35,"GBR":6.12,"NLD":5.8,"CAN":5.23,"NOR":4.79,"SWE":4.31,"AUS":3.21,"AUT":3.05,"FIN":3.04,"BEL":2.05,"DNK":1.37,"NZL":0.91,"PRT":0.76,"CHE":0.74,"SGP":0.6,"IRL":0.37,"POL":0.26,"USA":0.0},"IBGE":{"ITA":28.54,"DEU":20.24,"ESP":15.13,"FRA":11.91,"NLD":7.42,"BEL":6.21,"AUT":4.81,"PRT":2.2,"IRL":1.83,"FIN":1.25,"SVN":0.43,"SWE":0.02,"USA":0.0},"IGLO":{"USA":43.41,"JPN":22.65,"FRA":10.21,"ITA":8.64,"DEU":6.79,"GBR":6.32,"CAN":1.98},"IBTL":{"USA":100.0},"VVAL":{"USA":59.3,"JPN":9.18,"GBR":6.83,"FRA":4.03,"KOR":3.61,"CAN":3.19,"DEU":2.49,"ITA":1.95,"ESP":1.7,"NLD":1.18,"CHE":1.1,"AUT":0.71,"HKG":0.71,"SWE":0.71,"PRI":0.42,"AUS":0.39,"NOR":0.37,"CHN":0.36,"BEL":0.34,"LUX":0.27,"DNK":0.25,"IRL":0.25,"FIN":0.18,"SGP":0.18,"NZL":0.16,"PER":0.08,"IDN":0.07},"VMVL":{"USA":50.0,"GBR":9.12,"JPN":7.57,"CAN":5.82,"AUS":4.71,"DEU":2.85,"CHE":2.68,"IND":2.43,"HKG":1.97,"KOR":1.64,"FRA":1.63,"CHN":1.52,"SWE":1.33,"TWN":1.01,"ESP":0.84,"SGP":0.8,"MEX":0.68,"BRA":0.61,"DNK":0.57,"BEL":0.36,"FIN":0.34,"ISR":0.31,"IDN":0.3,"CHL":0.28,"ITA":0.23,"AUT":0.2,"NOR":0.1,"NZL":0.09},"VLIQ":{"USA":57.65,"JPN":11.11,"GBR":5.95,"FRA":4.96,"CAN":3.86,"DEU":2.52,"CHE":2.37,"HKG":1.36,"KOR":1.11,"AUT":1.08,"DNK":0.95,"SWE":0.88,"BEL":0.87,"SGP":0.85,"AUS":0.64,"CHN":0.59,"NZL":0.57,"ESP":0.5,"IRL":0.36,"NOR":0.36,"ITA":0.34,"NLD":0.34,"FIN":0.16,"IND":0.15,"PRT":0.15,"PRI":0.11,"BRA":0.1,"PER":0.06,"IDN":0.03,"MCO":0.01},"VMOM":{"USA":59.15,"JPN":9.05,"GBR":7.06,"CAN":3.49,"DEU":3.06,"FRA":2.99,"KOR":2.32,"ITA":1.87,"AUS":1.65,"NLD":0.93,"DNK":0.92,"SWE":0.81,"HKG":0.78,"CHE":0.77,"CHN":0.71,"FIN":0.71,"SGP":0.62,"ESP":0.58,"NOR":0.54,"AUT":0.49,"BEL":0.36,"IRL":0.36,"NZL":0.25,"PRI":0.21,"RUS":0.13,"PRT":0.12,"BRA":0.05,"MAC":0.05},"DBXM":{},"XEUM":{"GBR":24.92,"FRA":14.42,"DEU":13.39,"CHE":11.5,"SWE":5.64,"DNK":4.52,"FIN":3.65,"USA":3.62,"NLD":3.03,"ESP":2.95,"ITA":2.52,"NOR":2.35,"BEL":2.18,"IRL":2.0,"AUT":1.16,"PRT":0.72,"SGP":0.65,"LUX":0.42,"ARE":0.24,"MEX":0.12},"JPXX":{"JPN":100.0},"XDEV":{"USA":39.54,"JPN":27.79,"GBR":8.47,"FRA":7.17,"DEU":3.65,"HKG":2.5,"NLD":1.7,"ESP":1.55,"ITA":1.48,"CAN":1.27,"CHE":1.2,"SGP":0.88,"ISR":0.69,"AUS":0.56,"NOR":0.43,"CHN":0.27,"BEL":0.23,"DNK":0.23,"AUT":0.18,"SWE":0.09,"PRT":0.08,"IRL":0.06},"XCS2":{"AUS":100.0},"XGIG":{"USA":43.26,"GBR":28.94,"FRA":9.44,"ITA":5.97,"DEU":3.06,"JPN":2.67,"ESP":2.08,"CAN":1.98,"AUS":1.1,"SWE":0.85,"NZL":0.42,"DNK":0.24},"XGSG":{"USA":36.85,"JPN":20.09,"FRA":8.57,"ITA":7.38,"DEU":5.74,"GBR":5.49,"ESP":4.83,"BEL":2.11,"AUS":1.72,"CAN":1.72,"NLD":1.72,"AUT":1.25,"IRL":0.65,"DNK":0.49,"FIN":0.49,"SGP":0.32,"SWE":0.29,"NOR":0.18,"CHE":0.1},"CS1":{"ESP":98.7,"GBR":1.3},"XMEU":{"GBR":26.35,"FRA":16.53,"DEU":14.98,"CHE":13.76,"NLD":4.85,"ESP":4.65,"SWE":3.94,"ITA":3.04,"DNK":2.67,"USA":2.15,"FIN":1.69,"BEL":1.61,"NOR":1.24,"KOR":0.85,"IRL":0.42,"AUT":0.38,"CHN":0.32,"PRT":0.25,"SGP":0.14,"LUX":0.09,"ARE":0.05,"MEX":0.03},"IGLN":{},"CAC":{"FRA":90.53,"NLD":5.14,"USA":1.53,"RUS":1.08,"SGP":0.99,"BEL":0.73},"IEFM":{"FRA":21.88,"GBR":20.46,"DEU":12.97,"NLD":8.52,"CHE":7.83,"SWE":5.05,"NOR":3.82,"ITA":3.7,"FIN":3.51,"KOR":2.97,"BEL":2.23,"ESP":2.08,"DNK":1.94,"IRL":1.16,"USA":0.91,"AUT":0.66,"ARE":0.31},"IEFV":{"GBR":25.07,"FRA":23.9,"DEU":15.68,"CHE":7.83,"NLD":6.46,"ESP":5.46,"USA":3.94,"ITA":3.47,"FIN":2.12,"DNK":1.71,"NOR":1.14,"CHN":0.86,"BEL":0.65,"SGP":0.53,"SWE":0.41,"AUT":0.4,"PRT":0.24,"IRL":0.14},"VFEM":{"CHN":32.91,"TWN":13.55,"IND":12.17,"ZAF":7.22,"BRA":7.11,"RUS":3.97,"MEX":3.89,"THA":3.69,"MYS":3.17,"IDN":2.13,"POL":1.46,"PHL":1.34,"CHL":1.26,"QAT":1.1,"ARE":0.98,"HKG":0.85,"TUR":0.61,"COL":0.51,"GRC":0.39,"PER":0.38,"HUN":0.36,"CZE":0.22,"GBR":0.22,"EGY":0.2,"USA":0.14,"PAK":0.07,"MLT":0.02,"SGP":0.02,"UKR":0.02,"DEU":0.01,"LUX":0.01},"VWRL":{"USA":54.22,"JPN":8.2,"GBR":5.26,"CHN":3.4,"FRA":3.13,"DEU":2.97,"CHE":2.81,"CAN":2.73,"AUS":2.2,"KOR":1.76,"TWN":1.29,"IND":1.15,"HKG":1.06,"NLD":1.02,"ESP":0.93,"SWE":0.87,"BRA":0.69,"ZAF":0.68,"ITA":0.64,"DNK":0.53,"SGP":0.48,"RUS":0.43,"MEX":0.38,"THA":0.36,"FIN":0.35,"BEL":0.34,"MYS":0.3,"NOR":0.22,"IDN":0.2,"ISR":0.18,"POL":0.13,"CHL":0.12,"PHL":0.12,"IRL":0.11,"QAT":0.11,"ARE":0.1,"AUT":0.09,"NZL":0.07,"TUR":0.06,"COL":0.05,"PRT":0.05,"GRC":0.04,"PER":0.04,"CZE":0.03,"HUN":0.03,"MAC":0.03,"EGY":0.02,"LUX":0.02,"PNG":0.02,"MLT":0.0,"PAK":0.0,"UKR":0.0},"SGIL":{"USA":43.69,"GBR":29.13,"FRA":9.37,"ITA":5.22,"DEU":3.03,"JPN":2.69,"ESP":2.32,"CAN":1.95,"AUS":1.07,"SWE":0.84,"NZL":0.44,"DNK":0.24},"IBCI":{"FRA":46.87,"ITA":26.36,"DEU":15.22,"ESP":11.53,"NLD":0.01,"SWE":0.01,"USA":0.0},"ITPS":{"USA":100.0},"INXG":{"GBR":99.99,"AUS":0.01,"HKG":0.0,"NLD":0.0,"SGP":0.0,"USA":0.0},"ITPG":{"USA":100.0},"UB0F":{"FRA":32.11,"DEU":29.11,"NLD":9.46,"ESP":9.11,"ITA":6.06,"FIN":3.29,"BEL":3.14,"USA":2.01,"KOR":1.64,"GBR":0.94,"IRL":0.81,"AUT":0.75,"CHN":0.62,"PRT":0.5,"SGP":0.27,"LUX":0.17},"UB0E":{"FRA":32.11,"DEU":29.11,"NLD":9.46,"ESP":9.11,"ITA":6.06,"FIN":3.29,"BEL":3.14,"USA":2.01,"KOR":1.64,"GBR":0.94,"IRL":0.81,"AUT":0.75,"CHN":0.62,"PRT":0.5,"SGP":0.27,"LUX":0.17},"SGLD":{},"DHS":{"USA":100.0},"EEI":{"GBR":33.68,"FRA":16.52,"DEU":10.35,"ESP":8.27,"CHE":7.5,"ITA":5.76,"BEL":4.09,"SWE":4.07,"FIN":3.28,"NLD":2.48,"NOR":2.03,"PRT":1.07,"DNK":0.61,"AUT":0.22,"USA":0.04,"TUR":0.02,"IRL":0.01,"ZAF":0.01},"VHYL":{"USA":37.24,"GBR":9.97,"JPN":6.31,"CHE":5.4,"CAN":4.25,"DEU":4.09,"FRA":4.03,"AUS":3.96,"CHN":3.21,"TWN":2.76,"KOR":1.94,"ESP":1.84,"NLD":1.68,"SWE":1.21,"HKG":1.18,"ITA":1.06,"BRA":1.03,"SGP":0.87,"ZAF":0.78,"FIN":0.77,"RUS":0.77,"DNK":0.69,"BEL":0.61,"IND":0.52,"MYS":0.49,"NOR":0.48,"THA":0.48,"MEX":0.35,"QAT":0.24,"IDN":0.23,"ARE":0.18,"AUT":0.15,"ISR":0.14,"POL":0.14,"CHL":0.13,"NZL":0.11,"PRT":0.1,"TUR":0.09,"MAC":0.08,"COL":0.07,"PER":0.07,"CZE":0.05,"IRL":0.05,"GRC":0.04,"LUX":0.04,"PHL":0.04,"HUN":0.02,"EGY":0.01,"PAK":0.01},"WUKD":{"GBR":99.81,"TUR":0.13,"ZAF":0.05},"XMJP":{"JPN":100.0},"HMUS":{"USA":99.26,"CHE":0.24,"GBR":0.12,"CAN":0.08,"CHN":0.07,"BRA":0.05,"IRL":0.05,"RUS":0.05,"SGP":0.05,"SWE":0.03},"FINW":{"USA":50.06,"CAN":8.45,"GBR":7.06,"JPN":6.06,"AUS":5.55,"CHE":4.14,"DEU":2.83,"FRA":2.72,"HKG":2.37,"ESP":2.34,"SWE":1.81,"ITA":1.39,"NLD":1.39,"SGP":1.3,"BEL":0.53,"DNK":0.36,"NOR":0.34,"FIN":0.33,"ISR":0.29,"CHN":0.26,"AUT":0.24,"IRL":0.18},"LEMB":{},"UKDV":{"GBR":99.96,"USA":0.04},"SPY4":{"USA":99.62,"IRL":0.22,"GBR":0.16},"MVOL":{"USA":63.26,"JPN":13.27,"CHE":6.41,"CAN":4.11,"HKG":3.94,"DNK":1.47,"SGP":1.45,"GBR":1.38,"FRA":1.1,"ITA":0.58,"BEL":0.56,"DEU":0.45,"ISR":0.41,"IRL":0.37,"FIN":0.28,"CHN":0.26,"NZL":0.23,"ESP":0.2,"AUS":0.19,"NLD":0.08},"XDWT":{"USA":86.47,"JPN":5.45,"DEU":2.29,"KOR":0.96,"FRA":0.8,"CAN":0.78,"CHN":0.61,"SWE":0.53,"ESP":0.51,"FIN":0.39,"SGP":0.37,"GBR":0.28,"BRA":0.18,"AUS":0.13,"CHE":0.12,"ISR":0.09,"HKG":0.04},"R2SC":{"USA":99.02,"GBR":0.3,"PRI":0.21,"AGO":0.06,"CAN":0.06,"ISR":0.05,"MCO":0.05,"PER":0.05,"SGP":0.05,"TWN":0.05,"IRL":0.03,"BRA":0.02,"CZE":0.02,"MHL":0.02,"HKG":0.01},"IWFS":{"USA":37.59,"JPN":20.2,"GBR":6.39,"CAN":5.47,"FRA":4.31,"AUS":4.19,"DEU":3.61,"CHE":2.46,"SWE":1.83,"SGP":1.76,"HKG":1.7,"DNK":1.13,"ISR":1.08,"ITA":0.95,"FIN":0.92,"NOR":0.86,"NZL":0.85,"ESP":0.77,"NLD":0.67,"BEL":0.65,"CHN":0.62,"IRL":0.56,"AUT":0.43,"PRT":0.21,"LUX":0.16,"BRA":0.13,"MAC":0.13,"ARE":0.1,"RUS":0.1,"PHL":0.08,"MEX":0.07},"IWFM":{"USA":79.04,"JPN":7.09,"FRA":2.66,"HKG":1.67,"GBR":1.24,"SGP":1.17,"AUS":1.14,"NLD":0.96,"DEU":0.95,"CAN":0.57,"NOR":0.47,"KOR":0.41,"SWE":0.41,"CHE":0.39,"FIN":0.38,"ESP":0.26,"ITA":0.23,"DNK":0.17,"ISR":0.17,"BEL":0.14,"BRA":0.12,"NZL":0.11,"IRL":0.09,"ARE":0.04,"CHN":0.04,"MAC":0.04,"PHL":0.04},"IWFV":{"USA":39.62,"JPN":27.87,"GBR":8.44,"FRA":7.18,"DEU":3.65,"HKG":2.42,"NLD":1.67,"ESP":1.54,"ITA":1.45,"CAN":1.29,"CHE":1.19,"SGP":0.85,"ISR":0.7,"AUS":0.55,"NOR":0.44,"CHN":0.25,"BEL":0.23,"DNK":0.23,"AUT":0.19,"SWE":0.09,"PRT":0.08,"IRL":0.06},"IWFQ":{"USA":63.41,"GBR":8.75,"HKG":4.91,"CHE":4.02,"JPN":2.94,"AUS":2.78,"FRA":2.28,"DEU":2.09,"DNK":1.81,"CAN":1.47,"NLD":1.24,"SWE":1.07,"ESP":1.02,"FIN":0.89,"SGP":0.56,"NZL":0.18,"ITA":0.13,"MAC":0.13,"PRT":0.12,"BEL":0.09,"AUT":0.06,"NOR":0.06},"IWDG":{"USA":62.2,"JPN":8.45,"GBR":5.79,"FRA":3.59,"CAN":3.44,"DEU":3.27,"CHE":3.16,"AUS":2.29,"NLD":1.07,"HKG":1.05,"ESP":1.0,"SWE":0.86,"ITA":0.65,"DNK":0.58,"SGP":0.53,"FIN":0.45,"BEL":0.35,"NOR":0.27,"KOR":0.19,"CHN":0.16,"ISR":0.14,"IRL":0.11,"AUT":0.08,"NZL":0.07,"PRT":0.06,"MAC":0.04,"BRA":0.03,"RUS":0.03,"LUX":0.02,"PNG":0.02,"ARE":0.01,"MEX":0.01,"PHL":0.01},"WLDL":{"USA":62.24,"JPN":8.32,"GBR":5.69,"FRA":3.56,"CAN":3.42,"DEU":3.32,"CHE":3.15,"AUS":2.34,"NLD":1.12,"HKG":1.05,"ESP":1.01,"SWE":0.93,"ITA":0.65,"DNK":0.6,"SGP":0.53,"FIN":0.37,"BEL":0.36,"NOR":0.25,"KOR":0.2,"CHN":0.19,"ISR":0.16,"IRL":0.12,"AUT":0.08,"NZL":0.08,"PRT":0.06,"MAC":0.04,"BRA":0.03,"RUS":0.03,"LUX":0.02,"PNG":0.02,"ARE":0.01,"MEX":0.01,"PHL":0.01},"CMFP":{},"XXSC":{"GBR":31.79,"DEU":10.33,"SWE":9.45,"CHE":7.52,"ITA":6.76,"FRA":6.46,"ESP":4.68,"NLD":4.02,"DNK":3.39,"NOR":3.39,"BEL":3.26,"FIN":2.42,"AUT":1.9,"USA":1.28,"IRL":1.18,"PRT":0.79,"BRA":0.24,"EGY":0.2,"MLT":0.2,"LUX":0.18,"IND":0.16,"CAN":0.12,"ISR":0.12,"IRQ":0.09,"KAZ":0.06},"HLTG":{"USA":70.71,"CHE":7.75,"JPN":5.26,"GBR":4.1,"DEU":3.11,"FRA":2.71,"DNK":2.23,"AUS":1.87,"NLD":0.79,"ISR":0.42,"BEL":0.22,"CAN":0.22,"NZL":0.19,"ESP":0.17,"ARE":0.1,"FIN":0.07,"ITA":0.07},"XS6R":{"GBR":22.19,"ESP":21.23,"ITA":16.86,"FRA":16.08,"DEU":13.61,"FIN":3.1,"DNK":3.0,"PRT":2.78,"CZE":1.15},"IAEX":{"NLD":58.34,"GBR":20.19,"KOR":12.97,"FRA":4.57,"USA":3.22,"BEL":0.72},"XSKR":{"GBR":29.59,"DEU":19.44,"ESP":14.55,"FRA":12.18,"SWE":5.7,"CHE":4.96,"NOR":4.54,"NLD":2.95,"ITA":2.57,"FIN":2.24,"BEL":1.26},"XD3E":{"DEU":29.22,"FRA":22.47,"NLD":18.99,"ESP":10.0,"BEL":8.18,"ITA":5.81,"FIN":3.65,"PRT":1.11,"AUT":0.58},"XSPR":{"GBR":51.43,"CHE":13.78,"FIN":11.29,"USA":6.95,"SWE":5.82,"ITA":2.82,"NOR":2.71,"AUT":1.8,"DEU":0.95,"FRA":0.84,"RUS":0.82,"MEX":0.77},"XS3R":{"CHE":36.3,"GBR":17.29,"FRA":15.94,"BEL":13.18,"NLD":6.14,"IRL":3.85,"DNK":3.1,"NOR":2.92,"ITA":0.74,"ESP":0.53},"XSDR":{"CHE":33.24,"GBR":17.58,"DEU":12.9,"DNK":11.79,"FRA":11.74,"USA":5.16,"NLD":3.26,"BEL":1.48,"SWE":0.98,"ESP":0.67,"ARE":0.41,"FIN":0.3,"ITA":0.27,"IRL":0.19,"SGP":0.0},"EUDV":{"FRA":30.8,"DEU":22.35,"ITA":15.34,"ESP":9.59,"NLD":9.45,"PRT":5.08,"BEL":4.37,"FIN":3.02},"UC93":{"CHE":100.0},"XSER":{"GBR":31.25,"FRA":30.84,"ITA":10.53,"NOR":7.55,"ESP":5.87,"DNK":3.01,"RUS":3.0,"FIN":2.35,"PRT":2.09,"AUT":1.59,"SWE":1.34,"BRA":0.59},"UC94":{"CHE":100.0},"ZIEG":{"DEU":26.95,"CHE":23.83,"FRA":20.21,"NLD":7.52,"DNK":5.26,"SWE":4.76,"FIN":4.26,"ESP":1.94,"NOR":1.71,"GBR":0.91,"BEL":0.88,"PRT":0.71,"AUT":0.5,"LUX":0.37,"ITA":0.2},"DBXS":{},"XS8R":{"DEU":38.92,"FRA":15.75,"KOR":14.99,"SWE":8.79,"FIN":6.92,"GBR":3.54,"SGP":2.99,"CHE":2.4,"USA":2.34,"NLD":1.36,"AUT":1.16,"DNK":0.85},"XMUS":{"USA":99.25,"CHE":0.24,"GBR":0.12,"CAN":0.08,"CHN":0.08,"BRA":0.06,"SGP":0.06,"RUS":0.05,"IRL":0.03,"SWE":0.03},"EQQQ":{"USA":97.75,"CHN":1.4,"GBR":0.36,"BRA":0.17,"KOR":0.16,"SGP":0.16},"HDLG":{"USA":100.0},"XS7R":{},"CNX1":{"USA":97.77,"CHN":1.39,"GBR":0.36,"BRA":0.17,"KOR":0.16,"SGP":0.15},"CSUK":{"GBR":93.22,"USA":3.9,"CHE":2.26,"DEU":0.34,"ARE":0.19,"MEX":0.09},"CMB1":{"ITA":82.0,"USA":7.72,"GBR":5.24,"SGP":3.13,"NLD":1.91},"CIND":{"USA":100.0},"HMCX":{"GBR":88.97,"USA":3.37,"JPN":0.82,"CHN":0.75,"IND":0.73,"CHE":0.64,"IRL":0.52,"RUS":0.46,"ISR":0.38,"DEU":0.33,"FRA":0.33,"EGY":0.32,"VNM":0.24,"KOR":0.22,"TWN":0.2,"HKG":0.15,"NLD":0.15,"BRA":0.14,"CIV":0.14,"ZAF":0.12,"ESP":0.08,"IDN":0.08,"MEX":0.08,"SGP":0.08,"AUS":0.07,"DNK":0.07,"SWE":0.07,"CAN":0.06,"THA":0.06,"ITA":0.05,"NOR":0.05,"BEL":0.03,"PER":0.03,"CHL":0.02,"FIN":0.02,"MYS":0.02,"PHL":0.02,"AUT":0.01,"CZE":0.01,"HUN":0.01,"KAZ":0.01,"KEN":0.01,"MAC":0.01,"NGA":0.01,"NZL":0.01,"PAK":0.01,"ROU":0.01,"TUR":0.01,"VGB":0.01,"ARE":0.0,"ARG":0.0,"COL":0.0,"CYM":0.0,"CYP":0.0,"GHA":0.0,"GRC":0.0,"IRQ":0.0,"ISL":0.0,"KHM":0.0,"LBN":0.0,"LKA":0.0,"LUX":0.0,"MAR":0.0,"MCO":0.0,"MUS":0.0,"POL":0.0,"PRT":0.0,"SAU":0.0,"TZA":0.0},"EQGB":{"USA":97.75,"CHN":1.4,"GBR":0.36,"BRA":0.17,"KOR":0.16,"SGP":0.16},"CRBL":{},"L6EW":{"GBR":26.72,"FRA":14.57,"DEU":13.0,"CHE":8.3,"SWE":7.06,"NLD":4.52,"ESP":4.4,"ITA":4.37,"DNK":4.15,"FIN":2.66,"BEL":2.35,"NOR":2.05,"USA":1.51,"IRL":1.35,"AUT":1.14,"PRT":0.67,"CZE":0.34,"ARE":0.18,"LUX":0.18,"RUS":0.17,"MLT":0.16,"SGP":0.16},"L250":{"GBR":88.91,"USA":3.13,"CHE":1.14,"JPN":0.82,"IND":0.79,"CHN":0.78,"IRL":0.56,"RUS":0.49,"DEU":0.37,"FRA":0.35,"EGY":0.32,"VNM":0.24,"KOR":0.22,"TWN":0.21,"NLD":0.17,"HKG":0.16,"BRA":0.15,"ZAF":0.13,"MEX":0.09,"DNK":0.08,"ESP":0.08,"IDN":0.08,"SGP":0.08,"AUS":0.07,"SWE":0.07,"CAN":0.06,"ITA":0.06,"NOR":0.06,"THA":0.06,"BEL":0.03,"PER":0.03,"CHL":0.02,"FIN":0.02,"MYS":0.02,"PHL":0.02,"AUT":0.01,"CZE":0.01,"HUN":0.01,"ISR":0.01,"KAZ":0.01,"KEN":0.01,"MAC":0.01,"NGA":0.01,"NZL":0.01,"PAK":0.01,"ROU":0.01,"TUR":0.01,"VGB":0.01,"ARE":0.0,"ARG":0.0,"COL":0.0,"CYM":0.0,"CYP":0.0,"GHA":0.0,"GRC":0.0,"IRQ":0.0,"ISL":0.0,"KHM":0.0,"LBN":0.0,"LKA":0.0,"LUX":0.0,"MAR":0.0,"MCO":0.0,"MUS":0.0,"POL":0.0,"PRT":0.0,"SAU":0.0,"TZA":0.0},"ZHYG":{"USA":57.45,"GBR":8.25,"DEU":7.87,"ITA":7.39,"FRA":6.09,"NLD":5.48,"SWE":1.46,"ESP":1.28,"IRL":1.17,"JPN":0.9,"FIN":0.86,"CAN":0.51,"PRT":0.27,"AUS":0.26,"CHN":0.25,"CYM":0.25,"LUX":0.14,"DNK":0.13},"DXGP":{"DEU":100.0},"XRSS":{"USA":99.22,"CHN":0.39,"GBR":0.13,"IRL":0.11,"PRI":0.07,"IND":0.06,"GHA":0.03,"LUX":0.0},"USDV":{"USA":99.15,"CHE":0.85},"HCAN":{"CAN":100.0},"EUN":{"GBR":31.08,"CHE":20.14,"FRA":17.93,"DEU":14.47,"NLD":4.87,"ESP":3.79,"ITA":2.08,"KOR":1.95,"DNK":1.94,"BEL":1.75},"IMIB":{"ITA":82.02,"USA":7.71,"GBR":5.24,"SGP":3.12,"NLD":1.91},"UC44":{"USA":56.3,"JPN":8.69,"FRA":5.99,"DEU":5.12,"CAN":4.45,"GBR":3.9,"CHE":3.48,"AUS":3.38,"DNK":1.43,"ESP":1.31,"SGP":0.76,"HKG":0.75,"ITA":0.74,"NOR":0.72,"SWE":0.57,"FIN":0.46,"BEL":0.42,"NLD":0.28,"IRL":0.25,"PRT":0.24,"CHN":0.18,"NZL":0.15,"AUT":0.14,"RUS":0.14,"ISR":0.08,"LUX":0.08},"DFE":{"GBR":26.19,"SWE":14.96,"ITA":10.67,"DEU":8.1,"NOR":6.87,"FRA":6.25,"ESP":5.51,"FIN":5.08,"NLD":4.04,"PRT":3.13,"DNK":3.04,"CHE":2.64,"BEL":1.91,"AUT":0.75,"IRL":0.39,"USA":0.24,"TUR":0.15,"ZAF":0.07},"VZLD":{},"PHAU":{},"GBSP":{},"PSRU":{"GBR":92.93,"USA":3.45,"CHE":2.9,"IRL":0.38,"DEU":0.35},"PSRE":{"GBR":30.16,"FRA":16.44,"DEU":15.1,"CHE":10.37,"ESP":6.11,"ITA":5.13,"NLD":4.2,"SWE":4.06,"FIN":1.46,"USA":1.44,"NOR":1.41,"DNK":1.31,"BEL":1.21,"AUT":0.43,"PRT":0.35,"IRL":0.28,"RUS":0.17,"LUX":0.15,"KOR":0.13,"SGP":0.06,"BRA":0.04},"PSRF":{"USA":98.95,"GBR":0.37,"CHE":0.27,"CHN":0.2,"SGP":0.09,"SWE":0.05,"PRI":0.03,"IND":0.02,"BRA":0.01},"IEUR":{"FRA":33.82,"DEU":33.19,"NLD":10.09,"ESP":9.13,"ITA":5.48,"FIN":2.67,"BEL":2.66,"KOR":2.38,"USA":0.57},"IEUT":{"GBR":37.43,"FRA":20.98,"DEU":18.28,"NLD":6.47,"ESP":6.08,"ITA":3.65,"USA":1.96,"KOR":1.59,"BEL":1.35,"FIN":1.15,"CHE":1.04},"CSIL":{},"GBRE":{"USA":59.36,"JPN":11.09,"AUS":4.66,"FRA":4.46,"GBR":4.33,"SGP":3.45,"DEU":2.83,"HKG":2.59,"CAN":1.21,"CHE":0.93,"ZAF":0.91,"SWE":0.89,"PHL":0.74,"ESP":0.73,"AUT":0.45,"MEX":0.38,"THA":0.3,"BEL":0.24,"BRA":0.17,"ITA":0.17,"NLD":0.13},"XMJG":{"JPN":100.0},"HMXJ":{"AUS":56.58,"HKG":25.76,"SGP":11.62,"NZL":1.82,"CHN":1.59,"MAC":0.95,"USA":0.84,"PNG":0.53,"PHL":0.31,"FRA":0.0,"GBR":0.0},"DJSC":{"FRA":26.34,"DEU":23.71,"ITA":11.89,"FIN":7.88,"BEL":7.52,"ESP":7.16,"NLD":6.69,"IRL":2.32,"AUT":2.19,"PRT":1.85,"BRA":0.98,"LUX":0.76,"USA":0.71},"LFAS":{"GBR":91.53,"USA":4.2,"CHE":1.78,"IRL":0.41,"DEU":0.39,"CHN":0.22,"JPN":0.16,"ARE":0.15,"IND":0.15,"FRA":0.09,"MEX":0.09,"RUS":0.09,"KOR":0.06,"EGY":0.05,"NLD":0.05,"SGP":0.05,"TWN":0.05,"HKG":0.04,"VNM":0.04,"AUS":0.03,"BRA":0.03,"ESP":0.03,"MYS":0.03,"SWE":0.03,"ZAF":0.03,"CAN":0.02,"DNK":0.02,"IDN":0.02,"ITA":0.02,"NOR":0.02,"THA":0.02,"BEL":0.01,"FIN":0.01,"KAZ":0.01,"PER":0.01,"PHL":0.01,"ARG":0.0,"AUT":0.0,"BGD":0.0,"BMU":0.0,"CHL":0.0,"CIV":0.0,"COL":0.0,"CUW":0.0,"CYM":0.0,"CYP":0.0,"CZE":0.0,"EST":0.0,"GHA":0.0,"GRC":0.0,"HUN":0.0,"IRQ":0.0,"ISL":0.0,"ISR":0.0,"KEN":0.0,"KHM":0.0,"KWT":0.0,"LBN":0.0,"LKA":0.0,"LUX":0.0,"MAC":0.0,"MAR":0.0,"MCO":0.0,"MUS":0.0,"NGA":0.0,"NZL":0.0,"PAK":0.0,"POL":0.0,"PRT":0.0,"QAT":0.0,"ROU":0.0,"SAU":0.0,"SVN":0.0,"TUR":0.0,"TZA":0.0,"UKR":0.0,"VGB":0.0,"ZWE":0},"DJMC":{"DEU":24.38,"FRA":24.25,"ESP":9.55,"NLD":8.38,"ITA":7.78,"BEL":7.16,"FIN":5.94,"GBR":3.05,"PRT":2.58,"AUT":2.38,"IRL":2.16,"USA":1.21,"LUX":1.19},"IUKD":{"GBR":93.44,"ISR":3.04,"RUS":1.95,"DEU":1.57},"MIDD":{"GBR":89.08,"USA":3.37,"JPN":0.81,"CHN":0.76,"IND":0.73,"CHE":0.64,"IRL":0.52,"RUS":0.46,"ISR":0.38,"DEU":0.34,"FRA":0.33,"EGY":0.32,"VNM":0.25,"KOR":0.22,"TWN":0.2,"HKG":0.15,"NLD":0.15,"BRA":0.14,"ZAF":0.12,"ESP":0.09,"MEX":0.09,"IDN":0.08,"SGP":0.08,"AUS":0.07,"DNK":0.07,"SWE":0.07,"CAN":0.06,"THA":0.06,"ITA":0.05,"NOR":0.05,"BEL":0.03,"PER":0.03,"CHL":0.02,"FIN":0.02,"MYS":0.02,"PHL":0.02,"AUT":0.01,"CZE":0.01,"HUN":0.01,"KAZ":0.01,"KEN":0.01,"MAC":0.01,"NGA":0.01,"NZL":0.01,"PAK":0.01,"ROU":0.01,"TUR":0.01,"VGB":0.01,"ARE":0.0,"ARG":0.0,"COL":0.0,"CYM":0.0,"CYP":0.0,"GHA":0.0,"GRC":0.0,"IRQ":0.0,"ISL":0.0,"KHM":0.0,"LBN":0.0,"LKA":0.0,"LUX":0.0,"MAR":0.0,"MCO":0.0,"MUS":0.0,"POL":0.0,"PRT":0.0,"SAU":0.0,"TZA":0.0},"AGES":{"USA":36.26,"JPN":11.14,"GBR":6.59,"AUS":5.54,"KOR":5.28,"CAN":3.94,"FRA":3.43,"CHE":2.82,"CHN":2.51,"ZAF":2.14,"DEU":2.06,"TWN":1.98,"BRA":1.8,"THA":1.73,"BEL":1.58,"IND":1.32,"NLD":1.28,"ISR":1.2,"ITA":1.17,"SWE":1.1,"NOR":0.83,"NZL":0.82,"DNK":0.78,"SGP":0.42,"CHL":0.4,"ARE":0.39,"AUT":0.39,"HKG":0.39,"COL":0.35,"MYS":0.34},"INAA":{"USA":94.17,"CAN":5.22,"CHE":0.23,"GBR":0.11,"CHN":0.07,"BRA":0.05,"RUS":0.05,"SGP":0.05,"IRL":0.03,"SWE":0.03},"DRDR":{"USA":47.76,"KOR":16.54,"JPN":10.16,"CHN":3.79,"SWE":3.63,"CHE":2.8,"DEU":2.76,"IND":2.53,"FRA":2.3,"BEL":2.27,"DNK":2.22,"NOR":1.19,"ITA":1.17,"IRL":0.87},"ISP6":{"USA":98.78,"PRI":0.5,"GBR":0.37,"CHN":0.19,"CHE":0.16},"IDVY":{"FRA":30.64,"DEU":20.25,"ITA":13.0,"NLD":12.96,"FIN":11.71,"PRT":5.75,"BEL":3.2,"ESP":2.49},"IDJV":{"DEU":34.03,"FRA":32.91,"NLD":11.55,"ESP":11.22,"FIN":5.77,"BEL":1.02,"ITA":1.0,"RUS":0.76,"USA":0.62,"PRT":0.48,"AUT":0.43,"IRL":0.21},"DGIT":{"USA":49.69,"JPN":12.93,"AUS":6.84,"KOR":4.74,"DEU":4.3,"GBR":4.1,"BRA":3.44,"FRA":2.79,"IND":1.91,"CHN":1.22,"PRT":1.03,"CHE":0.99,"DNK":0.95,"NLD":0.85,"BEL":0.83,"CAN":0.82,"AUT":0.78,"SGP":0.71,"TWN":0.71,"ZAF":0.36},"IPRP":{"DEU":37.13,"FRA":27.52,"SWE":10.82,"CHE":7.73,"BEL":4.62,"ESP":4.54,"ITA":1.63,"NLD":1.54,"FIN":1.37,"AUT":1.32,"IRL":0.95,"NOR":0.84},"IUSP":{"USA":100.0},"IEUX":{"FRA":22.79,"DEU":20.61,"CHE":18.05,"NLD":6.65,"ESP":6.4,"SWE":5.42,"ITA":4.13,"DNK":3.67,"FIN":2.8,"BEL":2.22,"NOR":1.71,"USA":1.48,"KOR":1.19,"GBR":0.66,"IRL":0.58,"AUT":0.53,"CHN":0.44,"PRT":0.35,"SGP":0.19,"LUX":0.12},"IUKP":{"GBR":98.75,"DEU":1.25},"HPRO":{"USA":53.63,"JPN":10.99,"HKG":7.32,"DEU":4.92,"AUS":4.74,"GBR":4.11,"FRA":3.5,"SGP":2.91,"CAN":2.88,"SWE":1.62,"CHE":0.99,"BEL":0.62,"ESP":0.58,"ITA":0.21,"NLD":0.2,"AUT":0.17,"FIN":0.17,"IRL":0.12,"ISR":0.12,"NOR":0.11,"NZL":0.09},"HMEF":{"CHN":32.68,"KOR":16.3,"TWN":13.57,"BRA":6.66,"ZAF":6.23,"RUS":3.98,"MEX":3.49,"THA":2.75,"MYS":2.65,"IDN":2.14,"POL":1.32,"CHL":1.22,"PHL":1.04,"QAT":1.03,"HKG":1.02,"ARE":0.71,"TUR":0.67,"COL":0.52,"PER":0.36,"HUN":0.32,"GRC":0.31,"GBR":0.27,"USA":0.25,"CZE":0.2,"EGY":0.13,"LUX":0.08,"PAK":0.08,"IND":0.04,"CYP":0.0,"IRQ":0.0,"JPN":0.0,"MAC":0.0,"MLT":0.0,"SGP":0.0},"EMV":{"CHN":24.92,"TWN":16.67,"KOR":10.17,"IND":8.95,"THA":7.12,"MYS":7.08,"IDN":4.63,"CHL":3.23,"PHL":2.56,"QAT":2.34,"ARE":2.09,"MEX":1.43,"HKG":1.37,"BRA":1.28,"PER":1.26,"ZAF":1.09,"HUN":0.81,"COL":0.64,"CZE":0.54,"GRC":0.49,"POL":0.44,"EGY":0.37,"RUS":0.3,"PAK":0.21},"UKRE":{"GBR":99.01,"DEU":0.99},"EUXS":{"FRA":22.79,"DEU":20.6,"CHE":18.1,"NLD":6.65,"ESP":6.34,"SWE":5.42,"ITA":4.14,"DNK":3.68,"FIN":2.81,"BEL":2.22,"NOR":1.72,"USA":1.47,"KOR":1.18,"GBR":0.67,"IRL":0.58,"AUT":0.53,"CHN":0.44,"PRT":0.34,"SGP":0.19,"LUX":0.13},"RBTX":{"USA":32.95,"JPN":27.31,"TWN":11.13,"DEU":6.73,"GBR":4.78,"KOR":4.39,"FIN":2.94,"CAN":2.36,"CHN":1.98,"AUS":1.25,"AUT":1.17,"FRA":1.08,"SWE":1.0,"BRA":0.92},"IDJG":{"DEU":33.97,"FRA":33.37,"NLD":8.45,"ESP":7.69,"KOR":5.54,"USA":3.03,"GBR":1.84,"BEL":1.35,"ITA":1.18,"IRL":1.13,"AUT":0.84,"SGP":0.82,"FIN":0.79},"EMRG":{"CHN":30.24,"KOR":14.81,"TWN":12.14,"IND":9.27,"ZAF":5.88,"BRA":5.75,"RUS":3.31,"MEX":3.15,"MYS":2.53,"THA":2.34,"IDN":2.06,"POL":1.25,"HKG":1.01,"PHL":1.01,"QAT":1.01,"CHL":0.97,"ARE":0.63,"TUR":0.48,"COL":0.37,"HUN":0.33,"PER":0.32,"GRC":0.31,"CZE":0.22,"GBR":0.2,"USA":0.19,"EGY":0.14,"PAK":0.05,"LUX":0.03},"CUSS":{"USA":98.79,"PRI":0.25,"GBR":0.23,"CHN":0.22,"SWE":0.13,"CAN":0.08,"CHE":0.06,"GHA":0.06,"COL":0.04,"NLD":0.04,"TWN":0.03,"DEU":0.02,"SGP":0.02,"BRA":0.01,"HKG":0.01,"IRL":0.01,"MEX":0.01,"ZAF":0.01},"JPNL":{"JPN":100.0},"GBDV":{"USA":20.81,"CAN":20.52,"GBR":9.68,"FRA":7.12,"JPN":6.17,"HKG":4.5,"ZAF":3.99,"ESP":3.96,"SWE":3.6,"CHE":2.79,"DEU":2.71,"FIN":1.96,"PRT":1.84,"AUS":1.53,"ITA":1.33,"CHN":1.32,"MEX":1.13,"SGP":1.07,"DNK":0.96,"KOR":0.86,"NLD":0.78,"BEL":0.75,"NOR":0.61},"GRE":{"GRC":74.3,"GBR":24.89,"BEL":0.81},"SEMB":{"MEX":5.92,"IDN":5.06,"RUS":3.97,"TUR":3.97,"PHL":3.87,"ARG":3.58,"COL":3.56,"BRA":3.46,"ZAF":3.2,"DOM":3.14,"PER":3.09,"ECU":3.06,"KAZ":3.04,"OMN":3.02,"EGY":2.87,"UKR":2.73,"CHN":2.57,"POL":2.55,"HUN":2.54,"URY":2.5,"LBN":2.15,"MYS":2.02,"PAN":2.02,"LKA":1.99,"CHL":1.78,"ROU":1.64,"NGA":1.6,"AGO":1.27,"AZE":1.22,"HRV":1.15,"JAM":1.09,"VEN":1.07,"PAK":1.03,"GHA":0.94,"KEN":0.92,"CIV":0.89,"IRQ":0.83,"LTU":0.72,"USA":0.69,"JOR":0.66,"CRI":0.6,"HKG":0.53,"SRB":0.49,"SEN":0.44,"DEU":0.42,"IND":0.41,"ZMB":0.39,"MAR":0.34,"SVK":0.33,"GAB":0.32,"NLD":0.27,"PRY":0.24,"SLV":0.23,"VNM":0.23,"ETH":0.22,"BOL":0.21,"MNG":0.21,"TTO":0.21,"TUN":0.2,"CYM":0.15,"AUS":0.13,"IRL":0.05},"XPXJ":{"AUS":56.6,"HKG":25.7,"SGP":11.65,"NZL":1.82,"CHN":1.61,"MAC":0.93,"USA":0.84,"PNG":0.53,"PHL":0.31},"UKMV":{},"ZPRS":{"USA":57.69,"JPN":11.68,"GBR":7.25,"CAN":3.65,"AUS":2.7,"DEU":2.37,"SWE":2.04,"CHE":1.58,"FRA":1.45,"ITA":1.43,"ESP":0.98,"NLD":0.9,"DNK":0.72,"NOR":0.66,"BEL":0.64,"SGP":0.61,"HKG":0.6,"ISR":0.55,"FIN":0.52,"AUT":0.4,"NZL":0.38,"IRL":0.29,"CHN":0.23,"PRI":0.17,"PRT":0.14,"MLT":0.07,"BRA":0.05,"COL":0.04,"IDN":0.04,"TWN":0.04,"EGY":0.03,"GHA":0.02,"IND":0.02,"PER":0.02,"CIV":0.01,"LUX":0.01,"MEX":0.01,"VNM":0.01,"ZAF":0.01},"EXH4":{"DEU":20.22,"GBR":18.78,"FRA":17.52,"SWE":9.55,"CHE":9.1,"NLD":8.89,"USA":5.02,"FIN":3.86,"DNK":2.97,"ITA":1.8,"ESP":1.14,"IRL":0.79,"AUT":0.37},"EXH9":{"GBR":23.05,"ESP":21.48,"FRA":17.07,"ITA":15.56,"DEU":13.34,"DNK":3.45,"FIN":3.3,"PRT":2.75},"EXH5":{"GBR":27.17,"DEU":23.78,"CHE":17.35,"FRA":11.67,"NLD":5.84,"ITA":4.67,"FIN":4.38,"BEL":1.78,"NOR":1.26,"POL":1.05,"ESP":0.53,"DNK":0.51},"EXV6":{"GBR":50.64,"CHE":15.33,"FIN":11.26,"USA":6.82,"SWE":4.96,"NOR":2.8,"ITA":2.77,"AUT":1.78,"POL":1.14,"DEU":0.88,"FRA":0.82,"RUS":0.79},"RTWP":{"USA":99.17,"PRI":0.2,"GBR":0.19,"AGO":0.06,"CAN":0.06,"ISR":0.05,"MCO":0.05,"PER":0.05,"TWN":0.05,"SGP":0.04,"MHL":0.03,"BRA":0.01,"CZE":0.01,"HKG":0.01},"ISPA":{"USA":23.09,"GBR":12.41,"AUS":12.02,"SGP":10.32,"HKG":10.03,"CAN":8.93,"FRA":6.55,"CHE":3.64,"ITA":2.74,"DEU":2.36,"JPN":1.83,"PRT":1.46,"FIN":1.34,"SWE":1.08,"BEL":0.82,"THA":0.74,"ESP":0.63},"SBEG":{"COL":3.18,"IDN":3.16,"ECU":3.09,"PER":3.09,"ZAF":3.06,"CHL":3.04,"MEX":2.96,"PAN":2.96,"MYS":2.94,"HUN":2.92,"KAZ":2.91,"DOM":2.88,"TUR":2.84,"ARG":2.82,"EGY":2.81,"URY":2.68,"LBN":2.54,"UKR":2.43,"PHL":2.32,"IND":2.3,"NLD":2.26,"POL":2.24,"LKA":2.15,"RUS":2.13,"HRV":1.79,"BRA":1.66,"NGA":1.65,"CHN":1.57,"AZE":1.5,"ROU":1.47,"PAK":1.25,"SLV":1.22,"AGO":1.16,"CRI":1.14,"JAM":1.14,"GHA":1.12,"MAR":1.09,"CIV":0.95,"HKG":0.94,"KEN":0.87,"SRB":0.76,"IRQ":0.75,"USA":0.74,"MNG":0.73,"PRY":0.73,"VEN":0.71,"GBR":0.64,"JOR":0.62,"XSN":0.58,"SGP":0.54,"SEN":0.51,"GTM":0.5,"GAB":0.47,"BLR":0.46,"ZMB":0.46,"TTO":0.42,"DEU":0.4,"TUN":0.4,"BOL":0.36,"HND":0.36,"VNM":0.34,"NAM":0.28,"GEO":0.27,"THA":0.27,"IRL":0.25,"ETH":0.23,"ARM":0.2,"CMR":0.2,"SUR":0.15,"TJK":0.12,"MOZ":0.11,"AUS":0.07,"CAN":0.07,"BLZ":0.06,"MUS":0.06},"CSCA":{"CAN":100.0},"CSJP":{"JPN":100.0},"CNKY":{"JPN":100.0},"XMMD":{"CHN":29.91,"KOR":14.77,"TWN":12.23,"IND":9.33,"ZAF":5.87,"BRA":5.8,"RUS":3.33,"MEX":3.11,"MYS":2.48,"THA":2.41,"IDN":1.99,"POL":1.23,"CHL":1.07,"PHL":1.05,"HKG":0.99,"QAT":0.94,"ARE":0.67,"TUR":0.51,"COL":0.46,"PER":0.33,"HUN":0.29,"GRC":0.28,"GBR":0.25,"USA":0.22,"CZE":0.19,"EGY":0.14,"LUX":0.07,"PAK":0.06},"PSRM":{"CHN":31.28,"TWN":16.57,"BRA":11.86,"RUS":9.91,"IND":7.45,"ZAF":5.99,"MEX":4.41,"THA":4.19,"MYS":2.55,"IDN":1.5,"POL":1.43,"CHL":1.17,"TUR":1.17,"HKG":0.49},"BULL":{},"IGHY":{"USA":65.6,"ITA":6.36,"DEU":6.16,"FRA":5.07,"GBR":3.9,"NLD":3.79,"CAN":1.9,"ESP":1.43,"SWE":1.08,"IRL":0.96,"JPN":0.85,"FIN":0.72,"LUX":0.54,"CHN":0.32,"PRT":0.31,"DNK":0.3,"BEL":0.22,"AUT":0.19,"CYM":0.16,"AUS":0.05,"CHE":0.04,"SGP":0.02,"GRC":0.01},"XCHA":{"DEU":49.33,"USA":22.93,"CHE":13.7,"NLD":4.72,"DNK":3.17,"ISR":2.25,"SWE":1.72,"BEL":1.12,"NOR":1.07},"SEML":{"BRA":10.2,"POL":10.05,"MEX":9.88,"IDN":9.87,"ZAF":9.81,"THA":8.14,"RUS":7.01,"COL":6.57,"MYS":5.0,"HUN":4.44,"CZE":4.11,"TUR":4.08,"PER":3.24,"ROU":3.19,"CHL":2.98,"ARG":1.43},"SHYU":{"USA":94.95,"CAN":1.49,"NLD":1.05,"GBR":1.01,"DEU":0.52,"FRA":0.24,"SWE":0.2,"FIN":0.19,"ITA":0.11,"AUT":0.08,"AUS":0.07,"BEL":0.03,"SGP":0.03,"GRC":0.01,"LUX":0.01},"XCX3":{"MYS":100.0},"SAUS":{"AUS":98.4,"PNG":0.92,"USA":0.68},"FSWD":{"USA":64.64,"JPN":11.68,"GBR":5.61,"HKG":2.49,"FRA":2.48,"AUS":2.23,"CAN":2.09,"DEU":1.79,"CHE":1.72,"SGP":0.91,"ESP":0.77,"BEL":0.72,"NLD":0.72,"SWE":0.66,"DNK":0.6,"CHN":0.55,"ITA":0.2,"FIN":0.15},"CECL":{},"EMCP":{"NLD":11.0,"USA":7.25,"DEU":7.12,"HKG":7.07,"SGP":6.59,"ARE":5.17,"MEX":5.02,"KOR":4.81,"CHN":4.46,"COL":4.41,"TUR":4.28,"GBR":3.7,"CHL":3.38,"IND":2.99,"BRA":2.6,"ARG":2.58,"CAN":1.92,"PER":1.8,"SAU":1.56,"QAT":1.42,"THA":1.26,"IRL":1.12,"XSN":0.78,"ISR":0.77,"MAR":0.73,"IDN":0.69,"CYM":0.67,"LUX":0.64,"MYS":0.59,"MUS":0.54,"PHL":0.51,"RUS":0.44,"KAZ":0.38,"OMN":0.3,"VGB":0.26,"CHE":0.25,"NGA":0.25,"SWE":0.25,"AUT":0.19,"UKR":0.12,"ZAF":0.12},"SHYG":{"ITA":17.39,"DEU":17.08,"FRA":14.71,"NLD":12.28,"USA":9.5,"GBR":8.77,"ESP":3.38,"IRL":2.68,"SWE":2.57,"JPN":2.12,"FIN":1.79,"LUX":1.23,"DNK":1.02,"CAN":0.81,"AUT":0.68,"CHN":0.68,"MEX":0.67,"TUR":0.52,"CZE":0.5,"BGR":0.49,"BEL":0.4,"BRA":0.34,"POL":0.15,"CHE":0.13,"LTU":0.12},"IWRD":{"USA":62.17,"JPN":8.52,"GBR":5.81,"FRA":3.59,"CAN":3.44,"DEU":3.27,"CHE":3.13,"AUS":2.27,"HKG":1.05,"NLD":1.04,"ESP":1.0,"SWE":0.88,"ITA":0.64,"DNK":0.59,"SGP":0.53,"FIN":0.45,"BEL":0.36,"NOR":0.26,"CHN":0.19,"KOR":0.19,"ISR":0.14,"IRL":0.11,"AUT":0.08,"NZL":0.07,"PRT":0.05,"MAC":0.04,"BRA":0.03,"RUS":0.03,"LUX":0.02,"PNG":0.02,"ARE":0.01,"PHL":0.01,"MEX":0.0,"MLT":0},"XAUS":{"AUS":96.09,"USA":1.42,"NZL":0.92,"PNG":0.71,"FRA":0.6,"GBR":0.25},"XGDD":{"USA":23.13,"GBR":12.52,"AUS":12.35,"SGP":10.44,"HKG":9.74,"CAN":8.91,"FRA":6.37,"CHE":3.63,"ITA":2.7,"DEU":2.31,"JPN":1.84,"PRT":1.58,"FIN":1.34,"SWE":1.03,"BEL":0.78,"THA":0.69,"ESP":0.63},"ISUS":{"USA":99.35,"RUS":0.23,"GBR":0.17,"SWE":0.13,"CHN":0.11},"XCX4":{"THA":100.0},"GHYS":{"USA":65.78,"ITA":6.5,"DEU":5.73,"FRA":5.28,"GBR":3.89,"NLD":3.81,"CAN":1.97,"ESP":1.5,"SWE":0.91,"FIN":0.84,"IRL":0.83,"JPN":0.82,"LUX":0.43,"DNK":0.39,"CHN":0.37,"PRT":0.27,"AUT":0.24,"BEL":0.19,"CYM":0.17,"AUS":0.07,"GRC":0.01},"PADV":{"JPN":29.52,"AUS":24.45,"CHN":13.16,"TWN":11.83,"HKG":11.44,"SGP":4.4,"IND":1.39,"IDN":0.99,"KOR":0.98,"NZL":0.97,"PHL":0.85},"SPOG":{"USA":65.9,"CAN":13.26,"AUS":5.15,"RUS":4.84,"CHN":4.33,"JPN":1.97,"PNG":1.17,"GBR":1.13,"SWE":0.92,"NOR":0.81,"GHA":0.31,"COL":0.2},"SPGP":{"CAN":49.74,"AUS":15.79,"USA":13.5,"ZAF":5.36,"GBR":5.08,"PER":2.78,"CHN":2.22,"RUS":1.4,"NZL":1.38,"EGY":1.15,"CIV":0.87,"MEX":0.37,"TUR":0.35},"SSHY":{"USA":85.89,"CAN":6.01,"GBR":3.08,"NLD":1.95,"DEU":1.14,"AUS":0.67,"FIN":0.59,"GRC":0.23,"SWE":0.18,"MHL":0.16,"DNK":0.08,"FRA":0.03},"EMSD":{"KOR":19.48,"TWN":19.08,"IND":16.11,"CHN":12.27,"BRA":4.76,"ZAF":4.75,"THA":4.05,"MEX":3.46,"MYS":3.32,"IDN":2.31,"CHL":1.39,"HKG":1.01,"POL":1.01,"PHL":0.9,"GRC":0.89,"TUR":0.8,"QAT":0.78,"RUS":0.74,"PAK":0.73,"EGY":0.64,"ARE":0.42,"COL":0.4,"SGP":0.16,"HUN":0.15,"MLT":0.13,"GBR":0.1,"PER":0.08,"CZE":0.04,"IRQ":0.03,"JPN":0.02},"XDBG":{"DEU":50.76,"USA":11.89,"NLD":9.64,"CHE":8.61,"DNK":7.58,"JPN":4.28,"SWE":3.84,"BEL":3.4},"IGWD":{"USA":62.26,"JPN":8.44,"GBR":5.77,"FRA":3.59,"CAN":3.45,"DEU":3.27,"CHE":3.14,"AUS":2.28,"NLD":1.07,"HKG":1.05,"ESP":1.01,"SWE":0.88,"ITA":0.64,"DNK":0.58,"SGP":0.53,"FIN":0.44,"BEL":0.35,"NOR":0.27,"CHN":0.18,"KOR":0.18,"ISR":0.15,"IRL":0.11,"AUT":0.08,"NZL":0.07,"PRT":0.05,"MAC":0.04,"BRA":0.03,"RUS":0.03,"LUX":0.02,"PNG":0.02,"MEX":0.01,"PHL":0.01},"DXSM":{"DEU":50.76,"USA":11.89,"NLD":9.64,"CHE":8.61,"DNK":7.58,"JPN":4.28,"SWE":3.84,"BEL":3.4},"EMIN":{"ISR":20.32,"BRA":20.21,"MEX":20.17,"ZAF":15.46,"TUR":11.92,"KOR":4.21,"CHL":3.04,"THA":2.85,"RUS":1.22,"POL":0.6},"EMDL":{"KOR":10.78,"MEX":10.17,"MYS":9.71,"BRA":9.58,"IDN":9.2,"THA":8.32,"POL":7.65,"ZAF":6.7,"RUS":4.5,"COL":4.31,"ISR":4.03,"PHL":3.17,"CZE":3.12,"HUN":2.71,"PER":1.97,"TUR":1.86,"ROU":1.64,"ARG":0.45,"CHL":0.09,"XSN":0.04},"EMAS":{"CHN":40.19,"KOR":19.47,"TWN":16.12,"IND":12.33,"MYS":3.29,"THA":3.14,"IDN":2.6,"PHL":1.34,"HKG":1.29,"USA":0.19,"PAK":0.06},"EMDV":{"CHN":22.18,"ZAF":20.58,"THA":17.87,"TWN":16.07,"RUS":5.51,"MYS":4.12,"IDN":2.68,"ARE":2.2,"IND":1.72,"BRA":1.71,"MEX":1.42,"QAT":1.3,"TUR":1.25,"POL":0.9,"CHL":0.31,"COL":0.17},"LEML":{"CHN":29.91,"KOR":14.77,"TWN":12.23,"IND":9.33,"ZAF":5.87,"BRA":5.8,"RUS":3.33,"MEX":3.11,"MYS":2.48,"THA":2.41,"IDN":1.99,"POL":1.23,"CHL":1.07,"PHL":1.05,"HKG":0.99,"QAT":0.94,"ARE":0.67,"TUR":0.51,"COL":0.46,"PER":0.33,"HUN":0.29,"GRC":0.28,"GBR":0.25,"USA":0.22,"CZE":0.19,"EGY":0.14,"LUX":0.07,"PAK":0.06},"SPAG":{"USA":49.85,"CAN":10.97,"JPN":9.75,"NOR":8.4,"GBR":4.41,"SGP":3.04,"DEU":1.69,"ISR":1.64,"AUS":1.56,"CHL":1.27,"CHE":1.25,"BRA":1.23,"HKG":0.98,"SWE":0.85,"KOR":0.78,"NLD":0.6,"FRA":0.48,"CHN":0.45,"RUS":0.41,"DNK":0.32,"BEL":0.04},"ISJP":{"JPN":100.0},"CUKS":{"GBR":96.71,"IRL":0.5,"CHE":0.49,"USA":0.44,"EGY":0.35,"IND":0.35,"CAN":0.3,"ISR":0.3,"IRQ":0.19,"DEU":0.16,"ZAF":0.09,"AUS":0.08,"KAZ":0.06},"CES1":{"DEU":24.82,"ITA":15.68,"FRA":15.45,"ESP":11.08,"NLD":8.92,"BEL":6.99,"FIN":6.24,"AUT":3.92,"IRL":1.82,"GBR":1.74,"PRT":1.6,"USA":0.99,"BRA":0.54,"LUX":0.16,"CHE":0.04,"CYP":0},"IWDP":{"USA":56.12,"HKG":7.85,"JPN":7.18,"DEU":5.13,"AUS":5.08,"GBR":3.8,"FRA":3.76,"CAN":3.09,"SGP":2.89,"SWE":1.47,"CHE":1.06,"BEL":0.64,"ESP":0.62,"ITA":0.23,"NLD":0.21,"FIN":0.19,"AUT":0.18,"ISR":0.14,"IRL":0.13,"NOR":0.12,"NZL":0.1,"MLT":0},"IAPD":{"AUS":49.55,"HKG":26.93,"NZL":12.72,"SGP":6.26,"JPN":2.74,"CHN":1.79},"IJPN":{"JPN":100.0},"IASP":{"HKG":34.02,"JPN":31.06,"AUS":22.0,"SGP":12.5,"NZL":0.42,"MLT":0.0},"NA1":{"AUS":56.31,"HKG":26.01,"SGP":11.63,"NZL":1.81,"CHN":1.61,"MAC":0.96,"USA":0.83,"PNG":0.52,"PHL":0.31,"MLT":0},"ISWD":{"USA":49.66,"JPN":9.81,"GBR":7.51,"CHE":7.23,"DEU":5.95,"FRA":5.07,"CAN":3.74,"AUS":2.27,"ESP":1.28,"SWE":1.15,"HKG":1.0,"NLD":0.77,"KOR":0.64,"NOR":0.63,"SGP":0.62,"FIN":0.58,"ITA":0.56,"BEL":0.37,"DNK":0.36,"CHN":0.31,"NZL":0.16,"AUT":0.11,"RUS":0.11,"PRT":0.08,"MEX":0.02},"HRUD":{"RUS":98.6,"GBR":1.4},"SSAC":{"USA":55.64,"JPN":7.56,"GBR":5.05,"CHN":3.35,"FRA":3.14,"CAN":3.08,"DEU":2.95,"CHE":2.82,"AUS":2.06,"KOR":1.74,"TWN":1.39,"HKG":1.12,"NLD":0.99,"ESP":0.95,"IND":0.94,"SWE":0.77,"BRA":0.67,"ZAF":0.59,"DNK":0.55,"SGP":0.52,"ITA":0.5,"FIN":0.45,"RUS":0.42,"MEX":0.36,"BEL":0.31,"MYS":0.28,"THA":0.25,"IDN":0.24,"NOR":0.23,"ISR":0.17,"POL":0.13,"AUT":0.1,"PHL":0.09,"QAT":0.09,"CHL":0.08,"PRT":0.08,"COL":0.06,"MAC":0.06,"PER":0.06,"TUR":0.05,"ARE":0.03,"GRC":0.03,"IRL":0.03,"NZL":0.03,"CZE":0.02,"LUX":0.02},"HMYR":{"MYS":100.0},"HMLA":{"BRA":54.04,"MEX":28.3,"CHL":9.83,"COL":4.15,"PER":3.06,"USA":0.62},"ISRL":{"ISR":86.52,"USA":13.48},"HIDR":{"IDN":100.0},"XX25":{"CHN":99.29,"HKG":0.71},"HMEX":{"MEX":100.0},"HMBR":{"BRA":100.0},"HMFD":{"CHN":45.38,"KOR":22.52,"TWN":18.63,"THA":3.75,"MYS":3.69,"IDN":2.98,"PHL":1.46,"HKG":1.33,"USA":0.24},"HMCH":{"CHN":96.89,"HKG":2.72,"USA":0.39},"XSGI":{"USA":40.24,"CAN":10.92,"AUS":8.92,"ITA":7.18,"ESP":7.15,"FRA":5.44,"GBR":4.15,"CHN":3.84,"MEX":3.14,"DEU":2.5,"HKG":2.29,"NZL":1.4,"CHE":1.24,"SGP":0.57,"BRA":0.5,"NLD":0.3,"CHL":0.23},"HTRY":{"TUR":100.0},"IGSG":{"USA":43.99,"JPN":8.24,"FRA":5.88,"GBR":5.88,"CHE":5.83,"CAN":4.84,"DEU":4.58,"KOR":3.83,"AUS":2.78,"ESP":2.29,"NLD":1.98,"TWN":1.87,"ITA":1.25,"SWE":0.95,"IND":0.93,"DNK":0.79,"BRA":0.77,"FIN":0.56,"HKG":0.53,"THA":0.49,"CHN":0.38,"SGP":0.21,"ZAF":0.16,"MEX":0.15,"CHL":0.13,"PRT":0.13,"NOR":0.12,"COL":0.08,"RUS":0.08,"BEL":0.06,"NZL":0.06,"AUT":0.05,"PNG":0.05,"HUN":0.03,"PHL":0.03,"TUR":0.02},"IJPH":{"JPN":100.0},"IJPE":{"JPN":100.0},"ASIL":{},"RQFI":{"CHN":100.0},"FKU":{"GBR":94.43,"CHE":2.38,"RUS":1.31,"USA":0.97,"ARE":0.91},"LEMV":{},"CEA1":{"CHN":40.2,"KOR":19.9,"TWN":16.54,"IND":11.49,"THA":3.34,"MYS":3.26,"IDN":2.6,"PHL":1.29,"HKG":1.12,"USA":0.18,"PAK":0.09},"CSRU":{"RUS":98.49,"GBR":1.51},"CSBR":{"BRA":100.0},"XMID":{"IDN":100.0},"XMEX":{"MEX":100.0},"RIOL":{},"XPHI":{"PHL":100.0},"XKS2":{"KOR":100.0},"IH2O":{"USA":49.37,"GBR":12.74,"FRA":7.82,"CHE":5.31,"CHN":5.23,"SWE":3.68,"JPN":2.99,"CAN":2.64,"NLD":2.58,"KOR":1.93,"AUT":1.85,"ITA":1.73,"BRA":1.18,"AUS":0.83,"SGP":0.12},"XMLA":{"BRA":53.47,"MEX":28.72,"CHL":9.9,"COL":4.21,"PER":3.03,"USA":0.66},"XMRC":{"RUS":98.36,"GBR":1.64},"XMBR":{"BRA":100.0},"AUCO":{},"INFR":{"USA":58.76,"CAN":11.98,"JPN":7.79,"GBR":3.08,"HKG":2.94,"AUS":2.42,"ESP":1.94,"ITA":1.79,"CHN":1.64,"BRA":0.88,"MEX":0.88,"FRA":0.8,"IND":0.63,"THA":0.58,"DNK":0.51,"KOR":0.41,"LUX":0.4,"RUS":0.35,"CHL":0.32,"PHL":0.26,"NZL":0.22,"CHE":0.19,"DEU":0.18,"MYS":0.16,"ARE":0.15,"IDN":0.11,"TWN":0.11,"BEL":0.1,"SGP":0.1,"COL":0.09,"AUT":0.06,"PRT":0.05,"TUR":0.05,"GRC":0.02,"POL":0.02,"PAK":0.01},"XAXJ":{"CHN":34.33,"KOR":16.66,"TWN":13.8,"HKG":10.59,"IND":10.52,"SGP":4.22,"MYS":2.8,"THA":2.72,"IDN":2.25,"PHL":1.31,"MAC":0.39,"USA":0.35,"PAK":0.07},"SRSA":{"ZAF":94.71,"GBR":3.35,"HKG":1.07,"LUX":0.87},"SEDY":{"TWN":28.68,"RUS":17.04,"CHN":9.74,"THA":9.45,"BRA":7.3,"MYS":4.91,"ZAF":4.46,"QAT":2.87,"MEX":2.86,"ARE":2.6,"IDN":2.33,"PHL":2.11,"CZE":2.04,"TUR":1.4,"GRC":1.14,"IND":0.55,"POL":0.54},"XMAS":{"CHN":39.72,"KOR":19.61,"TWN":16.24,"IND":12.39,"MYS":3.3,"THA":3.2,"IDN":2.64,"PHL":1.39,"HKG":1.23,"USA":0.19,"PAK":0.09},"XMTW":{"TWN":99.83,"USA":0.17},"WOOD":{"USA":36.15,"CAN":12.15,"BRA":12.13,"SWE":10.76,"JPN":8.97,"FIN":8.31,"GBR":4.09,"IRL":3.9,"HKG":3.53},"INRG":{"USA":26.29,"CHN":24.4,"NZL":11.69,"AUT":10.05,"CAN":6.74,"BRA":5.58,"DNK":5.49,"ESP":4.27,"GBR":3.14,"DEU":2.33},"XCX6":{"CHN":96.89,"HKG":2.72,"USA":0.4},"FEX":{"USA":99.45,"CHE":0.27,"SGP":0.21,"CHN":0.08},"SEMA":{"CHN":29.98,"KOR":14.84,"TWN":12.35,"IND":8.55,"BRA":6.12,"ZAF":5.72,"RUS":3.7,"MEX":3.19,"THA":2.49,"MYS":2.45,"IDN":1.93,"POL":1.18,"CHL":1.09,"PHL":0.96,"QAT":0.94,"HKG":0.93,"ARE":0.66,"TUR":0.6,"COL":0.47,"PER":0.34,"GRC":0.28,"HUN":0.28,"GBR":0.25,"USA":0.21,"CZE":0.19,"EGY":0.14,"PAK":0.07,"LUX":0.06},"XLPE":{"DEU":50.71,"NLD":16.06,"JPN":12.61,"CHE":11.26,"BEL":3.67,"FRA":2.89,"FIN":2.79},"SPOL":{"POL":98.95,"LUX":0.97,"USA":0.08},"IEMS":{"KOR":20.43,"TWN":19.35,"IND":13.65,"CHN":12.05,"ZAF":5.04,"BRA":4.79,"THA":4.41,"MYS":3.53,"MEX":3.52,"IDN":2.29,"CHL":1.57,"HKG":1.16,"TUR":0.97,"POL":0.96,"QAT":0.91,"PHL":0.89,"RUS":0.83,"PAK":0.77,"GRC":0.69,"EGY":0.62,"ARE":0.51,"COL":0.3,"SGP":0.18,"MLT":0.15,"HUN":0.13,"GBR":0.07,"CYP":0.06,"CZE":0.05,"MAC":0.05,"IRQ":0.04,"JPN":0.03},"LTAM":{"BRA":54.01,"MEX":28.32,"CHL":9.85,"COL":4.15,"PER":3.04,"USA":0.63},"FXC":{"CHN":99.28,"HKG":0.72},"ITWN":{"TWN":99.88,"USA":0.12},"ISFE":{"KOR":26.29,"TWN":24.69,"CHN":16.91,"HKG":8.65,"SGP":8.03,"THA":5.73,"MYS":4.57,"IDN":3.25,"PHL":1.07,"MAC":0.21,"VNM":0.15,"CAN":0.12,"DEU":0.08,"GBR":0.08,"IRQ":0.05,"USA":0.05,"JPN":0.04},"IEMI":{"CHN":43.93,"MEX":13.45,"THA":9.78,"BRA":8.35,"MYS":7.78,"RUS":5.3,"CHL":5.27,"KOR":5.04,"MCO":1.1},"IEER":{"RUS":62.86,"POL":25.69,"HUN":6.1,"CZE":4.0,"GBR":1.1,"LUX":0.25},"IFFF":{"CHN":38.43,"KOR":18.71,"TWN":15.57,"HKG":11.76,"SGP":4.79,"THA":3.14,"MYS":3.06,"IDN":2.45,"PHL":1.34,"MAC":0.38,"USA":0.36},"ITKY":{"TUR":100.0},"BRIC":{"CHN":67.12,"RUS":14.37,"BRA":14.02,"IND":3.57,"HKG":0.93},"IBZL":{"BRA":100.0},"IKOR":{"KOR":100.0},"IPRV":{"USA":61.11,"CAN":14.49,"CHE":8.78,"GBR":5.08,"FRA":4.98,"DEU":2.08,"JPN":1.72,"SWE":1.7,"POL":0.03,"ISR":0.02},"XCX5":{"IND":100.0},"PSWC":{"USA":96.95,"PRI":0.74,"CAN":0.69,"BRA":0.52,"ISR":0.41,"GBR":0.37,"CHN":0.33},"ISPY":{"USA":86.6,"JPN":5.11,"GBR":5.05,"KOR":3.23},"IEEM":{"CHN":29.98,"KOR":14.87,"TWN":12.33,"IND":8.56,"BRA":6.1,"ZAF":5.72,"RUS":3.67,"MEX":3.2,"THA":2.49,"MYS":2.42,"IDN":1.95,"POL":1.21,"CHL":1.12,"PHL":0.96,"QAT":0.94,"HKG":0.92,"ARE":0.67,"TUR":0.59,"COL":0.47,"PER":0.35,"GRC":0.3,"HUN":0.29,"GBR":0.25,"USA":0.2,"CZE":0.19,"EGY":0.13,"PAK":0.07,"LUX":0.06},"FEM":{"CHN":39.71,"BRA":10.09,"RUS":9.32,"TWN":7.0,"IND":5.23,"TUR":4.45,"THA":4.33,"POL":4.09,"MYS":3.84,"MEX":2.69,"ZAF":2.25,"HKG":2.03,"IDN":1.62,"HUN":1.0,"EGY":0.67,"CHL":0.52,"CZE":0.52,"PHL":0.41,"COL":0.22},"ROBG":{"USA":45.41,"JPN":24.16,"DEU":7.59,"TWN":6.66,"CHE":3.86,"FRA":1.99,"SWE":1.94,"GBR":1.8,"ISR":1.68,"CHN":1.49,"KOR":1.36,"CAN":1.09,"FIN":0.98},"XFVT":{"VNM":100.0},"ISDE":{"KOR":27.57,"CHN":27.01,"IND":8.86,"TWN":6.83,"RUS":6.78,"BRA":3.96,"ZAF":3.69,"MYS":3.12,"THA":2.26,"MEX":1.96,"IDN":1.79,"CHL":1.51,"POL":1.35,"QAT":1.06,"HKG":0.52,"HUN":0.39,"PHL":0.38,"ARE":0.26,"CZE":0.24,"TUR":0.2,"PER":0.13,"COL":0.09,"PAK":0.03,"GRC":0.01},"INRU":{"IND":100.0},"XNIF":{},"XSFR":{"ARG":21.12,"PAK":15.57,"VNM":11.21,"BRA":9.9,"KWT":8.1,"USA":8.06,"GBR":7.46,"BHR":6.4,"KHM":3.28,"NGA":3.09,"MAR":1.97,"KAZ":1.81,"OMN":1.04,"ROU":1.01},"SPDM":{},"SPLT":{},"SSLN":{},"UGAS":{},"ALUM":{},"OILB":{},"CORN":{},"COTN":{},"CRUD":{},"HOGS":{},"NICK":{},"SLVR":{},"COFF":{},"CATL":{},"NGAS":{},"SOYB":{},"SUGA":{},"WEAT":{},"SOYO":{},"GBS":{},"HEAT":{},"AIGX":{},"OILW":{},"ZINC":{},"PHAG":{},"COPA":{},"PHPT":{},"PHPM":{},"PHPD":{},"NGAF":{},"OSB1":{},"VZLC":{},"SEUR":{},"SJPY":{},"SGBS":{},"TINM":{},"COCO":{},"GBNO":{},"USGB":{},"GBCH":{},"GBUS":{},"JPGB":{},"GBCA":{},"SSLV":{},"XGLS":{},"PBRT":{}}



