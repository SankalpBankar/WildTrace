from pathlib import Path

import cv2
from ultralytics import YOLO


# --------------------------------------------------
# Configuration
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "tiger_detector.pt"

CONFIDENCE_THRESHOLD = 0.20
MAX_PROCESSED_FRAMES = 150


# --------------------------------------------------
# Track Tigers in a Video
# --------------------------------------------------

def track_tiger_movement(video_path):
    """
    Detect and track tigers across sampled video frames.

    Requires a YOLO model trained to detect tigers.

    Tracking IDs are temporary within the video.
    They do not establish identity across separate videos.
    """

    video_path = Path(video_path)

    if not video_path.exists():
        raise FileNotFoundError(
            f"Video not found: {video_path}"
        )

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Tiger model not found: {MODEL_PATH}"
        )

    model = YOLO(str(MODEL_PATH))

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise ValueError("Could not open video.")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if fps <= 0:
        cap.release()
        raise ValueError("Could not determine video FPS.")

    # Sample the video to keep the demo manageable.
    step = max(1, total_frames // MAX_PROCESSED_FRAMES)

    processed_frames = 0
    detection_count = 0
    tracks = {}

    frame_number = 0

    try:
        while True:
            success, frame = cap.read()

            if not success:
                break

            if frame_number % step == 0:
                result = model.track(
                    source=frame,
                    persist=True,
                    tracker="bytetrack.yaml",
                    conf=CONFIDENCE_THRESHOLD,
                    verbose=False
                )[0]

                processed_frames += 1

                if result.boxes is not None and len(result.boxes) > 0:
                    boxes = result.boxes

                    for index, box in enumerate(boxes):
                        class_id = int(box.cls[0])
                        class_name = str(
                            result.names[class_id]
                        ).lower()

                        # Only retain detections classified as tiger.
                        if class_name != "tiger":
                            continue

                        # Tracking IDs are provided by the tracker.
                        if box.id is None:
                            continue

                        tracker_id = int(box.id[0])
                        confidence = float(box.conf[0])

                        x1, y1, x2, y2 = (
                            box.xyxy[0].tolist()
                        )

                        center_x = (x1 + x2) / 2
                        center_y = (y1 + y2) / 2

                        # Create a readable ID for this video.
                        tiger_id = f"T-{tracker_id:03d}"

                        if tiger_id not in tracks:
                            tracks[tiger_id] = []

                        tracks[tiger_id].append({
                            "frame": frame_number,
                            "time_seconds": round(
                                frame_number / fps, 2
                            ),
                            "center_x": round(center_x, 1),
                            "center_y": round(center_y, 1),
                            "width": round(x2 - x1, 1),
                            "height": round(y2 - y1, 1),
                            "confidence": round(confidence, 3)
                        })

                        detection_count += 1

            frame_number += 1

    finally:
        cap.release()

    if not tracks:
        return {
            "status": "NO_TIGER_DETECTED",
            "frames_processed": processed_frames,
            "detections": 0,
            "individual_tracks": 0,
            "tracks": {},
            "message": (
                "No tracked tiger detections were found. "
                "Check the model, video, and class names."
            )
        }

    return {
        "status": "TRACKING_DEMO",
        "frames_processed": processed_frames,
        "detections": detection_count,
        "individual_tracks": len(tracks),
        "tracks": tracks,
        "message": (
            "Tigers were detected and tracked within this video. "
            "Tracking IDs are temporary and do not verify "
            "individual identity across separate sightings."
        )
    }


# --------------------------------------------------
# Local Testing
# --------------------------------------------------

if __name__ == "__main__":
    test_video = BASE_DIR.parent / "test_videos" / "tiger.mp4"

    output = track_tiger_movement(test_video)

    print(output)
