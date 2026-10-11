from pathlib import Path

import cv2
from ultralytics import YOLO
from collections import defaultdict, deque


# --------------------------------------------------
# Configuration
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "tiger_detector.pt"

CONFIDENCE_THRESHOLD = 0.20
MAX_TRAIL_LENGTH = 40


# --------------------------------------------------
# Create Annotated Tracking Video
# --------------------------------------------------

def create_tracking_video(video_path, output_path):
    """
    Create an annotated video showing tiger detections,
    temporary tracking IDs, and their recent center trails.

    Tracking IDs are local to this video. They do not
    verify identity across separate sightings.
    """

    video_path = Path(video_path)
    output_path = Path(output_path)

    if not video_path.is_file():
        raise FileNotFoundError(
            f"Input video not found: {video_path}"
        )

    if not MODEL_PATH.is_file():
        raise FileNotFoundError(
            f"Tiger model not found: {MODEL_PATH}"
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    model = YOLO(str(MODEL_PATH))
    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise ValueError("Could not open input video.")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 25.0

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if width <= 0 or height <= 0:
        cap.release()
        raise ValueError(
            "Could not determine input video dimensions."
        )

    writer = cv2.VideoWriter(
        str(output_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height)
    )

    if not writer.isOpened():
        cap.release()
        raise ValueError("Could not create output video.")

    # A separate trail for each temporary tracker ID.
    trails = defaultdict(
        lambda: deque(maxlen=MAX_TRAIL_LENGTH)
    )

    frame_count = 0
    detection_count = 0

    try:
        while True:
            success, frame = cap.read()

            if not success:
                break

            result = model.track(
                source=frame,
                persist=True,
                tracker="bytetrack.yaml",
                conf=CONFIDENCE_THRESHOLD,
                verbose=False
            )[0]

            if result.boxes is not None and len(result.boxes) > 0:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    class_name = str(
                        result.names[class_id]
                    ).lower()

                    if class_name != "tiger":
                        continue

                    # ByteTrack must provide an ID for a trail.
                    if box.id is None:
                        continue

                    tracker_id = int(box.id[0])
                    confidence = float(box.conf[0])

                    x1, y1, x2, y2 = map(
                        int,
                        box.xyxy[0].tolist()
                    )

                    center = (
                        (x1 + x2) // 2,
                        (y1 + y2) // 2
                    )

                    tiger_id = f"T-{tracker_id:03d}"
                    trails[tracker_id].append(center)
                    detection_count += 1

                    # Draw tiger bounding box.
                    cv2.rectangle(
                        frame,
                        (x1, y1),
                        (x2, y2),
                        (0, 220, 120),
                        2
                    )

                    # Show temporary tracking ID and confidence.
                    label = (
                        f"{tiger_id} "
                        f"{confidence:.2f}"
                    )

                    cv2.putText(
                        frame,
                        label,
                        (x1, max(25, y1 - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 220, 120),
                        2
                    )

                    # Draw this tiger's recent trail.
                    recent_trail = list(
                        trails[tracker_id]
                    )

                    for i in range(1, len(recent_trail)):
                        cv2.line(
                            frame,
                            recent_trail[i - 1],
                            recent_trail[i],
                            (0, 180, 255),
                            2
                        )

            # Project branding.
            cv2.putText(
                frame,
                "WildTrace | Wildlife Tracking Prototype",
                (12, 28),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2
            )

            writer.write(frame)
            frame_count += 1

    finally:
        cap.release()
        writer.release()

    if frame_count == 0:
        raise ValueError(
            "The video contained no readable frames."
        )

    return {
        "status": "SUCCESS",
        "output_path": str(output_path.resolve()),
        "frames_written": frame_count,
        "tiger_detections": detection_count,
        "tracked_ids": [
            f"T-{tracker_id:03d}"
            for tracker_id in trails
        ],
        "note": (
            "The video shows tiger detections and temporary "
            "tracking trails. IDs are not verified individual "
            "identities across different videos."
        )
    }


# --------------------------------------------------
# Local Testing
# --------------------------------------------------

if __name__ == "__main__":
    input_video = (
        BASE_DIR.parent
        / "test_videos"
        / "tiger.mp4"
    )

    output_video = (
        BASE_DIR.parent
        / "outputs"
        / "wildtrace_tracking.mp4"
    )

    result = create_tracking_video(
        input_video,
        output_video
    )

    print("WildTrace tracking visualization result:")

    for key, value in result.items():
        print(f"{key}: {value}")
