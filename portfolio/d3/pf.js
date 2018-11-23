// set up canvas variables
var svgHeight = 300
    svgWidth = 400
    margin = {"top": 15, "bottom": 25, "left": 45, "right":5}
    chartWidth = svgWidth - (margin.left + margin.right)
    chartHeight = svgHeight - (margin.top + margin.bottom)
    dur = 2000

// set up data variables
var data1 = []
    rand_max = 9
    country_list = ['USA', 'FRA', 'DEU',
                    'JPN', 'ITA', 'CAN', 'CHN',
                    'ESP', 'NLD', 'KOR', 'TWN', 'IND', 'BRA']
    colors = {}

    for (var i=0; i<country_list.length; i++) {
        colors[country_list[i]] = d3.schemeCategory20[i];
    }
    
    colors['NoN'] = 'gold';
    colors['GBR'] = 'darkRed';


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
    .attr('transform', 'translate(' + (margin.left - 1) + ', 0)')
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
    data1 = get_portfolio_distribution(portfolio, funds);
    update();
});

var removeBtns

// moved these from addFundRow - need to have a row already I think
// is ok now as a couple are hardcoded in html, but watch out
removeBtns = d3.selectAll('.remove-btn')
removeBtns.on('click', function() { this.parentNode
                                        .parentNode.remove() });

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
removeBtns.on('click', function() { this.parentNode
                                        .parentNode.remove() });
};


function parseInputTable() {
    var fundSet = Object.keys(funds);
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
          .style("fill", function(d, i) {
              if (Object.keys(colors).includes(d.key)) { return colors[d.key]; }
              else { return 'steelblue'; };
          })
              
          .attr("height", d => svgHeight - yScale(d.value) - margin.bottom)
          .attr("x", d => xScale(d.key) + margin.left)
          .attr("y", d => yScale(d.value))
          .attr("text", d => d.value);

    // exit old bars stage left, diminishing and going transparent
    bars.exit()
        .attr("fill-opacity", 1)
            .transition()
            .duration(dur)
            .attr("fill-opacity", 0)
            .attr("x", svgWidth - xScale.bandwidth() / 2)
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
             if (barTop > svgHeight - margin.bottom - 25) { return "steelBlue"; }
             else { return "white"; }
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

    var countryDistro = {}, // the output object containing the distribution
        zoneDistro = {}; // not used yet
        fee = 0; // not used yet
        out1 = []
        out2 = []
        toAdd = 0,
        valSum = 0;
        numberOfBars = 10;

    var f = d3.format(".1f");
    var fund, c;

    // go through each fund in the portfolio
    for (fund in portfolio) {
        console.log('in', fund);

        // go through each country in the fund
        for (c in fundsDistributions[fund]['countries']) {
            console.log('in', c)

            // check if country already in object - if not, initialise it
            if (!(c in countryDistro)) {
                countryDistro[c] = 0;
            }

            // get percentage for that country in the fund, and weight
            // by multiplying by the amount of that fund in the portfolio 
            toAdd = fundsDistributions[fund]['countries'][c] * portfolio[fund];
            console.log('toAdd', fundsDistributions[fund]['countries'][c])

            // increment the corresponding country in the output distribution
            countryDistro[c] += toAdd;

            // and increment the sum for the distribution
            valSum += toAdd;
        }

        // go through each zone in the fund
        for (c in fundsDistributions[fund]['zones']) {
            console.log('in', c)

            // check if country already in object - if not, initialise it
            if (!(c in zoneDistro)) {
                countryDistro[c] = 0;
            }

            // get percentage for that country in the fund, and weight
            // by multiplying by the amount of that fund in the portfolio 
            toAdd = fundsDistributions[fund]['zones'][c] * portfolio[fund];
            console.log('toAdd', fundsDistributions[fund]['zones'][c])

            // increment the corresponding country in the output distribution
            zoneDistro[c] += toAdd;

            // and increment the sum for the distribution
            valSum += toAdd;
        }
    }

    // reweight values to 1 using the sum of all values added
    for (c in countryDistro) {
        out1.push({ key: c, value: countryDistro[c] / valSum });
    }

    // sort
    out1 = out1.sort((a, b) => b.value - a.value);

    // take top numberOfBars and sum the rest
    var others_sum = out1.slice(numberOfBars).map(a => a.value).reduce((a,b) => a + b, 0);
    out2 = out1.slice(0, numberOfBars);
    var others_len = out1.length - numberOfBars;
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





