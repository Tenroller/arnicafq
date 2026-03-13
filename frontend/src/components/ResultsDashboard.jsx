import VideoPlayer from "./VideoPlayer";
import PossessionChart from "./PossessionChart";
import PlayerStatsTable from "./PlayerStatsTable";
import EventsTimeline from "./EventsTimeline";

export default function ResultsDashboard({ jobId, analytics, onReset }) {
  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Analysis Results</h2>
        <button
          onClick={onReset}
          className="rounded-lg bg-gray-800 px-4 py-2 text-sm font-medium transition hover:bg-gray-700"
        >
          Analyze Another
        </button>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <VideoPlayer jobId={jobId} />
        <PossessionChart possession={analytics.possession} />
      </div>

      <PlayerStatsTable players={analytics.player_stats} />
      <EventsTimeline events={analytics.events} />
    </div>
  );
}
