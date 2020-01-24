let draw_vtree = function(svg, vdisk_id){
  if(vdisk_id == 0){
    return
  }
  $.ajax({type:'get', url:'/api/v1/tree/hierarchy/vdisks/' + vdisk_id,
    success:function(j, status, xhr){
      draw_vtree2(svg, j)
    }, 
    error:function(d){

    }
  })
}


let draw_vtree2 = function(svg, data){
  d3.selectAll(svg + " > *").remove();

  var margin = {top: 50, right: 20, bottom: 50, left: 20}
  let width = document.querySelector(svg).clientWidth;
  //let height = document.querySelector(svg).clientHeight;
  let height = width

  // declares a tree layout and assigns the size
  var treemap = d3.tree().size([width - 40, height - 100]);

  //  assigns the data to a hierarchy using parent-child relationships
  var nodes = d3.hierarchy(data);

  // maps the node data to the tree layout
  nodes = treemap(nodes);

  var g = d3.select(svg)
    .attr('width', width)
    .attr('height', height)
    .append("g")
    .attr("transform",
            "translate(" + margin.left + "," + margin.top + ")");

  // adds the links between the nodes
  var link = g.selectAll(".link")
      .data( nodes.descendants().slice(1))
    .enter().append("path")
      .attr("class", "link")
      .attr("d", function(d) {
         return "M" + d.x + "," + d.y
           + "C" + d.x + "," + (d.y + d.parent.y) / 2
           + " " + d.parent.x + "," +  (d.y + d.parent.y) / 2
           + " " + d.parent.x + "," + d.parent.y;
         });

  // adds each node as a group
  var node = g.selectAll(".node")
      .data(nodes.descendants())
    .enter().append("g")
      .attr("class", function(d) { 
        return "node" + 
          (d.children ? " node--internal" : " node--leaf"); })
      .attr("transform", function(d) { 
        return "translate(" + d.x + "," + d.y + ")"; });

  // adds the circle to the node
  node.append("circle")
    .attr("r", 10);

  // adds the text to the node
  node.append("text")
    .attr("dy", ".35em")
    .attr("y", function(d) { return d.children ? -20 : 20; })
    .style("text-anchor", "middle")
    .text(function(d) { 
      return d.data.name; 
    });

}

