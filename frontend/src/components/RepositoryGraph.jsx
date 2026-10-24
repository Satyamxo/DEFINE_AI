
import { useMemo, useState, useEffect } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Panel,
  MarkerType,
} from "@xyflow/react";

import dagre from "@dagrejs/dagre";

import "@xyflow/react/dist/style.css";

const NODE_WIDTH = 180;
const NODE_HEIGHT = 70;

function getNodeColor(type) {
  switch (type) {
    case "repository":
      return "#7c3aed";

    case "folder":
      return "#2563eb";

    case "file":
      return "#059669";

    case "class":
      return "#d97706";

    case "function":
      return "#dc2626";

    case "method":
      return "#db2777";

    default:
      return "#6b7280";
  }
}

// UI only: legend entries shown on the canvas.
const LEGEND = [
  ["Repository", "repository"],
  ["Folder", "folder"],
  ["File", "file"],
  ["Class", "class"],
  ["Function", "function"],
  ["Method", "method"],
];

/*
    ------------------------------------------------
    Get only the nodes that should currently be visible
    ------------------------------------------------

    The backend still sends the complete graph.

    This function controls which part of that graph
    should be displayed in React Flow.

    Only CONTAINS edges are used for expansion.

    IMPORTS edges are displayed only when both
    connected nodes are already visible.
*/

function getVisibleGraph(graph, expandedNodes) {
  const childrenMap = new Map();

  // ------------------------------------------------
  // Build parent -> children map
  // ------------------------------------------------

  graph.edges.forEach((edge) => {
    if (edge.type !== "CONTAINS") {
      return;
    }

    if (!childrenMap.has(edge.source)) {
      childrenMap.set(edge.source, []);
    }

    childrenMap.get(edge.source).push(edge.target);
  });

  // ------------------------------------------------
  // Keep track of visible nodes
  // ------------------------------------------------

  const visibleNodeIds = new Set();

  // ------------------------------------------------
  // Recursively add children of expanded nodes
  // ------------------------------------------------

  function addVisibleChildren(parentId) {
    const children = childrenMap.get(parentId) || [];

    for (const childId of children) {
      visibleNodeIds.add(childId);

      if (expandedNodes.has(childId)) {
        addVisibleChildren(childId);
      }
    }
  }

  // ------------------------------------------------
  // Find repository root
  // ------------------------------------------------

  const repositoryNode = graph.nodes.find((node) => node.type === "repository");

  // ------------------------------------------------
  // Repository is always visible
  // ------------------------------------------------

  if (repositoryNode) {
    visibleNodeIds.add(repositoryNode.id);

    // Show repository's children
    // only when repository is expanded

    if (expandedNodes.has(repositoryNode.id)) {
      addVisibleChildren(repositoryNode.id);
    }
  }

  // ------------------------------------------------
  // Return filtered graph
  // ------------------------------------------------

  return {
    nodes: graph.nodes.filter((node) => visibleNodeIds.has(node.id)),

    edges: graph.edges.filter(
      (edge) =>
        visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target),
    ),
  };
}

/*
    ------------------------------------------------
    Toggle expansion state
    ------------------------------------------------
*/

function toggleExpanded(nodeId, setExpandedNodes) {
  setExpandedNodes((previous) => {
    const next = new Set(previous);

    if (next.has(nodeId)) {
      next.delete(nodeId);
    } else {
      next.add(nodeId);
    }

    return next;
  });
}

