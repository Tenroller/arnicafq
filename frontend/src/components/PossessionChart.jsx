export default function PossessionChart({ possession }) {
  const team0 = possession?.team_0 ?? 0;
  const team1 = possession?.team_1 ?? 0;

  return (
    <div className="flex flex-col justify-center gap-4 rounded-xl bg-gray-900 p-6">
      <h3 className="text-lg font-semibold">Ball Possession</h3>

      <div className="flex h-10 w-full overflow-hidden rounded-full">
        <div
          className="flex items-center justify-center bg-red-500 text-sm font-bold text-white transition-all duration-500"
          style={{ width: `${team0}%` }}
        >
          {team0 > 8 && `${team0}%`}
        </div>
        <div
          className="flex items-center justify-center bg-blue-500 text-sm font-bold text-white transition-all duration-500"
          style={{ width: `${team1}%` }}
        >
          {team1 > 8 && `${team1}%`}
        </div>
      </div>

      <div className="flex justify-between text-sm">
        <span className="flex items-center gap-2">
          <span className="inline-block h-3 w-3 rounded-full bg-red-500" />
          Team A — {team0}%
        </span>
        <span className="flex items-center gap-2">
          Team B — {team1}%
          <span className="inline-block h-3 w-3 rounded-full bg-blue-500" />
        </span>
      </div>
    </div>
  );
}
