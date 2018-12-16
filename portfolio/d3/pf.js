// general variables
const dur = 1500,
      f = d3.format(".1f"),
      f0 = d3.format(".0f"),
      f2 = d3.format(".2f"),
      // minBarH = 15,
      maxColumns = 16;

// load external data
var funds = getFunds(),
    colors = makeColors(),
    zoneLookup = makeZoneLookup();

// set up input table and buttons
var inputTable = d3.select('#input_table'),
    inputRows = d3.selectAll('.fundAmt'),
    addRowBtn = d3.select('#addRow-btn').on("click", function() { addFundRow() }),
    updateBtn = d3.select('#update-btn'),
    removeBtns = d3.selectAll('.remove-btn')
                   .on('click', function() {
                       this.parentNode.parentNode.remove();
                       portfolio = parseInputTable();
                       setTimeout(update(portfolio,
                                'Whole portfolio', funds), 1500);
                   }),
    infoBtns = d3.selectAll('.info-btn'),
    modeBtn = d3.selectAll('input[name="mode"]');

// initialize country chart
var byAsset = initByAsset();
var byCountry = initByCountry();
var byZone = initByZone();

// initialise global mode variable
var mode = 'byPercent';

// Get the initial portfolio and make charts
var portfolio = parseInputTable();
update(portfolio, 'Whole portfolio', funds);


// ACTIONS

updateBtn.on('click', function() {
    portfolio = parseInputTable();
    update(portfolio, 'Whole portfolio', funds)
});

modeBtn.on("change", function() { 
	if (mode == 'byPercent') { mode = 'byAmt' }
	else { mode = 'byPercent' };
	console.log('new mode', mode);
    byCountry.update(mode);
    byZone.update(mode);
    byAsset.update(mode);
});

var infoBtnActive = 'none';
infoBtns.on("click", function() {
    let fundName = d3.select(this).attr("data-fund");

    if (infoBtnActive == fundName) {
        infoBtnActive = 'none';
        update(portfolio, 'Whole portfolio', funds);
        return;
    };
    infoBtnActive = fundName;

    let singlePortfolio = { [fundName]: portfolio[fundName] };

    update(singlePortfolio, fundName + " fund only", funds);
});


inputTable.on("change", function() {
    console.log('changed table');

    newPortfolio = parseInputTable();

    if (hasChanged([newPortfolio, portfolio])) {
        console.log('changed values');
    } else {console.log('not changed values') };
    setTimeout(update(newPortfolio, 'Whole portfolio', funds), 1500);
});


// FUNCTION DEFINITIONS

function update(portfolio, dataSource, funds) {

    portfolioDistributions = getPortfolioDistribution(portfolio, funds);

    byCountry.setData(portfolioDistributions.countries, dataSource, maxColumns);
    console.log('mode in update', mode);
    byCountry.update(mode);

    byZone.setData(portfolioDistributions.zones, dataSource, maxColumns);
    byZone.update(mode);

    byAsset.setData(portfolioDistributions.assets);
    byAsset.update(mode);

    pfSum = d3.select('#table-container').selectAll('div.sum')
        .data([sumObj(portfolio)]);
    pfSum.enter()
        .append('div')
        .attr('style', 'float: left')
        .attr('class', 'sum')
        .text(d => 'sum:  ' + d);
    pfSum
        .text(d => 'sum:  ' + d);

    pfFee = d3.select('#table-container').selectAll('div.fee')
        .data([portfolioDistributions.fee]);
    pfFee.enter()
        .append('div')
        .attr('style', 'float: left')
        .attr('class', 'fee')
        .text(d => 'fee:  ' + f2(d) + " %");
    pfFee
        .text(d => 'fee:  ' + f2(d) + " %");
};


function removeRow(input) {
    input.remove();
};


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



