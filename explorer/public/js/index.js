const width = 1600;
const height = 800;

var links;
var nodes;

var simulation;
var transform;

var canvas = d3.select("canvas");
var context = canvas.node().getContext('2d');


var xmlhttp = new XMLHttpRequest();
var tissue = "cochlea"


d3.select("select")
    .on("change",function(d){
        var selected = d3.select("#d3-dropdown").node().value;
        tissue = selected;
        load_data(tissue);
    })


get_graph()


function load_data(tissue){
    xmlhttp.open("GET", '/load-data/'+tissue, true);
    xmlhttp.setRequestHeader('Content-type', 'application/json; charset=utf-8');

    xmlhttp.onreadystatechange = function () {
        if (xmlhttp.readyState == 4 && xmlhttp.status == "200") {
            get_graph();
        }
    }
    xmlhttp.send();
}


function get_graph(){
    xmlhttp.open("GET", '/get-graph', true);
    xmlhttp.setRequestHeader('Content-type', 'application/json; charset=utf-8');

    xmlhttp.onreadystatechange = function () {
        if (xmlhttp.readyState == 4 && xmlhttp.status == "200") {
            data = JSON.parse(xmlhttp.responseText);
            links = data.links;
            nodes = data.nodes;

            simulation = d3.forceSimulation(nodes)
                .force("center", d3.forceCenter(width / 2, height / 2))
                .force("charge", d3.forceManyBody().strength(-50))
                .force("link", d3.forceLink().strength(0.1).id(function (d) { return d.id; }))
                .force('collision', d3.forceCollide().radius(function(d) {
                    return 2 + d.bc * 100;
                }))
                .alphaTarget(0)
                .alphaDecay(0.05);
            

            transform = d3.zoomIdentity;

            d3.select(context.canvas)
                .call(d3.drag().subject(dragsubject).on("start", dragstarted).on("drag", dragged).on("end", dragended))
                .call(d3.zoom().scaleExtent([1 / 10, 8]).on("zoom", zoomed));
            
            d3.select(context.canvas).on("click", function(d){
                    show_properties(d);
                });

            simulation.nodes(nodes)
                .on("tick", simulationUpdate);

            simulation.force("link")
                .links(links);
            
        }
    }
    xmlhttp.send();
}



function show_properties(event){
    protein_id = find_protein_id(event);
   
    if (protein_id != null) {
        xmlhttp.open("GET", '/protein-properties'+"/"+protein_id.toString(), true);
        xmlhttp.setRequestHeader('Content-type', 'application/json; charset=utf-8');

        xmlhttp.onreadystatechange = function () {
            if (xmlhttp.readyState == 4 && xmlhttp.status == "200") {
                data = JSON.parse(xmlhttp.responseText);
                var properties = data.properties;

                d3.select('#tooltip')
                    .style("visibility", "visible")
                    .style('opacity', 0.85)
                    .style('top', event.y + 'px')
                    .style('left', event.x + 'px')
                    .html(
                        'EntrezGeneID: ' + properties["EntrezGeneID"].toString() + '<br>' +
                        'OfficialSymbol: ' + properties['OfficialSymbol'] + '<br>' +
                        'OfficialFullName: ' + properties['OfficialFullName'] + '<br>' +
                        'Summary: ' + properties['Summary'] + '<br>' +
                        'BetweennessCentrality: ' + properties['BetweennessCentrality'].toString());
            }
        }
        xmlhttp.send();
    } else {
        d3.select('#tooltip').style("visibility", "hidden");
    }
}


function get_mouse_pos(evt) {
    var rect = canvas.node().getBoundingClientRect();
    return {
      x: evt.clientX - rect.left,
      y: evt.clientY - rect.top
    };
}


function find_protein_id(event){
    var pos = get_mouse_pos(event);
    var result = null
    nodes.forEach(function (d, i) {
        if (Math.sqrt(Math.pow((d.new_x - pos.x), 2) + Math.pow((d.new_y - pos.y), 2)) < radius(d) * transform.k){
            result = d.id
        }
    });
    return result;
}


function radius(d){
    return 2 + d.bc * 100;
}


function alpha(d){
    return 0.1 + d.source.bc * d.target.bc * 1000;
}


function zoomed(event) {
    transform = event.transform;
    simulationUpdate();
}


function dragsubject(event) {
    var i,
        x = transform.invertX(event.x),
        y = transform.invertY(event.y),
        dx,
        dy;
    for (i = nodes.length - 1; i >= 0; --i) {
        node = nodes[i];
        dx = x - node.x;
        dy = y - node.y;

        if (dx * dx + dy * dy < radius * radius) {
            node.x = transform.applyX(node.x);
            node.y = transform.applyY(node.y);
            return node;
        }
    }
}


function simulationUpdate() {
    context.save();
    context.clearRect(0, 0, width, height);
    context.translate(transform.x, transform.y);
    context.scale(transform.k, transform.k);

    links.forEach(function (d) {
        context.beginPath();

        context.globalAlpha = alpha(d);

        context.moveTo(d.source.x, d.source.y);
        context.lineTo(d.target.x, d.target.y);

        context.strokeStyle = "#7ecd8a";
        context.stroke();

        context.globalAlpha = 1;
    });
    nodes.forEach(function (d, i) {
        context.beginPath();

        context.shadowColor = " #7ecd8a";
        context.shadowBlur = 10 + d.bc * 1000;

        context.fillStyle = "#5abf69";
        context.arc(d.x, d.y, radius(d), 0, 2 * Math.PI, true);
        context.fill();

        context.strokeStyle = "#245c2c";

        context.font = "5px Comic Sans MS";
        context.fillStyle = "#15371a";
        context.textAlign = "center";
        context.fillText(d.symbol, d.x, d.y + radius(d) + 5);

        context.stroke();
        
        d.new_x = (d.x * transform.k + transform.x);
        d.new_y = (d.y * transform.k + transform.y);
    });
    
    context.restore();
}


function dragstarted(event) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    event.subject.fx = transform.invertX(event.x);
    event.subject.fy = transform.invertY(event.y);
}


function dragged(event) {
    event.subject.fx = transform.invertX(event.x);
    event.subject.fy = transform.invertY(event.y);
}


function dragended(event) {
    if (!event.active) simulation.alphaTarget(0);
    event.subject.fx = null;
    event.subject.fy = null;
}

