import { getVideoUrl } from "../api";

export default function VideoPlayer({ jobId }) {
  return (
    <div className="overflow-hidden rounded-xl bg-gray-900">
      <video
        controls
        className="w-full"
        src={getVideoUrl(jobId)}
      >
        Your browser does not support the video tag.
      </video>
    </div>
  );
}
