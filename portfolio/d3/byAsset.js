
function initByAsset() {
    console.log('initializing asset chart');

    var byAsset = {
        svgHeight: 170,
        svgWidth: 170,

        totalAmt: 1,
        dataSource: 'none yet',
        currentMode: 'none',
        setData: setAssetData,
        update: updateAssetChart,

        pieData: {
            byAmt: [],
            byPercent: [],
        },

        mouseData: {
            byAmt: [],
            byPercent: [],
        },
        
        initAssets: [{asset: 'bond', value: 1},
                     {asset: 'stock', value: 1},
                     {asset: 'gold', value: 1},
                     {asset: 'cash', value: 1},
        ],
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
                    .attr("transform", "translate(-35, -80)")
                    .text("Assets");

    var pie = d3.pie().value(d => d.value).sort(null);

    var g = byAsset.svg.selectAll("arc")
                .data(pie(byAsset.initAssets))
                .enter()
                .append("g")
                .attr("class", "arc")
                .attr("fill", "lightgrey")
                .style("fill", d => colors[d.data.asset])
                .style("fill-opacity", d => {
                    if (d.data.asset == 'bond') {
                        return 0.5;
                    } else { return 0.85; };
                });

    g.append("path")
        .attr("d", byAsset.arc)

    return byAsset;

};


function setAssetData(newData) {

    filledData = {};
    allAssets = ['bond', 'stock', 'gold', 'cash']; 

    for (i in allAssets) {
        filledData[allAssets[i]] = newData[allAssets[i]] || 0;
    };

    console.log('filled data', filledData);
    this.coreData = filledData;

    // // create chartData byAmt and byPercent
    this.totalAmt = sumObj(byAsset.coreData);

    this.pieData = { byAmt: [], byPercent: [] };

    Object.keys(byAsset.coreData).forEach( a => {
        if (a != 'countrySum') {
            this.pieData['byAmt'].push({asset: a, value: newData[a]});
            this.pieData['byPercent'].push({asset: a, value: 100 * newData[a] / this.totalAmt});
        };
    });

    this.mouseData['byAmt'] = clone(this.coreData);
    this.mouseData['byPercent'] = clone(this.coreData);

    for (elem in this.mouseData['byPercent']) {
        this.mouseData['byPercent'][elem] /= (this.totalAmt / 100);
    };

};


function updateAssetChart(mode) {
    console.log('updating asset chart, mode passed', mode);

    // cannot get updating to work, except by actually removing prev
    // - problem seems to be in making the selection.  It grows each time, 
    // i.e. the enter selection is always 3 (shd by 0 apart from first update)
    // d3.select('#chart2').selectAll('path').remove();

    let svg = this.svg;
    let arc = this.arc;
    let svgHeight = this.svgHeight;
    let svgWidth = this.svgWidth;
    let radius = this.radius;

    this.currentMode = mode;
    
    var pieData = this.pieData[mode];

    console.log('pieData', pieData);

    var pie = d3.pie().sort(null)
        .value(function(d) { return d.value; })(pieData);

    var path = svg.selectAll("path")
                .data(pie, d => d.data.asset);

    path.transition('arc transition')
        .duration(dur)
        .attrTween("d", arcTween);

    var g = svg.selectAll(".arc");

    g.on('mouseover', function(d) { 
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
                console.log('by asset', byAsset);
                let assetType = mData.data.asset;
                console.log('asset type in mouse', assetType);
                console.log('mode seen from asset mouse', byAsset.currentMode);
                if (byAsset.currentMode === 'byPercent') {
                    return f0(byAsset.mouseData['byPercent'][assetType]) + "%" }
                else { return f0(byAsset.mouseData['byAmt'][assetType]) };
            } ) 
            .attr("fill-opacity", 0).transition().delay(200).duration(500)
            .attr("fill-opacity", 1);
    });

    g.on('mouseout', function() {
        d3.selectAll('.tooltip')
            .transition().duration(200).remove();
    });

    return pieData;
};

function arcTween(a) {
  var i = d3.interpolate(this._current, a);
  this._current = i(0);
  return function(t) {
    return byAsset.arc(i(t));
  };
}
