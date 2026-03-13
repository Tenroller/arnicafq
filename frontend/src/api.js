const BASE = "";

export async function uploadVideo(file) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/api/upload`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`Upload failed: ${res.statusText}`);
  return res.json();
}

export async function getJobStatus(jobId) {
  const res = await fetch(`${BASE}/api/jobs/${jobId}/status`);
  if (!res.ok) throw new Error(`Status fetch failed: ${res.statusText}`);
  return res.json();
}

export async function getAnalytics(jobId) {
  const res = await fetch(`${BASE}/api/jobs/${jobId}/analytics`);
  if (!res.ok) throw new Error(`Analytics fetch failed: ${res.statusText}`);
  return res.json();
}

export function getVideoUrl(jobId) {
  return `${BASE}/api/jobs/${jobId}/video`;
}
