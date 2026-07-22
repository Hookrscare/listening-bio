import { DEMO_SITES } from "../../data/demoData";

// Signal constellation for the Detect chapter — candidate nodes separating from
// ambience. Purely decorative SVG.
export function SignalConstellation() {
  const nodes = [
    { cx: 30, cy: 40, r: 4, strong: true },
    { cx: 62, cy: 28, r: 2.5, strong: false },
    { cx: 78, cy: 58, r: 3.5, strong: true },
    { cx: 45, cy: 66, r: 2, strong: false },
    { cx: 20, cy: 72, r: 2.5, strong: false },
    { cx: 88, cy: 36, r: 2, strong: false },
  ];
  return (
    <svg
      className="constellation"
      viewBox="0 0 100 100"
      preserveAspectRatio="xMidYMid slice"
      aria-hidden="true"
    >
      {nodes.map((n, i) =>
        nodes
          .slice(i + 1)
          .map((m, j) => (
            <line
              key={`${i}-${j}`}
              x1={n.cx}
              y1={n.cy}
              x2={m.cx}
              y2={m.cy}
              stroke="rgba(114,242,199,0.18)"
              strokeWidth="0.3"
            />
          )),
      )}
      {nodes.map((n, i) => (
        <circle
          key={i}
          cx={n.cx}
          cy={n.cy}
          r={n.r}
          fill={n.strong ? "rgba(183,255,101,0.85)" : "rgba(208,255,239,0.4)"}
        />
      ))}
    </svg>
  );
}

// Review matrix for the Review chapter — confirmed / rejected / uncertain /
// unreviewed all remain visible (spec §5, §6).
export function ReviewMatrix() {
  const cells = [
    { state: "Confirmed", count: 2, cls: "confirmed" },
    { state: "Uncertain", count: 1, cls: "uncertain" },
    { state: "Rejected", count: 1, cls: "rejected" },
    { state: "Unreviewed", count: 1, cls: "unreviewed" },
  ];
  return (
    <div className="review-matrix" aria-hidden="true">
      {cells.map((c) => (
        <div key={c.state} className={`review-cell ${c.cls}`}>
          <span className="state">{c.state}</span>
          <strong>{c.count}</strong>
        </div>
      ))}
    </div>
  );
}

// Site network for the Act chapter — representative simulation sites.
export function SiteNetwork() {
  const lons = DEMO_SITES.map((s) => s.longitude);
  const lats = DEMO_SITES.map((s) => s.latitude);
  const minLon = Math.min(...lons);
  const maxLon = Math.max(...lons);
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);
  const nx = (lon: number) =>
    10 + ((lon - minLon) / (maxLon - minLon || 1)) * 80;
  const ny = (lat: number) =>
    90 - ((lat - minLat) / (maxLat - minLat || 1)) * 80;

  return (
    <svg
      className="site-network"
      viewBox="0 0 100 100"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="Representative simulation monitoring sites arranged as a network"
    >
      {DEMO_SITES.map((s, i) =>
        DEMO_SITES.slice(i + 1).map((t, j) => (
          <line
            key={`${i}-${j}`}
            x1={nx(s.longitude)}
            y1={ny(s.latitude)}
            x2={nx(t.longitude)}
            y2={ny(t.latitude)}
            stroke="rgba(114,242,199,0.2)"
            strokeWidth="0.4"
          />
        )),
      )}
      {DEMO_SITES.map((s) => (
        <g key={s.siteId}>
          <circle
            cx={nx(s.longitude)}
            cy={ny(s.latitude)}
            r="3"
            fill="rgba(183,255,101,0.85)"
          />
        </g>
      ))}
    </svg>
  );
}
