import cv2
from pathlib import Path


# --------------------------------------------------
# Configuration
# --------------------------------------------------

FRAME_WIDTH = 320
FRAME_HEIGHT = 240
FRAME_SAMPLE_STEP = 3
MOTION_THRESHOLD = 2.0


# --------------------------------------------------
# Analyze Video Motion
# --------------------------------------------------

def analyze_movement(video_path):
    """
    Estimate overall visual motion in a video.

    This analyzes frame-to-frame visual differences.
    It does not measure tiger-specific movement or identity.
    """

    video_path = Path(video_path)

    if not video_path.exists():
        raise FileNotFoundError(
            f"Video not found: {video_path}"
        )

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise ValueError("Could not open video file.")

    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(
            cap.get(cv2.CAP_PROP_FRAME_COUNT)
        )

        if fps <= 0 or total_frames < 2:
            raise ValueError(
                "Video has insufficient readable frames "
                "or invalid FPS information."
            )

        duration = total_frames / fps

        previous_gray = None
        motion_values = []
        frames_analyzed = 0
        frame_number = 0

        while True:
            success, frame = cap.read()

            if not success:
                break

            # Sample frames to reduce processing time.
            if frame_number % FRAME_SAMPLE_STEP != 0:
                frame_number += 1
                continue

            frame = cv2.resize(
                frame,
                (FRAME_WIDTH, FRAME_HEIGHT)
            )

            gray = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2GRAY
            )

            gray = cv2.GaussianBlur(
                gray,
                (5, 5),
                0
            )

            if previous_gray is not None:
                difference = cv2.absdiff(
                    previous_gray,
                    gray
                )

                motion_score = float(
                    difference.mean()
                )

                motion_values.append(motion_score)

            previous_gray = gray
            frames_analyzed += 1
            frame_number += 1

        if not motion_values:
            raise ValueError(
                "Not enough readable sampled frames "
                "to calculate motion."
            )

        average_motion = (
            sum(motion_values) / len(motion_values)
        )

        return {
            "project": "WildTrace",
            "video_duration_seconds": round(
                duration, 2
            ),
            "video_fps": round(fps, 2),
            "total_video_frames": total_frames,
            "frames_analyzed": frames_analyzed,
            "average_frame_motion": round(
                average_motion, 3
            ),
            "motion_detected": (
                average_motion > MOTION_THRESHOLD
            ),
            "analysis_type": (
                "Sampled frame-to-frame visual motion analysis"
            ),
            "limitation": (
                "Measures overall visual change, which may "
                "include camera movement, lighting changes, "
                "background movement, or animal movement. "
                "It does not establish tiger identity or gait."
            )
        }

    finally:
        cap.release()


# --------------------------------------------------
# Local Testing
# --------------------------------------------------

if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent

    video_path = (
        base_dir
        / "test_videos"
        / "tiger.mp4"
    )

    result = analyze_movement(video_path)

    for key, value in result.items():
        print(f"{key}: {value}")
