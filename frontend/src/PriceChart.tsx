import { money } from "./api";
import type { History } from "./types";
export function PriceChart({ rows }: { rows: History[] }) {
  if (!rows.length)
    return (
      <p className="muted">Este producto todavía no ha cambiado de precio.</p>
    );
  const values = [
      rows[0].previous_price_cents,
      ...rows.map((r) => r.price_cents),
    ],
    min = Math.min(...values),
    max = Math.max(...values),
    range = Math.max(max - min, 100);
  const points = values
    .map(
      (v, i) =>
        `${20 + (i * 440) / Math.max(1, values.length - 1)},${115 - ((v - min) * 85) / range}`,
    )
    .join(" ");
  return (
    <div className="chart">
      <svg
        viewBox="0 0 480 145"
        role="img"
        aria-label={`Evolución del precio: de ${money(values[0])} a ${money(values.at(-1)!)}`}
      >
        <path
          d="M20 25H460M20 70H460M20 115H460"
          stroke="#dfded8"
          strokeDasharray="3 5"
        />
        <polyline
          points={points}
          fill="none"
          stroke="#d85634"
          strokeWidth="3"
          strokeLinejoin="round"
        />
        {values.map((v, i) => (
          <circle
            key={i}
            cx={20 + (i * 440) / Math.max(1, values.length - 1)}
            cy={115 - ((v - min) * 85) / range}
            r="4"
            fill="#d85634"
          />
        ))}
      </svg>
      <div className="chart-label">
        <span>{money(values[0])} · inicio</span>
        <span>{money(values.at(-1)!)} · actual</span>
      </div>
      <details>
        <summary>Ver cambios de precio</summary>
        <ul>
          {rows.map((r) => (
            <li key={r.id}>
              {new Date(r.changed_at + "Z").toLocaleDateString("es-ES")}:{" "}
              {money(r.previous_price_cents)} → {money(r.price_cents)}
            </li>
          ))}
        </ul>
      </details>
    </div>
  );
}
