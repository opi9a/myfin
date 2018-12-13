
function initByAsset() {
    console.log('initializing asset chart x');

    var byAsset = {
        svgHeight: 170,
        svgWidth: 170,
    }

    byAsset.radius = (Math.min(byAsset.svgHeight, byAsset.svgWidth) - 20) / 2;


    byAsset['svg'] = d3.select("#chart2").append("svg")
           .attr("width", byAsset.svgWidth)
           .attr("height", byAsset.svgHeight)
             .append("g")
                 .attr("transform",
                       "translate(" + byAsset.svgWidth/2
                                 + "," + (byAsset.svgHeight/2 + 15) +")");

    byAsset['arc'] = d3.arc()
                        .outerRadius(byAsset.radius - 15)
                        .innerRadius(30);

    byAsset['svg'].append("text")
                    .attr("class", "chart-title")
                    .attr("transform", "translate(-20, -80)")
                    .text("Assets");

    var pie = d3.pie();

    var g = byAsset.svg.selectAll("arc")
                .data(pie([1]))
                .enter()
                .append("g")
                .attr("class", "arc")
                .attr("fill", "lightgrey");

    g.append("path")
        .attr("d", byAsset.arc)

    byAsset['testFunc'] = function() { console.log('byAsset testFunc') };

    byAsset['update'] = updateAssetChart;

    byAsset['currentMode'] = 'byPercent';

    return byAsset;

};

function updateAssetChart(newData='none', mode='none') {
    console.log('updating asset chart x');

    // cannot get updating to work, except by actually removing prev
    // - problem seems to be in making the selection.  It grows each time, 
    // i.e. the enter selection is always 3 (shd by 0 apart from first update)
    d3.select('#chart2').selectAll('path').remove();

    let svg = this.svg;
    let arc = this.arc;
    let svgHeight = this.svgHeight;
    let svgWidth = this.svgWidth;
    let radius = this.radius;

    if (newData !== 'none') {
        this.chartData = newData;
    };

    if (mode !== 'none') {
        this.mode = mode;
    };
    
    var chartData = this.chartData;

    console.log('pie input', chartData);

    // todo make percents

    var pieData = [];

    let divisor = 1;

    if (mode === 'byPercent') {
        divisor = sumObj(chartData) / 100;
    };

    Object.keys(chartData).forEach( a => {
        if (a != 'countrySum') {
            let row = {asset: a, value: chartData[a] / divisor};
            pieData.push(row);
        };
    });

    console.log('divisor', divisor);
    console.log('pieData', pieData);

    var pie = d3.pie()
        .value(function(d) { return d.value; })(pieData);
    

    var g = svg.selectAll("arc")
                .data(pie, d => d.data.asset);


    var h = g.enter()
                .append("g")
                .attr("class", "arc");

    h.append("path")
        .attr("d", arc)
        .transition()
        .duration(dur)
        .style("fill", d => colors[d.data.asset])
        .style("fill-opacity", d => {
            if (d.data.asset == 'bond') {
                return 0.5;
            } else { return 0.85; };
        });


    h.on('mouseover', function(d) { 
        var mData = d;
        svg.append('text')
            .attr("class", "tooltip")
            .attr("x", -1)
            .attr("y", -5)
            .attr("text-anchor", "middle")
            .text( function(d) { return mData.data.asset;} )
            .attr("fill-opacity", 0).transition().delay(200).duration(500)
            .attr("fill-opacity", 1);
        svg.append('text')
            .attr("class", "tooltip")
            .attr("x", 0)
            .attr("y", 10)
            .attr("text-anchor", "middle")
            // .text("heye")
            .text( function(d) {
                if (mode == 'byPercent') { return f(mData.data.value) + "%" }
                else { return f(mData.data.value) };
            } )
            .attr("fill-opacity", 0).transition().delay(200).duration(500)
            .attr("fill-opacity", 1);
    });

    h.on('mouseout', function() {
        d3.selectAll('.tooltip')
            .transition().duration(200).remove();
    });

    return pieData;

    
};
