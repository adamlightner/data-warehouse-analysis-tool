/**
 * DWAT Lineage Visualization
 * Interactive DAG visualization using D3.js and Dagre
 */

(function() {
    'use strict';

    // ============================================
    // Configuration
    // ============================================
    const CONFIG = {
        nodeWidth: 180,
        nodeHeight: 40,
        nodePadding: 20,
        rankSep: 80,
        nodeSep: 40,
        edgeSep: 20,
        zoomExtent: [0.1, 4],
        transitionDuration: 500,
        searchDebounce: 200
    };

    // Node type color mapping
    const NODE_COLORS = {
        // DAG container
        dag: { fill: '#f1f5f9', stroke: '#94a3b8' },
        // Operator types (DAG view)
        PythonOperator: { fill: '#dbeafe', stroke: '#3b82f6' },
        SnowflakeOperator: { fill: '#e0e7ff', stroke: '#6366f1' },
        BashOperator: { fill: '#dcfce7', stroke: '#22c55e' },
        PostgresOperator: { fill: '#f3e8ff', stroke: '#a855f7' },
        BigQueryOperator: { fill: '#fce7f3', stroke: '#ec4899' },
        SparkOperator: { fill: '#ffedd5', stroke: '#f97316' },
        EmailOperator: { fill: '#ccfbf1', stroke: '#14b8a6' },
        // Data layer types (Table view)
        source: { fill: '#f3e8ff', stroke: '#a855f7' },
        staging: { fill: '#e0e7ff', stroke: '#6366f1' },
        dimension: { fill: '#fce7f3', stroke: '#ec4899' },
        fact: { fill: '#ccfbf1', stroke: '#14b8a6' },
        table: { fill: '#dbeafe', stroke: '#3b82f6' },
        // Fallbacks
        task: { fill: '#dcfce7', stroke: '#22c55e' },
        default: { fill: '#f1f5f9', stroke: '#64748b' }
    };

    // ============================================
    // State
    // ============================================
    let allGraphs = null;      // All view mode graphs { dag: {...}, table: {...}, metric: {...} }
    let graphData = null;      // Current active graph
    let svg = null;
    let g = null;
    let zoom = null;
    let selectedNode = null;
    let visibleNodes = new Set();
    let visibleEdges = new Set();
    let currentViewMode = 'dag';

    // ============================================
    // Initialization
    // ============================================
    function init() {
        // Load graph data
        const dataElement = document.getElementById('graph-data');
        if (!dataElement) {
            console.error('No graph data element found');
            return;
        }

        try {
            allGraphs = JSON.parse(dataElement.textContent);
        } catch (e) {
            console.error('Failed to parse graph data:', e);
            return;
        }

        // Set initial view mode
        switchViewMode('dag');

        // Setup visualization
        setupSVG();
        setupZoom();
        setupControls();
        setupSearch();
        setupLegend();
        render();
        fitToView();
    }

    // ============================================
    // Switch View Mode
    // ============================================
    function switchViewMode(mode) {
        currentViewMode = mode;
        graphData = allGraphs[mode] || allGraphs.dag;

        // Reset visibility sets
        visibleNodes.clear();
        visibleEdges.clear();
        graphData.nodes.forEach(n => visibleNodes.add(n.id));
        graphData.edges.forEach((_, i) => visibleEdges.add(i));

        // Clear selection
        selectedNode = null;
    }

    // ============================================
    // SVG Setup
    // ============================================
    function setupSVG() {
        const container = document.getElementById('graph-container');
        const width = container.clientWidth;
        const height = container.clientHeight;

        svg = d3.select('#graph-container')
            .append('svg')
            .attr('width', width)
            .attr('height', height);

        // Arrow marker definition - smaller and sleeker
        svg.append('defs')
            .append('marker')
            .attr('id', 'arrowhead')
            .attr('viewBox', '-6 -3 6 6')
            .attr('refX', 0)
            .attr('refY', 0)
            .attr('markerWidth', 5)
            .attr('markerHeight', 5)
            .attr('orient', 'auto')
            .append('path')
            .attr('d', 'M-6,-3L0,0L-6,3')
            .attr('fill', '#94a3b8');

        // Highlighted arrow marker
        svg.select('defs')
            .append('marker')
            .attr('id', 'arrowhead-highlighted')
            .attr('viewBox', '-6 -3 6 6')
            .attr('refX', 0)
            .attr('refY', 0)
            .attr('markerWidth', 5)
            .attr('markerHeight', 5)
            .attr('orient', 'auto')
            .append('path')
            .attr('d', 'M-6,-3L0,0L-6,3')
            .attr('fill', '#f59e0b');

        g = svg.append('g').attr('class', 'graph');
    }

    // ============================================
    // Zoom Setup
    // ============================================
    function setupZoom() {
        zoom = d3.zoom()
            .scaleExtent(CONFIG.zoomExtent)
            .on('zoom', (event) => {
                g.attr('transform', event.transform);
            });

        svg.call(zoom);
    }

    // ============================================
    // Controls Setup
    // ============================================
    function setupControls() {
        // Reset view
        document.getElementById('reset-view').addEventListener('click', () => {
            resetView();
        });

        // Zoom in
        document.getElementById('zoom-in').addEventListener('click', () => {
            svg.transition().duration(300).call(zoom.scaleBy, 1.3);
        });

        // Zoom out
        document.getElementById('zoom-out').addEventListener('click', () => {
            svg.transition().duration(300).call(zoom.scaleBy, 0.7);
        });

        // Fit to view
        document.getElementById('fit-view').addEventListener('click', fitToView);

        // Show upstream
        document.getElementById('show-upstream').addEventListener('click', () => {
            if (selectedNode) {
                showLineage(selectedNode, 'upstream');
            }
        });

        // Show downstream
        document.getElementById('show-downstream').addEventListener('click', () => {
            if (selectedNode) {
                showLineage(selectedNode, 'downstream');
            }
        });

        // Show all
        document.getElementById('show-all').addEventListener('click', () => {
            showAllNodes();
        });

        // Info panel close
        document.getElementById('info-close').addEventListener('click', () => {
            closeInfoPanel();
        });

        // Filter by type
        document.getElementById('node-type-filter').addEventListener('change', (e) => {
            filterByType(e.target.value);
        });

        // View mode toggle
        setupViewModeToggle();

        // Window resize
        window.addEventListener('resize', () => {
            const container = document.getElementById('graph-container');
            svg.attr('width', container.clientWidth)
               .attr('height', container.clientHeight);
        });
    }

    // ============================================
    // Search Setup
    // ============================================
    function setupSearch() {
        const input = document.getElementById('search-input');
        const dropdown = document.getElementById('search-dropdown');
        let debounceTimer = null;

        input.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                const query = e.target.value.toLowerCase().trim();
                if (query.length < 2) {
                    dropdown.classList.add('hidden');
                    return;
                }

                const matches = graphData.nodes.filter(n =>
                    n.label.toLowerCase().includes(query) ||
                    (n.type && n.type.toLowerCase().includes(query))
                ).slice(0, 10);

                if (matches.length === 0) {
                    dropdown.classList.add('hidden');
                    return;
                }

                dropdown.innerHTML = matches.map(n => `
                    <div class="dropdown-item" data-id="${n.id}">
                        ${n.label}
                        <span class="node-type">${n.type || 'node'}</span>
                    </div>
                `).join('');
                dropdown.classList.remove('hidden');

                dropdown.querySelectorAll('.dropdown-item').forEach(item => {
                    item.addEventListener('click', () => {
                        const nodeId = item.dataset.id;
                        selectNode(nodeId);
                        centerOnNode(nodeId);
                        dropdown.classList.add('hidden');
                        input.value = '';
                    });
                });
            }, CONFIG.searchDebounce);
        });

        // Close dropdown on outside click
        document.addEventListener('click', (e) => {
            if (!e.target.closest('#search-container')) {
                dropdown.classList.add('hidden');
            }
        });
    }

    // ============================================
    // Legend Setup
    // ============================================
    function setupLegend() {
        const types = new Set(graphData.nodes.map(n => n.type || 'default'));
        const legendItems = document.getElementById('legend-items');
        const filterSelect = document.getElementById('node-type-filter');

        legendItems.innerHTML = '';

        types.forEach(type => {
            const colors = NODE_COLORS[type] || NODE_COLORS.default;
            legendItems.innerHTML += `
                <div class="legend-item">
                    <div class="legend-color" style="background: ${colors.fill}; border-color: ${colors.stroke};"></div>
                    <span>${type}</span>
                </div>
            `;

            // Add to filter dropdown
            const option = document.createElement('option');
            option.value = type;
            option.textContent = type.charAt(0).toUpperCase() + type.slice(1);
            filterSelect.appendChild(option);
        });
    }

    // ============================================
    // View Mode Toggle
    // ============================================
    function setupViewModeToggle() {
        const toggleButtons = document.querySelectorAll('#view-mode-toggle .toggle-btn');

        toggleButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                // Update active state
                toggleButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                // Switch to new view mode
                const mode = btn.dataset.mode;
                switchViewMode(mode);

                // Re-render and update UI
                render();
                setupLegend();
                fitToView();
                closeInfoPanel();
            });
        });
    }

    // ============================================
    // Graph Rendering
    // ============================================
    function render() {

        // Show "coming soon" banner for empty views (e.g. metric)
        if (graphData.nodes.length === 0) {
            g.selectAll('*').remove();
            const container = document.getElementById('graph-container');
            const cx = container.clientWidth / 2;
            const cy = container.clientHeight / 2;

            // Reset zoom so banner is centered
            svg.call(zoom.transform, d3.zoomIdentity);

            const banner = g.append('g').attr('transform', `translate(${cx}, ${cy})`);
            banner.append('rect')
                .attr('x', -160)
                .attr('y', -40)
                .attr('width', 320)
                .attr('height', 80)
                .attr('rx', 12)
                .attr('fill', '#f1f5f9')
                .attr('stroke', '#cbd5e1')
                .attr('stroke-width', 1.5)
                .attr('stroke-dasharray', '6 4');
            banner.append('text')
                .attr('text-anchor', 'middle')
                .attr('dy', '0.35em')
                .attr('font-size', '18px')
                .attr('font-weight', '600')
                .attr('fill', '#64748b')
                .text('Coming Soon');
            return;
        }

        // Separate DAG nodes (clusters) from regular nodes
        const dagNodes = graphData.nodes.filter(n => n.type === 'dag' && visibleNodes.has(n.id));
        const taskNodes = graphData.nodes.filter(n => n.type !== 'dag' && visibleNodes.has(n.id));

        // If no DAG clusters, use simple flat layout (e.g. table view)
        if (dagNodes.length === 0) {
            renderFlat(taskNodes);
            return;
        }

        // Group tasks by their parent DAG
        const dagTaskGroups = {};
        dagNodes.forEach(dag => {
            const dagName = dag.label;
            dagTaskGroups[dagName] = taskNodes.filter(n => n.dag === dagName);
        });

        // Layout each DAG's tasks independently, then stack them vertically
        const clusterPadding = { top: 45, bottom: 25, left: 30, right: 30 };
        const clusterGap = 40;
        const dagLayouts = {}; // { dagName: { nodes: {id: {x,y}}, edges: [...], bbox } }

        dagNodes.forEach(dag => {
            const dagName = dag.label;
            const tasks = dagTaskGroups[dagName] || [];
            if (tasks.length === 0) return;

            // Create a separate dagre graph for this DAG's tasks
            const subGraph = new dagre.graphlib.Graph();
            subGraph.setGraph({
                rankdir: 'LR',
                ranksep: CONFIG.rankSep,
                nodesep: CONFIG.nodeSep,
                edgesep: CONFIG.edgeSep
            });
            subGraph.setDefaultEdgeLabel(() => ({}));

            const taskIds = new Set(tasks.map(t => t.id));
            tasks.forEach(t => {
                subGraph.setNode(t.id, {
                    label: t.label,
                    width: CONFIG.nodeWidth,
                    height: CONFIG.nodeHeight
                });
            });

            // Add edges only within this DAG
            graphData.edges.forEach(edge => {
                if (edge.source.startsWith('dag:')) return;
                if (taskIds.has(edge.source) && taskIds.has(edge.target)) {
                    subGraph.setEdge(edge.source, edge.target);
                }
            });

            dagre.layout(subGraph);

            // Collect positioned nodes and compute bounding box
            const positioned = {};
            let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
            tasks.forEach(t => {
                const n = subGraph.node(t.id);
                positioned[t.id] = { x: n.x, y: n.y };
                minX = Math.min(minX, n.x - CONFIG.nodeWidth / 2);
                maxX = Math.max(maxX, n.x + CONFIG.nodeWidth / 2);
                minY = Math.min(minY, n.y - CONFIG.nodeHeight / 2);
                maxY = Math.max(maxY, n.y + CONFIG.nodeHeight / 2);
            });

            // Collect edge points
            const edgePoints = {};
            graphData.edges.forEach(edge => {
                if (edge.source.startsWith('dag:')) return;
                if (taskIds.has(edge.source) && taskIds.has(edge.target)) {
                    const de = subGraph.edge(edge.source, edge.target);
                    if (de) edgePoints[`${edge.source}|${edge.target}`] = de.points;
                }
            });

            dagLayouts[dagName] = {
                nodes: positioned,
                edgePoints,
                contentWidth: maxX - minX,
                contentHeight: maxY - minY,
                // Offset to normalize positions so content starts at (0,0)
                originX: minX,
                originY: minY
            };
        });

        // Compute uniform cluster size from largest content
        let maxContentWidth = 0, maxContentHeight = 0;
        Object.values(dagLayouts).forEach(layout => {
            maxContentWidth = Math.max(maxContentWidth, layout.contentWidth);
            maxContentHeight = Math.max(maxContentHeight, layout.contentHeight);
        });

        const uniformWidth = clusterPadding.left + maxContentWidth + clusterPadding.right;
        const uniformHeight = clusterPadding.top + maxContentHeight + clusterPadding.bottom;

        // Position each cluster: all left-aligned, stacked vertically
        let currentY = 0;
        const clusterPositions = {}; // { dagName: { x, y } } — top-left corner

        dagNodes.forEach(dag => {
            const dagName = dag.label;
            if (!dagLayouts[dagName]) return;
            clusterPositions[dagName] = { x: 0, y: currentY };
            currentY += uniformHeight + clusterGap;
        });

        // Clear previous render
        g.selectAll('*').remove();

        // Render DAG clusters (containers) first (background)
        const clusterGroup = g.append('g').attr('class', 'clusters');

        dagNodes.forEach(dag => {
            const dagName = dag.label;
            const layout = dagLayouts[dagName];
            const pos = clusterPositions[dagName];
            if (!layout || !pos) return;

            // Store position (center) for info panel / selection
            dag.x = pos.x + uniformWidth / 2;
            dag.y = pos.y + uniformHeight / 2;

            const clusterG = clusterGroup.append('g')
                .attr('class', 'cluster type-dag')
                .attr('data-id', dag.id)
                .attr('transform', `translate(${pos.x}, ${pos.y})`);

            // Cluster background rectangle
            clusterG.append('rect')
                .attr('width', uniformWidth)
                .attr('height', uniformHeight)
                .attr('rx', 8)
                .attr('ry', 8)
                .attr('fill', '#f1f5f9')
                .attr('stroke', '#94a3b8')
                .attr('stroke-width', 1.5)
                .attr('stroke-dasharray', '6 4')
                .attr('opacity', 0.7);

            // Cluster label at upper left
            clusterG.append('text')
                .attr('x', 14)
                .attr('y', 22)
                .attr('text-anchor', 'start')
                .attr('font-weight', '600')
                .attr('font-size', '13px')
                .attr('fill', '#475569')
                .text(dagName);

            // Click handler for cluster
            clusterG.on('click', () => selectNode(dag.id));
        });

        // Helper: compute absolute position for a task node
        function getTaskAbsolutePos(node) {
            const dagName = node.dag;
            const layout = dagLayouts[dagName];
            const pos = clusterPositions[dagName];
            if (!layout || !pos || !layout.nodes[node.id]) return null;
            const local = layout.nodes[node.id];
            return {
                x: pos.x + clusterPadding.left + (local.x - layout.originX),
                y: pos.y + clusterPadding.top + (local.y - layout.originY)
            };
        }

        // Render edges
        const edgeGroup = g.append('g').attr('class', 'edges');
        graphData.edges.forEach((edge, i) => {
            if (!visibleEdges.has(i) || !visibleNodes.has(edge.source) || !visibleNodes.has(edge.target)) {
                return;
            }
            // Skip DAG->task edges (shown by containment)
            if (edge.source.startsWith('dag:')) return;

            // Find which DAG this edge belongs to
            const srcNode = graphData.nodes.find(n => n.id === edge.source);
            if (!srcNode || !srcNode.dag) return;
            const dagName = srcNode.dag;
            const layout = dagLayouts[dagName];
            const pos = clusterPositions[dagName];
            if (!layout || !pos) return;

            const key = `${edge.source}|${edge.target}`;
            const points = layout.edgePoints[key];
            if (!points) return;

            // Offset edge points to absolute position
            const offsetPoints = points.map(p => ({
                x: pos.x + clusterPadding.left + (p.x - layout.originX),
                y: pos.y + clusterPadding.top + (p.y - layout.originY)
            }));

            const pathG = edgeGroup.append('g')
                .attr('class', 'edge')
                .attr('data-source', edge.source)
                .attr('data-target', edge.target);

            const line = d3.line()
                .x(d => d.x)
                .y(d => d.y)
                .curve(d3.curveBasis);

            pathG.append('path')
                .attr('d', line(offsetPoints))
                .attr('marker-end', 'url(#arrowhead)');
        });

        // Render task nodes (on top of clusters)
        const nodeGroup = g.append('g').attr('class', 'nodes');
        taskNodes.forEach(node => {
            const absPos = getTaskAbsolutePos(node);
            if (!absPos) return;

            const nodeType = node.type || 'default';
            const nodeG = nodeGroup.append('g')
                .attr('class', `node type-${nodeType}`)
                .attr('data-id', node.id)
                .attr('transform', `translate(${absPos.x - CONFIG.nodeWidth/2}, ${absPos.y - CONFIG.nodeHeight/2})`);

            // Store position for later use
            node.x = absPos.x;
            node.y = absPos.y;

            // Node rectangle
            nodeG.append('rect')
                .attr('width', CONFIG.nodeWidth)
                .attr('height', CONFIG.nodeHeight)
                .attr('rx', 6)
                .attr('ry', 6);

            // Node label
            nodeG.append('text')
                .attr('x', CONFIG.nodeWidth / 2)
                .attr('y', CONFIG.nodeHeight / 2)
                .attr('dy', '0.35em')
                .attr('text-anchor', 'middle')
                .text(truncateLabel(node.label, 20));

            // Click handler
            nodeG.on('click', () => {
                selectNode(node.id);
            });

            // Drag behavior
            const drag = d3.drag()
                .on('start', function() {
                    d3.select(this).classed('dragging', true);
                })
                .on('drag', function(event) {
                    const newX = event.x - CONFIG.nodeWidth / 2;
                    const newY = event.y - CONFIG.nodeHeight / 2;
                    d3.select(this).attr('transform', `translate(${newX}, ${newY})`);
                    node.x = event.x;
                    node.y = event.y;
                    updateEdgesForNode(node.id);
                })
                .on('end', function() {
                    d3.select(this).classed('dragging', false);
                });

            nodeG.call(drag);
        });
    }

    // ============================================
    // Flat Layout (no clusters — used for table/metric views)
    // ============================================
    function renderFlat(nodes) {
        const flatGraph = new dagre.graphlib.Graph();
        flatGraph.setGraph({
            rankdir: 'LR',
            ranksep: CONFIG.rankSep,
            nodesep: CONFIG.nodeSep,
            edgesep: CONFIG.edgeSep
        });
        flatGraph.setDefaultEdgeLabel(() => ({}));

        nodes.forEach(node => {
            flatGraph.setNode(node.id, {
                label: node.label,
                width: CONFIG.nodeWidth,
                height: CONFIG.nodeHeight
            });
        });

        const nodeIds = new Set(nodes.map(n => n.id));
        graphData.edges.forEach((edge, i) => {
            if (!visibleEdges.has(i)) return;
            if (nodeIds.has(edge.source) && nodeIds.has(edge.target)) {
                flatGraph.setEdge(edge.source, edge.target);
            }
        });

        dagre.layout(flatGraph);

        // Clear previous render
        g.selectAll('*').remove();

        // Render edges
        const edgeGroup = g.append('g').attr('class', 'edges');
        graphData.edges.forEach((edge, i) => {
            if (!visibleEdges.has(i)) return;
            if (!nodeIds.has(edge.source) || !nodeIds.has(edge.target)) return;

            const dagreEdge = flatGraph.edge(edge.source, edge.target);
            if (!dagreEdge) return;

            const pathG = edgeGroup.append('g')
                .attr('class', 'edge')
                .attr('data-source', edge.source)
                .attr('data-target', edge.target);

            const line = d3.line()
                .x(d => d.x)
                .y(d => d.y)
                .curve(d3.curveBasis);

            pathG.append('path')
                .attr('d', line(dagreEdge.points))
                .attr('marker-end', 'url(#arrowhead)');
        });

        // Render nodes
        const nodeGroup = g.append('g').attr('class', 'nodes');
        nodes.forEach(node => {
            const dagreNode = flatGraph.node(node.id);
            if (!dagreNode) return;

            const nodeType = node.type || 'default';
            const nodeG = nodeGroup.append('g')
                .attr('class', `node type-${nodeType}`)
                .attr('data-id', node.id)
                .attr('transform', `translate(${dagreNode.x - CONFIG.nodeWidth/2}, ${dagreNode.y - CONFIG.nodeHeight/2})`);

            node.x = dagreNode.x;
            node.y = dagreNode.y;

            nodeG.append('rect')
                .attr('width', CONFIG.nodeWidth)
                .attr('height', CONFIG.nodeHeight)
                .attr('rx', 6)
                .attr('ry', 6);

            nodeG.append('text')
                .attr('x', CONFIG.nodeWidth / 2)
                .attr('y', CONFIG.nodeHeight / 2)
                .attr('dy', '0.35em')
                .attr('text-anchor', 'middle')
                .text(truncateLabel(node.label, 20));

            nodeG.on('click', () => selectNode(node.id));

            const drag = d3.drag()
                .on('start', function() {
                    d3.select(this).classed('dragging', true);
                })
                .on('drag', function(event) {
                    const newX = event.x - CONFIG.nodeWidth / 2;
                    const newY = event.y - CONFIG.nodeHeight / 2;
                    d3.select(this).attr('transform', `translate(${newX}, ${newY})`);
                    node.x = event.x;
                    node.y = event.y;
                    updateEdgesForNode(node.id);
                })
                .on('end', function() {
                    d3.select(this).classed('dragging', false);
                });

            nodeG.call(drag);
        });
    }

    // ============================================
    // Edge Update (for drag) - only updates edges for specific node
    // ============================================
    function updateEdgesForNode(nodeId) {
        g.selectAll('.edge').each(function() {
            const edge = d3.select(this);
            const sourceId = edge.attr('data-source');
            const targetId = edge.attr('data-target');

            // Only update edges connected to the dragged node
            if (sourceId !== nodeId && targetId !== nodeId) return;

            const sourceNode = graphData.nodes.find(n => n.id === sourceId);
            const targetNode = graphData.nodes.find(n => n.id === targetId);

            if (sourceNode && targetNode && sourceNode.x && targetNode.x) {
                updateEdgePath(edge, sourceNode, targetNode);
            }
        });
    }

    function updateEdgePath(edge, sourceNode, targetNode) {
        const startX = sourceNode.x + CONFIG.nodeWidth / 2;
        const startY = sourceNode.y;
        const endX = targetNode.x - CONFIG.nodeWidth / 2;
        const endY = targetNode.y;

        // Horizontal offset for control points (creates smooth curve)
        const cpOffset = Math.abs(endX - startX) * 0.4;

        const points = [
            { x: startX, y: startY },
            { x: startX + cpOffset, y: startY },
            { x: endX - cpOffset, y: endY },
            { x: endX, y: endY }
        ];

        const line = d3.line()
            .x(d => d.x)
            .y(d => d.y)
            .curve(d3.curveBasis);

        edge.select('path').attr('d', line(points));
    }

    // ============================================
    // Node Selection
    // ============================================
    function selectNode(nodeId) {
        // Clear previous selection
        g.selectAll('.node').classed('selected', false);

        // Select new node
        selectedNode = nodeId;
        g.select(`.node[data-id="${CSS.escape(nodeId)}"]`).classed('selected', true);

        // Show info panel
        const node = graphData.nodes.find(n => n.id === nodeId);
        if (node) {
            showInfoPanel(node);
        }

        // Highlight lineage
        highlightLineage(nodeId);
    }

    // ============================================
    // Lineage Highlighting
    // ============================================
    function highlightLineage(nodeId) {
        const upstream = getUpstream(nodeId);
        const downstream = getDownstream(nodeId);
        const lineage = new Set([nodeId, ...upstream, ...downstream]);

        // Dim non-lineage nodes
        g.selectAll('.node').each(function() {
            const id = d3.select(this).attr('data-id');
            d3.select(this).classed('dimmed', !lineage.has(id));
        });

        // Highlight lineage edges
        g.selectAll('.edge').each(function() {
            const source = d3.select(this).attr('data-source');
            const target = d3.select(this).attr('data-target');
            const isLineageEdge = lineage.has(source) && lineage.has(target);
            d3.select(this).classed('dimmed', !isLineageEdge);
            d3.select(this).classed('highlighted', isLineageEdge);
            d3.select(this).select('path')
                .attr('marker-end', isLineageEdge ? 'url(#arrowhead-highlighted)' : 'url(#arrowhead)');
        });
    }

    function getUpstream(nodeId, visited = new Set()) {
        if (visited.has(nodeId)) return [];
        visited.add(nodeId);

        const upstream = [];
        graphData.edges.forEach(edge => {
            if (edge.target === nodeId) {
                upstream.push(edge.source);
                upstream.push(...getUpstream(edge.source, visited));
            }
        });
        return upstream;
    }

    function getDownstream(nodeId, visited = new Set()) {
        if (visited.has(nodeId)) return [];
        visited.add(nodeId);

        const downstream = [];
        graphData.edges.forEach(edge => {
            if (edge.source === nodeId) {
                downstream.push(edge.target);
                downstream.push(...getDownstream(edge.target, visited));
            }
        });
        return downstream;
    }

    // ============================================
    // Show Lineage (filter view)
    // ============================================
    function showLineage(nodeId, direction) {
        visibleNodes.clear();
        visibleEdges.clear();

        visibleNodes.add(nodeId);

        if (direction === 'upstream' || direction === 'both') {
            const upstream = getUpstream(nodeId);
            upstream.forEach(id => visibleNodes.add(id));
        }

        if (direction === 'downstream' || direction === 'both') {
            const downstream = getDownstream(nodeId);
            downstream.forEach(id => visibleNodes.add(id));
        }

        // Add relevant edges
        graphData.edges.forEach((edge, i) => {
            if (visibleNodes.has(edge.source) && visibleNodes.has(edge.target)) {
                visibleEdges.add(i);
            }
        });

        render();
        fitToView();
    }

    // ============================================
    // Show All Nodes
    // ============================================
    function showAllNodes() {
        graphData.nodes.forEach(n => visibleNodes.add(n.id));
        graphData.edges.forEach((e, i) => visibleEdges.add(i));

        selectedNode = null;
        render();
        fitToView();
        closeInfoPanel();
    }

    // ============================================
    // Filter by Type
    // ============================================
    function filterByType(type) {
        visibleNodes.clear();
        visibleEdges.clear();

        if (type === 'all') {
            graphData.nodes.forEach(n => visibleNodes.add(n.id));
            graphData.edges.forEach((e, i) => visibleEdges.add(i));
        } else {
            graphData.nodes.forEach(n => {
                if ((n.type || 'default') === type) {
                    visibleNodes.add(n.id);
                }
            });

            // Add edges between visible nodes
            graphData.edges.forEach((edge, i) => {
                if (visibleNodes.has(edge.source) && visibleNodes.has(edge.target)) {
                    visibleEdges.add(i);
                }
            });
        }

        render();
        fitToView();
    }

    // ============================================
    // View Controls
    // ============================================
    function fitToView() {
        const container = document.getElementById('graph-container');
        const width = container.clientWidth;
        const height = container.clientHeight;

        const bounds = g.node().getBBox();
        if (bounds.width === 0 || bounds.height === 0) return;

        const padding = 50;
        const scale = Math.min(
            (width - padding * 2) / bounds.width,
            (height - padding * 2) / bounds.height,
            1
        );

        const translateX = (width - bounds.width * scale) / 2 - bounds.x * scale;
        const translateY = (height - bounds.height * scale) / 2 - bounds.y * scale;

        svg.transition()
            .duration(CONFIG.transitionDuration)
            .call(zoom.transform, d3.zoomIdentity.translate(translateX, translateY).scale(scale));
    }

    function centerOnNode(nodeId) {
        const node = graphData.nodes.find(n => n.id === nodeId);
        if (!node || !node.x) return;

        const container = document.getElementById('graph-container');
        const width = container.clientWidth;
        const height = container.clientHeight;

        const scale = 1;
        const translateX = width / 2 - node.x * scale;
        const translateY = height / 2 - node.y * scale;

        svg.transition()
            .duration(CONFIG.transitionDuration)
            .call(zoom.transform, d3.zoomIdentity.translate(translateX, translateY).scale(scale));
    }

    function resetView() {
        // Clear highlights
        g.selectAll('.node').classed('dimmed', false).classed('selected', false).classed('highlighted', false);
        g.selectAll('.edge').classed('dimmed', false).classed('highlighted', false);
        g.selectAll('.edge path').attr('marker-end', 'url(#arrowhead)');

        selectedNode = null;
        closeInfoPanel();
        fitToView();
    }

    // ============================================
    // Info Panel
    // ============================================
    function showInfoPanel(node) {
        const panel = document.getElementById('info-panel');
        const title = document.getElementById('info-title');
        const content = document.getElementById('info-content');

        title.textContent = node.label;

        // Build content
        let html = '';

        if (node.type) {
            html += `
                <div class="info-section">
                    <div class="info-label">Type</div>
                    <div class="info-value">${node.type}</div>
                </div>
            `;
        }

        if (node.dag) {
            html += `
                <div class="info-section">
                    <div class="info-label">DAG</div>
                    <div class="info-value">${node.dag}</div>
                </div>
            `;
        }

        if (node.operator) {
            html += `
                <div class="info-section">
                    <div class="info-label">Operator</div>
                    <div class="info-value">${node.operator}</div>
                </div>
            `;
        }

        if (node.source_file) {
            html += `
                <div class="info-section">
                    <div class="info-label">Source File</div>
                    <div class="info-value">${node.source_file}</div>
                </div>
            `;
        }

        if (node.params) {
            html += `
                <div class="info-section">
                    <div class="info-label">Parameters</div>
                    <div class="info-value"><pre>${JSON.stringify(node.params, null, 2)}</pre></div>
                </div>
            `;
        }

        // Show upstream/downstream counts
        const upstream = getUpstream(node.id);
        const downstream = getDownstream(node.id);

        html += `
            <div class="info-section">
                <div class="info-label">Lineage</div>
                <div class="info-value">
                    ${upstream.length} upstream, ${downstream.length} downstream
                </div>
            </div>
        `;

        if (upstream.length > 0) {
            html += `
                <div class="info-section">
                    <div class="info-label">Direct Parents</div>
                    <ul class="info-list">
                        ${graphData.edges
                            .filter(e => e.target === node.id)
                            .map(e => `<li>${graphData.nodes.find(n => n.id === e.source)?.label || e.source}</li>`)
                            .join('')}
                    </ul>
                </div>
            `;
        }

        if (downstream.length > 0) {
            html += `
                <div class="info-section">
                    <div class="info-label">Direct Children</div>
                    <ul class="info-list">
                        ${graphData.edges
                            .filter(e => e.source === node.id)
                            .map(e => `<li>${graphData.nodes.find(n => n.id === e.target)?.label || e.target}</li>`)
                            .join('')}
                    </ul>
                </div>
            `;
        }

        content.innerHTML = html;
        panel.classList.remove('hidden');
    }

    function closeInfoPanel() {
        document.getElementById('info-panel').classList.add('hidden');
    }

    // ============================================
    // Utilities
    // ============================================
    function truncateLabel(label, maxLength) {
        if (label.length <= maxLength) return label;
        return label.substring(0, maxLength - 3) + '...';
    }

    // ============================================
    // Initialize on DOM ready
    // ============================================
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
