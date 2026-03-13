import { useCallback, useState } from "react";
import { uploadVideo } from "../api";

export default function UploadForm({ onUploadComplete }) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

  const handleFile = useCallback(
    async (file) => {
      if (!file) return;
      setError(null);
      setUploading(true);
      try {
        const data = await uploadVideo(file);
        onUploadComplete(data.job_id);
      } catch (err) {
        setError(err.message);
      } finally {
        setUploading(false);
      }
    },
    [onUploadComplete],
  );

  function onDrop(e) {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    handleFile(file);
  }

  function onDragOver(e) {
    e.preventDefault();
    setDragging(true);
  }

  function onDragLeave() {
    setDragging(false);
  }

  function onFileChange(e) {
    handleFile(e.target.files[0]);
  }

  return (
    <div className="flex flex-col items-center gap-6">
      <h2 className="text-xl font-semibold">Upload a Soccer Video</h2>

      <div
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        className={`flex w-full max-w-lg cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-8 py-16 transition ${
          dragging
            ? "border-blue-400 bg-blue-400/10"
            : "border-gray-700 bg-gray-900 hover:border-gray-500"
        }`}
      >
        {uploading ? (
          <p className="text-gray-400">Uploading...</p>
        ) : (
          <>
            <p className="mb-2 text-gray-400">
              Drag & drop a video file here, or
            </p>
            <label className="cursor-pointer rounded-lg bg-blue-600 px-5 py-2 font-medium text-white transition hover:bg-blue-500">
              Browse Files
              <input
                type="file"
                accept="video/*"
                className="hidden"
                onChange={onFileChange}
              />
            </label>
          </>
        )}
      </div>

      {error && (
        <p className="text-sm text-red-400">{error}</p>
      )}
    </div>
  );
}