function createLayout(graph, expandedNodes, toggleNode) {
  const dagreGraph = new dagre.graphlib.Graph();

  dagreGraph.setDefaultEdgeLabel(() => ({}));

  dagreGraph.setGraph({
    rankdir: "TB",
    nodesep: 60,
    ranksep: 100,
  });

  // ------------------------------------------------
  // Add nodes to Dagre
  // ------------------------------------------------

  graph.nodes.forEach((node) => {
    dagreGraph.setNode(node.id, {
      width: NODE_WIDTH,
      height: NODE_HEIGHT,
    });
  });

  // ------------------------------------------------
  // Add edges to Dagre
  // ------------------------------------------------

  graph.edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  // ------------------------------------------------
  // Calculate layout
  // ------------------------------------------------

  dagre.layout(dagreGraph);

  // ------------------------------------------------
  // Build children map
  // ------------------------------------------------

  const childrenMap = new Map();

  graph.edges.forEach((edge) => {
    if (edge.type !== "CONTAINS") {
      return;
    }

    if (!childrenMap.has(edge.source)) {
      childrenMap.set(edge.source, []);
    }

    childrenMap.get(edge.source).push(edge.target);
  });

  // ------------------------------------------------
  // Convert backend nodes → React Flow nodes
  // ------------------------------------------------

  const nodes = graph.nodes.map((node) => {
    const position = dagreGraph.node(node.id);

    const children = childrenMap.get(node.id) || [];

    const hasChildren = children.length > 0;

    const isExpanded = expandedNodes.has(node.id);

    const color = getNodeColor(node.type);

    return {
      id: node.id,

      position: {
        x: position.x - NODE_WIDTH / 2,
        y: position.y - NODE_HEIGHT / 2,
      },

      // UI only: explicit size so the MiniMap can always draw the node.
      width: NODE_WIDTH,
      height: NODE_HEIGHT,

      data: {
        ...node,

        analysis: node.analysis || {},

        label: (
          <div
            className="da-node"
            style={{
              position: "relative",

              background: `linear-gradient(145deg, ${color}, ${color}bb)`,

              color: "white",

              padding: "10px 14px",

              width: `${NODE_WIDTH}px`,

              minHeight: `${NODE_HEIGHT}px`,

              boxSizing: "border-box",
            }}
          >
            {/* =========================
                EXPAND / COLLAPSE BUTTON
            ========================= */}

            {hasChildren && (
              <button
                onClick={(event) => {
                  event.stopPropagation();

                  toggleNode(node.id);
                }}
                style={{
                  position: "absolute",

                  left: "-10px",

                  top: "50%",

                  transform: "translateY(-50%)",

                  width: "22px",

                  height: "22px",

                  borderRadius: "50%",

                  border: "2px solid white",

                  background: "#0b0d16",

                  color: "white",

                  display: "flex",

                  alignItems: "center",

                  justifyContent: "center",

                  fontSize: "16px",

                  fontWeight: "700",

                  lineHeight: "1",

                  cursor: "pointer",

                  zIndex: 10,

                  boxShadow: `0 0 12px ${color}`,
                }}
                title={isExpanded ? "Collapse" : "Expand"}
              >
                {isExpanded ? "−" : "+"}
              </button>
            )}

            {/* =========================
                NODE TYPE
            ========================= */}

            <div
              style={{
                fontSize: "11px",

                opacity: 0.8,

                textTransform: "capitalize",

                letterSpacing: "0.02em",
              }}
            >
              {node.type}
            </div>

            {/* =========================
                NODE NAME
            ========================= */}

            <div
              style={{
                fontWeight: 600,

                marginTop: "4px",

                overflow: "hidden",

                textOverflow: "ellipsis",

                whiteSpace: "nowrap",
              }}
            >
              {node.name}
            </div>
          </div>
        ),
      },
    };
  });

  // ------------------------------------------------
  // Convert backend edges → React Flow edges
  // ------------------------------------------------

  const edges = graph.edges.map((edge, index) => {
    const isImport = edge.type === "IMPORTS";

    return {
      id: `edge-${index}`,

      source: edge.source,

      target: edge.target,

      label: edge.type,

      animated: edge.type === "IMPORTS",

      // UI only: softer curves and colour-coded edge types.
      type: "smoothstep",

      style: {
        stroke: isImport ? "#22d3ee" : "rgba(148, 163, 184, 0.45)",
        strokeWidth: isImport ? 1.8 : 1.4,
      },

      labelStyle: {
        fill: isImport ? "#67e8f9" : "#8b90a5",
        fontSize: 10,
      },

      labelBgStyle: {
        fill: "#0b0d16",
        fillOpacity: 0.9,
      },

      labelBgPadding: [6, 3],

      labelBgBorderRadius: 6,

      markerEnd: isImport
        ? { type: MarkerType.ArrowClosed, color: "#22d3ee" }
        : undefined,
    };
  });

  return {
    nodes,
    edges,
  };
}