function parseInputTable() {


    var fundSet = Object.keys(funds);
    var out = {};
    var names = document.getElementsByClassName('fundName');
    var amts = document.getElementsByClassName('fundAmt');

    for (var i=0; i<names.length; i++) {
        name = names[i].value.toUpperCase();
        amt = amts[i].value;

        if (fundSet.includes(name)) {
          out[name] = Number(amt);
        }
        
        else { alert(name + ' is not in set of funds - ignoring it'); }
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
    var fee = 0; // not used yet
    var portfolioSum = sumObj(portfolio);


    console.log('funds passed to getportfolio', funds);
    // go through each fund in the portfolio
    for (var fund in portfolio) {

        // get type of asset
        var assetType = funds[fund].type;

        // add to total for that asset type, initialising if reqd
        if (!(assetType in assets)) {
            assets[assetType] = 0;
        };

        assets[assetType] += portfolio[fund];

        // increment the fee
        fee += (funds[fund]["fee_%"] * portfolio[fund] / portfolioSum)

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

    return { countries: countries, zones: zones, assets: assets, fee: fee };
};

testOrderCountries = {
    a: { bonds: 1, stock: 1 },
    b: { bonds: 8, stock: 1 },
    c: { bonds: 1, stock: 6 },
    d: { bonds: 2, stock: 2 },
    e: { gold: 8 },
}

function orderCountries(countriesIn, numberOfBars) {   
    /*Return an object of top countries, trimmed to numberOfBars,
     with assets for each, including 'other', which includes
     all countries outside numberOfBars*/


    // get a list of all countries with their individual and summed assets
    // - needs to be a list, so can sort it
    // - eg [ { country: CHN, bond: 3.5, stock: 2.4 }, 
    //        { country: USA, bond: 2.5, stock: 1.4 } ] 
    let countryList = []

    for (let country in countriesIn) {
        let countryLine = clone(countriesIn[country]);
        countryLine['country'] = country;
        countryLine['sum'] = sumObj(countryLine);
        countryList.push(countryLine);
    };

    
    // sort by sum and select topN

    countryList = countryList.sort((a, b) => b.sum - a.sum);

    if (countryList.length > numberOfBars) {

        countryList = countryList.slice(0, numberOfBars);

        // Now make the 'other' element
        // make the sum across all countries for each asset $assetSums
        // - eg { bond: 17.1, stock: 9.5, gold: 8.1 }

        let assetSums = sumAssetsAcrossArea(countriesIn);
        let topNAssetSums = sumAssetsAcrossArea(countryList);

        // for each asset, subtract topN sum from total for that asset
        //
        let other = {country: 'other'};

        for (asset in assetSums) {
            other[[asset]] = assetSums[asset] - (topNAssetSums[asset] || 0);
        };

        countryList.push(other);
    };

    // clean up before returning - delete sums, use country as key
    outObj = {};
    countryList.forEach(c => {
        delete c.sum;
        let countryName = c.country;
        delete c.country;
        outObj[[countryName]] = c;
    });
    return outObj;

};


function sumAssetsAcrossArea(areas) {
    // works for objects and lists

    assetSums = {};

    for (area in areas) {
        for (asset in areas[area]) {
            if (!Object.keys(assetSums).includes(asset)) {
                assetSums[asset] = 0;
            };

            assetSums[asset] += areas[area][asset];
        };
    };

    return assetSums;
};


function makeColors() {

    // set up colors for likely countries (not all)
    let country_list = ['USA', 'FRA', 'DEU',
                        'JPN', 'ITA', 'CAN', 'CHN',
                        'ESP', 'NLD', 'KOR', 'RUS', 'IND', 'BRA']

    let colors = {};
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

    return colors;
};


function makeZoneLookup() {

    zoneLookup = {};

    zoneLookup['uk'] = 'UK';
    zoneLookup['na'] = 'North America';
    zoneLookup['cn'] = 'China';
    zoneLookup['nn'] = 'Not National';
    zoneLookup['eu'] = 'EU';
    zoneLookup['la'] = 'Latin America';
    zoneLookup['as'] = 'Asia excl China';
    zoneLookup['em'] = 'Emerging markets';
    zoneLookup['pc'] = 'Petro economies';

    return zoneLookup;

};


var portfolio_x = {
    'VFEM': 11.08,
    'AGBP': 27.81,
    'H50E': 22.23,
    'IGLN': 16.67,
    'XDJP': 11.11,
    'XDUS': 11.09,
};

var testPortfolio = {
    xfas: 1000,
    // xfab: 1,
    // xfag: 1,
    xfbs: 1000,
    // xfbb: 1,
    // xfbg: 1,
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
    xfag: { countries: { NON: 100 },
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
    xfbg: { countries: { NON: 100 },
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
      {country: 'NON', type: 'gold', start: '0', end: '12', key: 'NON-gold'},
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


function makeProfile(area, areaData, mode) {
    // currently only works for countries
    // need to fix for zones, taking out eg 'countrySum'
    // maybe test at start for whether is zone or country
    // and have a token accordingly
    // ACTUALLY appears ok..?  must not be a 'countrySum' in zones (?)
    
    console.log('area in makeP', area);

    areaRow = areaData[mode][area];

    var areaName;
    if (( area == 'NON') || ( area == 'nn')) {
        areaName = 'Not National' }
    else { areaName = area };

    out = [];

    Object.keys(areaRow)
        .forEach(a => {
            if (a !== 'countrySum' && areaRow[a] > 0.05 ) {
                if (mode === 'byAmt') {
                    out.push(" - " + a + ": " + f(areaRow[a]));
                };
                if (mode === 'byPercent') {
                    out.push(" - " + a + ": " + f0(areaRow[a]) + " %");
                };
            }
        })
    out = out.sort();
    var label = zoneLookup[areaName] || areaName;

    if (mode === 'byAmt') {
        var title = label + " " + f(sumObj(areaRow));
        console.log('title', title);
    };

    if (mode === 'byPercent') {
        var title = label + " " + f0(sumObj(areaRow)) + " %";
        console.log('title', title);
    };
    out.unshift(title);

    return out;
}


function sumObj(inObj) {
    return d3.sum(Object.values(inObj));
};


function sumAssets(portfolio) {
    assetTypes = {};

    for (area in portfolio) {
        for (asset in portfolio[area]) {
            if (!(Object.keys(assetTypes).includes(asset))) {
                assetTypes[asset] = 0;
            };

            assetTypes[asset] += portfolio[area][asset];
        };
    };

    return assetTypes;
};


function hasChanged(portfolios) {
    // reports whether a portfolio has changed, treating absent funds as equal
    // to zero (so that adding an empty fund is NOT a change)

    // get unique fund names
    let funds = new Set(Object.keys(portfolios[0])
                        .concat(Object.keys(portfolios[1])));

    funds = Array.from(funds);

    for (let i in funds) {

        let a = 0, b = 0;
        let fund = funds[i];

        if (Object.keys(portfolios[0]).includes(fund)) {
            a = portfolios[0][fund]
        };

        if (Object.keys(portfolios[1]).includes(fund))
        { b = portfolios[1][fund]
        };

        if (a !== b) { return true; };
    };

    return false;

};


function getPercents(chartArray) {
    // input array in form [{area: 'x', type: 't', start: 's', end: 'e'}]
    // get sum, and divide all by this
    var chartArray = clone(chartArray);

    let totalAmt = chartArray.reduce((acc, elem) => {
            acc += (elem.end - elem.start);
            return acc;
    }, 0);

    totalAmt /= 100;

    newArr = chartArray.map(row => {
        row.start /= totalAmt;
        row.end /= totalAmt;
        return row;
    });

    console.log('newArr', clone(newArr));
    return newArr;
};


function getCountrySummary(acc, elem) {

    if (!Object.keys(acc).includes(elem.country)) {
        acc[elem.country] = {};
    };

    acc[elem.country][elem.type] = elem.end - elem.start;

    return acc;
};


function getZoneSummary(acc, elem) {

    if (!Object.keys(acc).includes(elem.zone)) {
        acc[elem.zone] = {};
    };

    acc[elem.zone][elem.type] = elem.end - elem.start;

    return acc;
};

