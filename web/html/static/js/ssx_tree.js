let draw = function(svg, data){
  let width = document.querySelector(svg).clientWidth;
  let height = document.querySelector(svg).clientHeight;

  root = d3.hierarchy(data);
  root.x0 = height / 2;
  root.y0 = 0;
  var tree = d3.tree().size([height, width - 160]);

  g = d3.select(svg).append("g").attr("transform", "translate(80,0)");
  update(root);

  function toggle(d) {
    if(d.children) {
      d._children = d.children;
      d.children = null;
    } else {
      d.children = d._children;
      d._children = null;
    }
  }

  var i = 0;
  function update(source) {
 
    tree(root);
 
    root.each(function(d) { d.y = d.depth * 320; });
 
    var node = g.selectAll('.node')
      .data(root.descendants(), function(d) { return d.id || (d.id = ++i); });

    var nodeEnter = node
      .enter()
      .append("g")
      .attr("class", "node")
      .attr("transform", function(d) { return "translate(" + source.y0 + "," + source.x0 + ")"; })
      .on("click", function(d) {
        toggle(d);
        update(d);
      });
   
    nodeEnter.append("circle")
      .attr("r", 5)
      .style("fill", function(d) { return d._children ? "lightsteelblue" : "#fff"; });
   
    nodeEnter.append("text")
      .attr("x", function(d) { return d.children || d._children ? -13 : 13; })
      .attr("dy", "3")
      .attr("font-size", "150%")
      .attr("text-anchor", function(d) { return d.children || d._children ? "end" : "start"; })
      .text(function(d) { return d.data.name; })
      .style("fill-opacity", 1e-6);
   
    var nodeUpdate = nodeEnter.merge(node);
    var duration = 500;

    nodeUpdate.transition()
      .duration(duration)
      .attr("transform", function(d) { return "translate(" + d.y + "," + d.x + ")"; });

    nodeUpdate.select("circle")
      .attr("r", 8)
      .style("fill", function(d) { return d._children ? "lightsteelblue" : "#fff"; });

    nodeUpdate.select("text")
      .style("fill-opacity", 1);

    var nodeExit = node
      .exit()
      .transition()
      .duration(duration)
      .attr("transform", function(d) { return "translate(" + source.y + "," + source.x + ")"; })
      .remove();
   
    nodeExit.select("circle")
      .attr("r", 1e-6);

    nodeExit.select("text")
      .style("fill-opacity", 1e-6);

    var link = g.selectAll(".link")
      .data(root.links(), function(d) { return d.target.id; });

    var linkEnter = link.enter().insert('path', "g")
      .attr("class", "link")
      .attr("d", d3.linkHorizontal()
        .x(function(d) { return source.y0; })
        .y(function(d) { return source.x0; }));

    var linkUpdate = linkEnter.merge(link);
    linkUpdate
      .transition()
      .duration(duration)
      .attr("d", d3.linkHorizontal()
        .x(function(d) { return d.y; })
        .y(function(d) { return d.x; }));

    link
      .exit()
      .transition()
      .duration(duration)
      .attr("d", d3.linkHorizontal()
        .x(function(d) { return source.y; })
        .y(function(d) { return source.x; })
      )
      .remove();

    node.each(function(d) {
      d.x0 = d.x;
      d.y0 = d.y;
    });
  }
}
