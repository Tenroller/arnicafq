import { useState } from "react";
import UploadForm from "./components/UploadForm";
import JobProgress from "./components/JobProgress";
import ResultsDashboard from "./components/ResultsDashboard";

export default function App() {
  const [stage, setStage] = useState("idle"); // idle | processing | done
  const [jobId, setJobId] = useState(null);
  const [analytics, setAnalytics] = useState(null);

  function handleUploadComplete(id) {
    setJobId(id);
    setStage("processing");
  }

  function handleProcessingDone(data) {
    setAnalytics(data);
    setStage("done");
  }

  function handleReset() {
    setStage("idle");
    setJobId(null);
    setAnalytics(null);
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <header className="border-b border-gray-800 px-6 py-4">
        <h1 className="text-2xl font-bold tracking-tight">Soccer Analytics</h1>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-10">
        {stage === "idle" && <UploadForm onUploadComplete={handleUploadComplete} />}
        {stage === "processing" && (
          <JobProgress jobId={jobId} onDone={handleProcessingDone} />
        )}
        {stage === "done" && (
          <ResultsDashboard
            jobId={jobId}
            analytics={analytics}
            onReset={handleReset}
          />
        )}
      </main>
    </div>
  );
}
