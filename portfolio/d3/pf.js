
svgHeight = 200
svgWidth = 600
margin = {"top": 15, "bottom": 25, "left": 45, "right":5}
chartWidth = svgWidth - (margin.left + margin.right)
chartHeight = svgHeight - (margin.top + margin.bottom)

var data1 = []

var rand_max = 5

country_list = ['uk', 'us', 'fr', 'de', 'jp', 'it', 'ca', 'cn', 'sp', 'ru']
countries_used = []

data1 = make_data();

console.log('data1', data1)

barPad = 1
barWidth = (chartWidth / data1.length) - barPad

yScale = d3.scaleLinear()
            .domain([0, rand_max])
            .range([svgHeight - margin.bottom, margin.top])

xScale = d3.scaleBand()
            .domain(countries_used)
            .range([0, chartWidth])
            .align(0)
            // .paddingOuter(0.5)
            .paddingInner(0.05)

yAxis = d3.axisLeft().scale(yScale)
            .ticks(10)

xAxis = d3.axisBottom().scale(xScale)
            .tickSize(0)

var svg = d3.select("body").append("svg")
          .attr("width", svgWidth)
          .attr("height", svgHeight)

var bars = svg.selectAll("rect")
            .data(data1)
            .enter().append("rect")
              .attr("class", "bar")
              .style("fill", "steelblue")
              .attr("width", xScale.bandwidth())

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
              })

var text = svg.selectAll("text")
            .data(data1)
            .enter().append("text")
              .attr('class', 'barLabels')

              .attr("x", function(d, i) {
                return margin.left + i * (barWidth + 1) + (barWidth / 2);
              })

              .attr("y", function(d, i) {
                barTop = yScale(d.value);
                if (barTop > svgHeight - margin.bottom - 25) {
                  return barTop - 5;
                }
                return barTop + 20;
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
              })

svg.append('g')
    .attr('class', 'xAxis')
    .attr('transform', 'translate(' + (margin.left) + ', '
                                    + (chartHeight + margin.top) + ')')
    .call(xAxis)
        .selectAll('text')
        .attr('transform', 'translate(0, 5)')

svg.append('g')
    .attr('transform', 'translate(' + (margin.left) + ', 0)')
    .call(yAxis)

update_btn = d3.select('body').append('div')
                              .attr('class', 'btn')
                              .append('button')
                                .text('update me')

update_btn.on('click', function() {
    console.log('hey now');
    countries_used = [];
    data1 = make_data();
    console.log(countries_used);

    // update scale domains
    xScale.domain(countries_used);
    // rebind data
    var bars = svg.selectAll("rect").data(data1)
    
    // get enter selection
    bars.enter()
            .append("rect")
            .attr("class", "bar")
            .attr("x", svgWidth)

    .merge(bars)
    .transition()
          .style("fill", "steelblue")
          .attr("width", xScale.bandwidth())

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

    bars.exit().remove();

    labels = svg.selectAll('.barLabels').data(data1)

    labels.enter().append('text')
        .attr('class', 'barLabels')
        .merge(labels)

        .transition()
          .attr("x", function(d, i) {
            return xScale(d.key) + margin.left + (xScale.bandwidth() / 2);
          })

          .attr("y", function(d, i) {
            barTop = yScale(d.value);
            if (barTop > svgHeight - margin.bottom - 25) {
              return barTop - 5;
            }
            return barTop + 20;
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

    labels.exit().remove();

    svg.select('.xAxis')
        .transition()
            .call(xAxis)
                .selectAll('text')
                .attr('transform', 'translate(0, 5)');

    //
    //
    //
    // merge
    // get exit selection
    // remove
})


function make_data() {

    data_out = [] 
    var rand_len = Math.round(Math.random() * rand_max) + 4

    for (var i=0; i < rand_len; i++) {
        var ind = Math.round(Math.random() * rand_max)
        var co = country_list[ind];
        var val = Math.round(Math.random() * rand_max);
        if (!countries_used.includes(co)) {
          data_out.push({key: co, value: val});
          countries_used.push(co);
          console.log('added', co, 'value', val, 'index', ind);
        }
    }
    console.log('length of dataset is', data_out.length)
    return data_out;
}




