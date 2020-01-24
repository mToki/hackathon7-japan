let draw_sunburst = function(svg){
  $.ajax({type:'get', url:'/api/v1/tree/',
    success:function(j, status, xhr){
      draw_sunburst2(svg, j)
    }, 
    error:function(d){

    }
  })
}

let draw_sunburst2 = function(svg, data){
  let width = document.querySelector(svg).clientWidth;
  let height = document.querySelector(svg).clientHeight;
  var radius = Math.min(width, height) / 2;
  var color = d3.scaleOrdinal().range([
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", 
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
  ]);

  // Create primary <g> element
  var g = d3.select(svg)
      .attr('width', width)
      .attr('height', height)
      .append('g')
      .attr('transform', 'translate(' + width / 2 + ',' + height / 2 + ')');

  // Data strucure
  var partition = d3.partition()
      .size([2 * Math.PI, radius]);

  // Find data root
  var root = d3.hierarchy(data)
      .sum(function (d) { return d.size});

  // Size arcs
  partition(root);
  var arc = d3.arc()
      .startAngle(function (d) { return d.x0 })
      .endAngle(function (d) { return d.x1 })
      .innerRadius(function (d) { return d.y0 })
      .outerRadius(function (d) { return d.y1 });

  // Put it all together
  g.selectAll('path')
    .data(root.descendants())
    .enter()
    .append('path')
    .on("click", function(d){
      draw_vtree('#svg-vtree', d.data.vdisk_id)
      console.log(d.data.name)
    })
    .attr("display", function (d) { return d.depth ? null : "none"; })
    .attr("d", arc)
    .style('stroke', '#fff')
    .style("fill", function (d) { return color((d.children ? d : d.parent).data.name); })
    .append("title")
    .text(function(d) { return d.data.name; });

  g.selectAll("text")
    .data(root.descendants())
    .enter()
    .append("text")
    .on("click", function(d){
      console.log(d.data.name)
    })
    .attr("fill", "black")
    .attr("transform", function(d) { return "translate(" + arc.centroid(d) + ")"; })
    .attr("dy", "5px")
    .attr("font", "10px")
    .attr("text-anchor", "middle")
    .text(function(d) { 
      //return d.data.name;
      /*
      if(d.data.vm_name != ''){
        return d.data.name
      }
      */
      /*
      if(d.data.source_cluster != ''){
        return d.data.name
      }
      if(d.data.size > 10 * 1000 * 1000 * 1000){
        return d.data.name
      }
      */
      return ''
    })

  /*
  g = d3.select(svg).append("g").attr("transform", "translate(" + width / 2 + "," + (height / 2) + ")");

  var colorScale = d3.scaleOrdinal().range([
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
  ]);
 
  var rScale = d3.scaleLinear()
    .domain([0, radius])
    .range([0.4 * radius, radius]);
 
  root = d3.hierarchy(data);
  root.sum(function(d) { return d.value; })
    .sort(function(a, b) { return b.height - a.height || b.value - a.value; });
 
  var partition = d3.partition()
    .size([2 * Math.PI, radius]);
 
  partition(root);
 
  var arc = d3.arc()
    .startAngle(function(d) { return d.x0; })
    .endAngle(function(d) { return d.x1; })
    .innerRadius(function(d) { return rScale(d.y0); })
    .outerRadius(function(d) { return rScale(d.y1); });
 
  g.selectAll("path")
    .data(root.descendants())
    .enter()
    .append("path")
    .attr("d", arc)
    .attr('stroke', '#fff')
    .attr("fill", function(d) {
      while(d.depth > 1) d = d.parent;
      if(d.depth == 0) return "lightgray";
      return colorScale(d.value);
    })
    .attr("opacity", 0.8)
    .append("title")
    .text(function(d) { return d.data.name + "\n" + d.value; });
 
  g.selectAll("text")
    .data(root.descendants())
    .enter()
    .append("text")
    .attr("fill", "black")
    .attr("transform", function(d) { return "translate(" + arc.centroid(d) + ")"; })
    .attr("dy", "5px")
    .attr("font", "10px")
    .attr("text-anchor", "middle")
    .text(function(d) { return d.data.name; });
  */
}