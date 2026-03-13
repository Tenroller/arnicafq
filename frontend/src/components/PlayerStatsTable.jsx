import { useMemo, useState } from "react";

export default function PlayerStatsTable({ players }) {
  const [sortKey, setSortKey] = useState("tracker_id");
  const [sortAsc, setSortAsc] = useState(true);

  const sorted = useMemo(() => {
    const copy = [...(players ?? [])];
    copy.sort((a, b) => {
      const va = a[sortKey];
      const vb = b[sortKey];
      return sortAsc ? va - vb : vb - va;
    });
    return copy;
  }, [players, sortKey, sortAsc]);

  function handleSort(key) {
    if (key === sortKey) {
      setSortAsc((prev) => !prev);
    } else {
      setSortKey(key);
      setSortAsc(true);
    }
  }

  const columns = [
    { key: "tracker_id", label: "#ID" },
    { key: "team_id", label: "Team" },
    { key: "distance_px", label: "Distance (px)" },
    { key: "avg_speed_px_per_s", label: "Avg Speed" },
    { key: "max_speed_px_per_s", label: "Max Speed" },
    { key: "sprints", label: "Sprints" },
    { key: "time_on_ball_sec", label: "Ball Time (s)" },
  ];

  return (
    <div className="overflow-hidden rounded-xl bg-gray-900">
      <h3 className="px-6 pt-5 text-lg font-semibold">Player Stats</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-gray-800 text-gray-400">
              {columns.map((col) => (
                <th
                  key={col.key}
                  onClick={() => handleSort(col.key)}
                  className="cursor-pointer px-6 py-3 font-medium select-none hover:text-gray-200"
                >
                  {col.label}
                  {sortKey === col.key && (sortAsc ? " ▲" : " ▼")}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((p) => (
              <tr
                key={p.tracker_id}
                className="border-b border-gray-800/50 hover:bg-gray-800/40"
              >
                <td className="px-6 py-3 font-mono">{p.tracker_id}</td>
                <td className="px-6 py-3">
                  <span
                    className={`inline-block h-3 w-3 rounded-full ${
                      p.team_id === 0 ? "bg-red-500" : "bg-blue-500"
                    }`}
                  />{" "}
                  {p.team_id === 0 ? "A" : "B"}
                </td>
                <td className="px-6 py-3">{p.distance_px.toFixed(1)}</td>
                <td className="px-6 py-3">{p.avg_speed_px_per_s.toFixed(1)}</td>
                <td className="px-6 py-3">{p.max_speed_px_per_s.toFixed(1)}</td>
                <td className="px-6 py-3">{p.sprints}</td>
                <td className="px-6 py-3">{p.time_on_ball_sec.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
