import { useEffect, useRef, useState } from "react";
import { getJobStatus, getAnalytics } from "../api";

export default function JobProgress({ jobId, onDone }) {
  const [status, setStatus] = useState(null);
  const intervalRef = useRef(null);

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      try {
        const data = await getJobStatus(jobId);
        if (cancelled) return;
        setStatus(data);

        if (data.status === "completed") {
          clearInterval(intervalRef.current);
          const analytics = await getAnalytics(jobId);
          if (!cancelled) onDone(analytics);
        } else if (data.status === "failed") {
          clearInterval(intervalRef.current);
        }
      } catch {
        // keep polling
      }
    }

    poll();
    intervalRef.current = setInterval(poll, 2000);

    return () => {
      cancelled = true;
      clearInterval(intervalRef.current);
    };
  }, [jobId, onDone]);

  const phase = status?.phase ?? "pending";
  const pct = status?.progress_pct ?? 0;
  const current = status?.current_frame ?? 0;
  const total = status?.total_frames ?? 0;

  return (
    <div className="flex flex-col items-center gap-6">
      <h2 className="text-xl font-semibold">Processing Video</h2>

      <div className="w-full max-w-lg">
        <div className="mb-2 flex justify-between text-sm text-gray-400">
          <span className="capitalize">{phase}</span>
          <span>
            {current}/{total} frames ({pct.toFixed(1)}%)
          </span>
        </div>

        <div className="h-4 w-full overflow-hidden rounded-full bg-gray-800">
          <div
            className="h-full rounded-full bg-blue-500 transition-all duration-300"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      {status?.status === "failed" && (
        <p className="text-sm text-red-400">
          Processing failed: {status.error}
        </p>
      )}
    </div>
  );
}
