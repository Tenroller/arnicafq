const TYPE_STYLES = {
  pass: "bg-green-500/20 text-green-400 border-green-500/40",
  shot: "bg-orange-500/20 text-orange-400 border-orange-500/40",
  goal: "bg-red-500/20 text-red-400 border-red-500/40",
};

function formatTime(seconds) {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

export default function EventsTimeline({ events }) {
  if (!events || events.length === 0) {
    return (
      <div className="rounded-xl bg-gray-900 p-6">
        <h3 className="text-lg font-semibold">Events</h3>
        <p className="mt-3 text-sm text-gray-500">No events detected.</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl bg-gray-900 p-6">
      <h3 className="mb-4 text-lg font-semibold">Events</h3>
      <div className="flex max-h-80 flex-col gap-3 overflow-y-auto pr-2">
        {events.map((evt, idx) => {
          const style =
            TYPE_STYLES[evt.event_type] ??
            "bg-gray-700/30 text-gray-400 border-gray-600/40";
          return (
            <div
              key={idx}
              className="flex items-center gap-4 rounded-lg border border-gray-800 bg-gray-800/30 px-4 py-3"
            >
              <span className="font-mono text-sm text-gray-500">
                {formatTime(evt.timestamp)}
              </span>
              <span
                className={`rounded-full border px-3 py-0.5 text-xs font-semibold uppercase ${style}`}
              >
                {evt.event_type}
              </span>
              <span className="text-sm text-gray-300">
                Team {evt.team_id === 0 ? "A" : "B"} — Player #{evt.player_id}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
