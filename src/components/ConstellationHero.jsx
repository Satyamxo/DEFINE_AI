

function ConstellationHero({ analyzing }) {
  const nodes = [
    { x: 300, y: 40, c: "#8b5cf6", d: "0s" },
    { x: 150, y: 140, c: "#3b82f6", d: "0.4s" },
    { x: 450, y: 140, c: "#3b82f6", d: "0.8s" },
    { x: 80, y: 250, c: "#10b981", d: "1.2s" },
    { x: 220, y: 250, c: "#10b981", d: "1.6s" },
    { x: 380, y: 250, c: "#10b981", d: "2s" },
    { x: 520, y: 250, c: "#f59e0b", d: "2.4s" },
  ];

  const lines = [
    [0, 1], [0, 2], [1, 3], [1, 4], [2, 5], [2, 6],
  ];

  return (
    <svg
      viewBox="0 0 600 300"
      className="mx-auto w-full max-w-[520px]"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="da-line-grad" x1="0" x2="1">
          <stop offset="0%" stopColor="#8b5cf6" />
          <stop offset="100%" stopColor="#22d3ee" />
        </linearGradient>
      </defs>

      {lines.map(([a, b], i) => (
        <line
          key={i}
          x1={nodes[a].x}
          y1={nodes[a].y}
          x2={nodes[b].x}
          y2={nodes[b].y}
          stroke="url(#da-line-grad)"
          strokeOpacity={analyzing ? 0.9 : 0.4}
          strokeWidth="1.5"
          className="da-hero-line"
        />
      ))}

      {nodes.map((n, i) => (
        <g key={i}>
          <circle cx={n.x} cy={n.y} r="16" fill={n.c} opacity="0.12" />
          <circle
            cx={n.x}
            cy={n.y}
            r="5"
            fill={n.c}
            className="da-hero-node"
            style={{ animationDelay: n.d }}
          />
        </g>
      ))}
    </svg>
  );
}

export default ConstellationHero;