function RepositoryGraph({ graph, onNodeSelect }) {
  /*
        ------------------------------------------------
        Expanded nodes state
        ------------------------------------------------

        A Set is used because we only need to know
        whether a node is expanded or collapsed.

        Example:

        {
            "repo:AI_Video_Ajent",
            "folder:core"
        }
    */

  const [expandedNodes, setExpandedNodes] = useState(new Set());

  /*
        ------------------------------------------------
        Automatically expand repository when graph loads
        ------------------------------------------------
    */

  useEffect(() => {
    if (!graph) {
      return;
    }

    setExpandedNodes(new Set([`repo:${graph.repository}`]));
  }, [graph]);

  /*
        ------------------------------------------------
        Calculate currently visible graph
        ------------------------------------------------
    */

  const visibleGraph = useMemo(
    () =>
      graph
        ? getVisibleGraph(graph, expandedNodes)
        : {
            nodes: [],
            edges: [],
          },

    [graph, expandedNodes],
  );

  /*
        ------------------------------------------------
        Layout only the visible graph
        ------------------------------------------------
    */
  const { nodes, edges } = useMemo(
    () =>
      createLayout(visibleGraph, expandedNodes, (nodeId) => {
        toggleExpanded(nodeId, setExpandedNodes);
      }),

    [visibleGraph, expandedNodes],
  );

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
      }}
    >
      <ReactFlow
        className="da-flow"
        colorMode="dark"
        nodes={nodes}
        edges={edges}
        fitView
        minZoom={0.1}
        maxZoom={2}
        onNodeClick={(event, node) => {
          /*
                        IMPORTANT:

                        Normal node click still only
                        selects the node.

                        We are NOT expanding/collapsing
                        from node click yet.

                        Later we will add an explicit
                        + / - control to each node.
                    */

          onNodeSelect(node);
        }}
        onNodeDoubleClick={(event, node) => {
          toggleExpanded(node.id, setExpandedNodes);
        }}
      >
        <Background gap={28} size={1} color="rgba(255,255,255,0.08)" />

        <Controls />

        <MiniMap
          position="bottom-right"
          pannable
          zoomable
          style={{ width: 200, height: 140 }}
          bgColor="#0b0d16"
          maskColor="rgba(139, 92, 246, 0.14)"
          maskStrokeColor="#8b5cf6"
          maskStrokeWidth={1.5}
          nodeColor={(node) => getNodeColor(node.data?.type)}
          nodeStrokeColor="rgba(255,255,255,0.35)"
          nodeStrokeWidth={2}
          nodeBorderRadius={4}
        />

        {/* UI only: colour legend */}
        <Panel position="top-left">
          <div className="da-glass da-pop rounded-xl px-3.5 py-3">
            <p className="mb-2 text-xs font-semibold text-gray-300">
              Legend
            </p>

            <ul className="grid grid-cols-2 gap-x-4 gap-y-1.5">
              {LEGEND.map(([label, type]) => (
                <li
                  key={type}
                  className="flex items-center gap-2 text-xs text-gray-400"
                >
                  <span
                    className="h-2.5 w-2.5 rounded-sm"
                    style={{ background: getNodeColor(type) }}
                  />
                  {label}
                </li>
              ))}
            </ul>

            <p className="mt-2.5 border-t border-white/10 pt-2 text-[11px] text-gray-500">
              Use + / − or double-click a node to expand it.
            </p>
          </div>
        </Panel>
      </ReactFlow>
    </div>
  );
}

export default RepositoryGraph;