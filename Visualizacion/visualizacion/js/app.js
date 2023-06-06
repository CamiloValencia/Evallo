// Fetch data using Apache Jena Fuseki endpoint
const queryEndpoint = 'https://apevallows.azure-api.net/Evallo/query';
const query = `
  PREFIX ex: <http://example.org/>
  SELECT ?subject ?predicate ?object
  WHERE {
    ?subject ?predicate ?object .
  }
  LIMIT 100
`;

const results = await fetch(`${queryEndpoint}?query=${encodeURIComponent(query)}`, {
  headers: { 'Accept': 'application/sparql-results+json' }
})
  .then(response => response.json())
  .then(data => data.results.bindings);

// Convert SPARQL query results to a graph object
const graph = { nodes: [], links: [] };
const nodeMap = new Map();

for (const result of results) {
  const { subject, predicate, object } = result;

  let subjectNode = nodeMap.get(subject.value);
  if (!subjectNode) {
    subjectNode = { id: subject.value, label: subject.value };
    nodeMap.set(subject.value, subjectNode);
    graph.nodes.push(subjectNode);
  }

  let objectNode = nodeMap.get(object.value);
  if (!objectNode) {
    objectNode = { id: object.value, label: object.value };
    nodeMap.set(object.value, objectNode);
    graph.nodes.push(objectNode);
  }

  graph.links.push({
    source: subject.value,
    target: object.value,
    label: predicate.value
  });
}

// Visualize graph using D3.js force-directed layout
const width = 800;
const height = 600;

const svg = d3.select('body').append('svg')
  .attr('width', width)
  .attr('height', height);

const simulation = d3.forceSimulation(graph.nodes)
  .force('link', d3.forceLink(graph.links).id(d => d.id))
  .force('charge', d3.forceManyBody())
  .force('center', d3.forceCenter(width / 2, height / 2));

const link = svg.selectAll('.link')
  .data(graph.links)
  .enter().append('line')
  .attr('class', 'link')
  .attr('stroke-width', 2);

const node = svg.selectAll('.node')
  .data(graph.nodes)
  .enter().append('circle')
  .attr('class', 'node')
  .attr('r', 10)
  .call(d3.drag()
    .on('start', dragstarted)
    .on('drag', dragged)
    .on('end', dragended));

const label = svg.selectAll('.label')
  .data(graph.nodes)
  .enter().append('text')
  .attr('class', 'label')
  .text(d => d.label)
  .attr('font-size', 12)
  .attr('dx', 15)
  .attr('dy', 4);

simulation.on('tick', () => {
  link.attr('x1', d => d.source.x)
    .attr('y1', d => d.source.y)
    .attr('x2', d => d.target.x)
    .attr('y2', d => d.target.y);

  node.attr('cx', d => d.x)
    .attr('cy', d => d.y);

  label.attr('x', d => d.x)
    .attr('y', d => d.y);
});

function dragstarted(d) {
  if (!d3.event.active) simulation.alphaTarget(0.3).restart();
  d.fx = d.x;
  d.fy = d.y;
}