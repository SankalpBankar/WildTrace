import React, { useEffect, useState } from "react";
import "./App.css";

const API_URL = (
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");

// Reusable statistics card
function StatCard({ title, value, description, icon }) {
  return (
    <div className="stat-card">
      <div className="stat-card-icon">{icon}</div>
      <div className="stat-card-content">
        <p>{title}</p>
        <h2>WildTrace</h2>
        <span>{description}</span>
      </div>
    </div>
  );
}

// Safely format API values for display
function formatValue(value) {
  if (value === null || value === undefined) {
    return "N/A";
  }

  if (typeof value === "object") {
    return JSON.stringify(value, null, 2);
  }

  return String(value);
}

function App() {
  const [mode, setMode] = useState("image");
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [apiStatus, setApiStatus] = useState("checking");

  // Check whether the backend is running.
  useEffect(() => {
    let active = true;

    async function checkAPI() {
      try {
        const response = await fetch(`${API_URL}/health`);

        if (!response.ok) {
          throw new Error("Backend health check failed");
        }

        if (active) {
          setApiStatus("online");
        }
      } catch {
        if (active) {
          setApiStatus("offline");
        }
      }
    }

    checkAPI();

    return () => {
      active = false;
    };
  }, []);

  // Release temporary preview URLs when they change.
  useEffect(() => {
    return () => {
      if (preview?.startsWith("blob:")) {
        URL.revokeObjectURL(preview);
      }
    };
  }, [preview]);

  // Switch between image and video modes.
  function chooseMode(nextMode) {
    setMode(nextMode);
    setFile(null);
    setPreview(null);
    setResult(null);
    setError("");
  }

  // Validate and select the uploaded file.
  function handleFileChange(event) {
    const selectedFile = event.target.files?.[0];

    setResult(null);
    setError("");

    if (!selectedFile) {
      setFile(null);
      setPreview(null);
      return;
    }

    const isImage = selectedFile.type.startsWith("image/");
    const isVideo = selectedFile.type.startsWith("video/");

    if (mode === "image" && !isImage) {
      setFile(null);
      setPreview(null);
      setError("Please select a valid image file.");
      event.target.value = "";
      return;
    }

    if (mode === "video" && !isVideo) {
      setFile(null);
      setPreview(null);
      setError("Please select a valid video file.");
      event.target.value = "";
      return;
    }

    const maxSize = mode === "image" ? 15 * 1024 * 1024 : 200 * 1024 * 1024;

    if (selectedFile.size > maxSize) {
      setFile(null);
      setPreview(null);
      setError(
        `File is too large. Maximum allowed size is ${
          mode === "image" ? "15 MB" : "200 MB"
        }.`,
      );
      event.target.value = "";
      return;
    }

    setFile(selectedFile);
    setPreview(URL.createObjectURL(selectedFile));
  }

  // Upload the selected image or video to FastAPI.
  async function handleSubmit(event) {
    event.preventDefault();

    if (!file) {
      setError("Please select a file before starting analysis.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const endpoint = mode === "image" ? "/upload" : "/upload-video";

      const response = await fetch(`${API_URL}${endpoint}`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          data.detail || `Request failed with status ${response.status}`,
        );
      }

      setResult(data);
    } catch (err) {
      setError(
        err.message ||
          "Unable to process the file. Check whether the backend is running.",
      );
    } finally {
      setLoading(false);
    }
  }

  // Normalize detection and tracking results.
  const detections = Array.isArray(result?.detections) ? result.detections : [];

  const reidentificationResults = Array.isArray(
    result?.reidentification_results,
  )
    ? result.reidentification_results
    : [];

  const videoResults = result?.results || {};

  const tracks = videoResults?.tracks || {};

  const trackEntries = Array.isArray(tracks)
    ? tracks.map((track, index) => [
        track?.track_id ?? track?.id ?? index + 1,
        track,
      ])
    : Object.entries(tracks);

  const detectionCount = result?.detection_count ?? detections.length;

  const trackingCount =
    videoResults?.track_count ??
    videoResults?.total_tracks ??
    trackEntries.length;

  const formatBytes = (bytes) => {
    if (!bytes) return "0 Bytes";

    const units = ["Bytes", "KB", "MB", "GB"];
    const index = Math.min(
      Math.floor(Math.log(bytes) / Math.log(1024)),
      units.length - 1,
    );

    return `${(bytes / Math.pow(1024, index)).toFixed(
      index === 0 ? 0 : 2,
    )} ${units[index]}`;
  };

  return (
    <div className="app-shell">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">W</div>
          <div>
            <h2>WildTrace</h2>
            <span>Wildlife Intelligence</span>
          </div>
        </div>

        <div className="sidebar-section">
          <p className="sidebar-label">WORKSPACE</p>

          <button
            type="button"
            className={`nav-item ${mode === "image" ? "active" : ""}`}
            onClick={() => chooseMode("image")}
          >
            <span>▧</span>
            Image Analysis
          </button>

          <button
            type="button"
            className={`nav-item ${mode === "video" ? "active" : ""}`}
            onClick={() => chooseMode("video")}
          >
            <span>▷</span>
            Video Tracking
          </button>
        </div>

        <div className="sidebar-bottom">
          <div className="connection-card">
            <span
              className={`status-dot ${
                apiStatus === "online" ? "online" : "offline"
              }`}
            />
            <div>
              <strong>Backend API</strong>
              <p>
                {apiStatus === "checking"
                  ? "Checking connection..."
                  : apiStatus === "online"
                    ? "Connected"
                    : "Disconnected"}
              </p>
            </div>
          </div>

          <p className="sidebar-footer">WildTrace Prototype · v0.5.0</p>
        </div>
      </aside>

      {/* Main dashboard */}
      <main className="main-content">
        <header className="topbar">
          <div>
            <p className="breadcrumb">Workspace / Dashboard</p>
            <h1>Wildlife Intelligence Dashboard</h1>
          </div>

          <div className="api-indicator">
            <span
              className={`status-dot ${
                apiStatus === "online" ? "online" : "offline"
              }`}
            />
            {apiStatus === "online"
              ? "API Online"
              : apiStatus === "checking"
                ? "Connecting..."
                : "API Offline"}
          </div>
        </header>

        {/* Welcome section */}
        <section className="welcome-section">
          <div>
            <p className="eyebrow">WILDLIFE MONITORING PLATFORM</p>
            <h2>Track wildlife. Identify individuals.</h2>
            <p>
              Analyze animal images, inspect detections, and explore video-based
              tracking results with WildTrace.
            </p>
          </div>

          <div className="welcome-icon" aria-hidden="true">
            🐅
          </div>
        </section>

        {/* Statistics */}
        <section className="stats-grid">
          <StatCard
            title="API Status"
            value={
              apiStatus === "online"
                ? "Online"
                : apiStatus === "checking"
                  ? "Checking"
                  : "Offline"
            }
            description="Backend connectivity"
            icon="⌁"
          />

          <StatCard
            title="Detections"
            value={result?.input_type === "image" ? detectionCount : "—"}
            description="Objects detected in image"
            icon="◎"
          />

          <StatCard
            title="Identifications"
            value={
              result?.input_type === "image"
                ? reidentificationResults.filter(
                    (item) =>
                      item?.reidentification?.status === "MATCH" ||
                      item?.reidentification?.status === "IDENTIFIED",
                  ).length
                : "—"
            }
            description="Potential gallery matches"
            icon="⌕"
          />

          <StatCard
            title="Video Tracks"
            value={result?.input_type === "video" ? trackingCount : "—"}
            description="Tracks returned by the API"
            icon="▷"
          />
        </section>

        {/* Upload and preview */}
        <section className="workspace-grid">
          <div className="panel upload-panel">
            <div className="panel-heading">
              <div>
                <h2>Analyze Wildlife</h2>
                <p>Choose an input type and upload your file.</p>
              </div>
            </div>

            <div className="mode-switch">
              <button
                type="button"
                className={mode === "image" ? "selected" : ""}
                onClick={() => chooseMode("image")}
              >
                ▧ Image
              </button>

              <button
                type="button"
                className={mode === "video" ? "selected" : ""}
                onClick={() => chooseMode("video")}
              >
                ▷ Video
              </button>
            </div>

            <form onSubmit={handleSubmit}>
              <label className="upload-dropzone">
                <input
                  type="file"
                  accept={
                    mode === "image"
                      ? "image/jpeg,image/png,image/webp"
                      : "video/mp4,video/avi,video/quicktime,video/x-matroska,video/webm"
                  }
                  onChange={handleFileChange}
                  hidden
                />

                <span className="upload-icon">
                  {mode === "image" ? "▧" : "▷"}
                </span>

                <strong>{file ? file.name : "Choose a file to analyze"}</strong>

                <span>
                  {file
                    ? formatBytes(file.size)
                    : mode === "image"
                      ? "JPG, PNG, WEBP · Maximum 15 MB"
                      : "MP4, AVI, MOV, MKV, WEBM · Maximum 200 MB"}
                </span>

                <span className="browse-label">Browse files</span>
              </label>

              {file && (
                <div className="selected-file">
                  <span>Selected file</span>
                  <strong>{file.name}</strong>
                  <button
                    type="button"
                    onClick={() => {
                      setFile(null);
                      setPreview(null);
                      setResult(null);
                      setError("");
                    }}
                  >
                    Remove
                  </button>
                </div>
              )}

              {error && (
                <div className="error-message" role="alert">
                  <strong>Something went wrong</strong>
                  <p>{error}</p>
                </div>
              )}

              <button
                type="submit"
                className="analyze-button"
                disabled={!file || loading}
              >
                {loading
                  ? "Processing..."
                  : mode === "image"
                    ? "Analyze Image →"
                    : "Track Video →"}
              </button>

              {apiStatus === "offline" && (
                <p className="helper-text">
                  The backend is unreachable. Start the FastAPI server before
                  analyzing files.
                </p>
              )}
            </form>
          </div>

          <div className="panel preview-panel">
            <div className="panel-heading">
              <div>
                <h2>Input Preview</h2>
                <p>
                  {preview
                    ? "Preview of your selected file"
                    : "Your selected media will appear here"}
                </p>
              </div>
            </div>

            <div className="preview-area">
              {preview && mode === "image" && (
                <img
                  src={preview}
                  alt="Selected wildlife"
                  className="media-preview"
                />
              )}

              {preview && mode === "video" && (
                <video src={preview} controls className="media-preview">
                  Your browser does not support video playback.
                </video>
              )}

              {!preview && (
                <div className="empty-preview">
                  <span>{mode === "image" ? "▧" : "▷"}</span>
                  <strong>No media selected</strong>
                  <p>Upload an image or video to get started.</p>
                </div>
              )}
            </div>

            {result && (
              <div className="result-summary">
                <span className="success-indicator">✓</span>
                <div>
                  <strong>Processing completed</strong>
                  <p>{result.message || "Analysis finished."}</p>
                </div>
              </div>
            )}
          </div>
        </section>

        {/* Image detection results */}
        {result?.input_type === "image" && (
          <section className="panel results-panel">
            <div className="panel-heading">
              <div>
                <h2>Detection Results</h2>
                <p>{detectionCount} detection(s) returned by the model.</p>
              </div>
            </div>

            {detections.length === 0 ? (
              <div className="empty-results">
                <strong>No detections returned</strong>
                <p>
                  The model did not return any objects for this image. This does
                  not necessarily mean no animal is present.
                </p>
              </div>
            ) : (
              <div className="detection-list">
                {detections.map((detection, index) => {
                  const box = detection.bounding_box || {};
                  const confidence = Number(detection.confidence);

                  return (
                    <article
                      className="detection-card"
                      key={`${index}-${detection.class || "animal"}`}
                    >
                      <div className="detection-card-header">
                        <div>
                          <span className="detection-number">
                            Detection {index + 1}
                          </span>
                          <h3>{detection.class || "Unknown animal"}</h3>
                        </div>

                        <span className="confidence-badge">
                          {Number.isFinite(confidence)
                            ? `${(confidence * 100).toFixed(1)}%`
                            : "N/A"}
                        </span>
                      </div>

                      <p className="detail-label">Bounding box</p>

                      <div className="bbox-grid">
                        <span>X1: {formatValue(box.x1)}</span>
                        <span>Y1: {formatValue(box.y1)}</span>
                        <span>X2: {formatValue(box.x2)}</span>
                        <span>Y2: {formatValue(box.y2)}</span>
                      </div>

                      {box.crop_path && (
                        <p className="crop-note">
                          Animal crop saved for gallery comparison.
                        </p>
                      )}
                    </article>
                  );
                })}
              </div>
            )}
          </section>
        )}

        {/* Re-identification results */}
        {result?.input_type === "image" && (
          <section className="panel results-panel">
            <div className="panel-heading">
              <div>
                <h2>Individual Re-Identification</h2>
                <p>Comparison results from your existing animal gallery.</p>
              </div>
            </div>

            {reidentificationResults.length === 0 ? (
              <div className="empty-results">
                <p>
                  No re-identification results were returned for this image.
                </p>
              </div>
            ) : (
              <div className="detection-list">
                {reidentificationResults.map((item, index) => {
                  const identification = item.reidentification || {};
                  const matches = Array.isArray(identification.matches)
                    ? identification.matches
                    : [];

                  return (
                    <article className="detection-card" key={`reid-${index}`}>
                      <div className="detection-card-header">
                        <div>
                          <span className="detection-number">
                            Detection {index + 1}
                          </span>
                          <h3>
                            {identification.individual_id ||
                              identification.animal_id ||
                              "Identity not confirmed"}
                          </h3>
                        </div>

                        <span className="confidence-badge">
                          {identification.status || "UNKNOWN"}
                        </span>
                      </div>

                      {identification.message && (
                        <p>{identification.message}</p>
                      )}

                      {matches.length > 0 && (
                        <div className="match-list">
                          <strong>Gallery matches</strong>

                          {matches.map((match, matchIndex) => (
                            <div
                              className="match-item"
                              key={`match-${matchIndex}`}
                            >
                              <span>
                                {match.individual_id ||
                                  match.animal_id ||
                                  match.id ||
                                  `Match ${matchIndex + 1}`}
                              </span>

                              <span>
                                {match.similarity !== undefined
                                  ? `Similarity: ${match.similarity}`
                                  : match.score !== undefined
                                    ? `Score: ${match.score}`
                                    : ""}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </article>
                  );
                })}
              </div>
            )}
          </section>
        )}

        {/* Video tracking results */}
        {result?.input_type === "video" && (
          <section className="panel results-panel">
            <div className="panel-heading">
              <div>
                <h2>Video Tracking Results</h2>
                <p>
                  {trackEntries.length} track record(s) returned by the tracking
                  module.
                </p>
              </div>
            </div>

            {trackEntries.length === 0 ? (
              <div className="empty-results">
                <strong>No track records returned</strong>
                <p>
                  The video was processed, but no track entries were found in
                  the response.
                </p>
              </div>
            ) : (
              <div className="detection-list">
                {trackEntries.map(([trackId, track], index) => (
                  <article className="detection-card" key={`track-${trackId}`}>
                    <div className="detection-card-header">
                      <div>
                        <span className="detection-number">
                          Track {index + 1}
                        </span>
                        <h3>
                          Individual ID:{" "}
                          {track?.individual_id ||
                            track?.animal_id ||
                            track?.tiger_id ||
                            trackId}
                        </h3>
                      </div>

                      <span className="confidence-badge">
                        {track?.status || "TRACKED"}
                      </span>
                    </div>

                    <pre className="json-preview">
                      {JSON.stringify(track, null, 2)}
                    </pre>
                  </article>
                ))}
              </div>
            )}
          </section>
        )}

        {/* Raw API response for debugging */}
        {result && (
          <details className="panel raw-response">
            <summary>View complete API response</summary>
            <pre className="json-preview">
              {JSON.stringify(result, null, 2)}
            </pre>
          </details>
        )}

        <footer className="app-footer">
          <span>WildTrace · Wildlife Intelligence Prototype</span>
          <span>Detection · Tracking · Re-Identification</span>
        </footer>
      </main>
    </div>
  );
}

export default App;
