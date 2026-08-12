import { labelCounts } from "@/data/research";

export function DatasetDistribution() {
  const total = labelCounts.reduce((sum, item) => sum + item.value, 0);
  const stops = labelCounts.map((item, index) => {
    const prior = labelCounts.slice(0, index).reduce((sum, entry) => sum + entry.value, 0);
    const start = (prior / total) * 360;
    const end = ((prior + item.value) / total) * 360;
    return `${item.color} ${start}deg ${end}deg`;
  });

  return (
    <div className="distribution-card">
      <div className="distribution-ring" style={{ background: `conic-gradient(${stops.join(",")})` }}>
        <div>
          <strong>1,336</strong>
          <span>FDA-approved drugs</span>
        </div>
      </div>
      <div className="distribution-legend">
        {labelCounts.map((item) => (
          <div key={item.label}>
            <i style={{ background: item.color }} />
            <span>{item.label}</span>
            <strong>{item.value}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}
