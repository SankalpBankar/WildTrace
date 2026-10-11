import math
import random
import shutil
from pathlib import Path
from functools import lru_cache
from tkinter import Image
from PIL import Image

from ultralytics import YOLO


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
SOURCE_DIR = PROJECT_DIR / "dataset" / "train"
DATASET_DIR = PROJECT_DIR / "datasets" / "amur_tiger"
DATA_YAML = DATASET_DIR / "data.yaml"
OUTPUT_DIR = PROJECT_DIR / "runs" / "detect"
MODEL_PATH = BASE_DIR / "models" / "tiger_detector.pt"
TRAINING_WEIGHTS = PROJECT_DIR / "yolov8n.pt"
LABEL_CONFIDENCE = 0.10
VALIDATION_FRACTION = 0.10
ANIMAL_CLASSES = {
    "bear",
    "cat",
    "cow",
    "dog",
    "elephant",
    "giraffe",
    "horse",
    "sheep",
    "zebra",
}


@lru_cache(maxsize=1)
def get_detector():
    """Load the trained model once and reuse it."""
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(
            f"Model not found at {MODEL_PATH}. Train the model first."
        )

    return YOLO(str(MODEL_PATH))

def detect_objects(image_path):
    """
    Detect tigers and save each detected animal crop.

    Returns a list compatible with main.py's expected detection format.
    """
    image_path = Path(image_path)
    model = get_detector()

    results = model.predict(
        source=str(image_path),
        conf=0.25,
        imgsz=640,
        verbose=False,
    )

    detections = []
    crop_dir = BASE_DIR / "uploads" / "crops"
    crop_dir.mkdir(parents=True, exist_ok=True)

    for result in results:
        for index, box in enumerate(result.boxes):
            x1, y1, x2, y2 = map(
                int, box.xyxy[0].tolist()
            )

            # Ignore invalid bounding boxes.
            if x2 <= x1 or y2 <= y1:
                continue

            crop_path = crop_dir / (
                f"{image_path.stem}_detection_{index}.jpg"
            )

            with Image.open(image_path) as source_image:
                crop = source_image.crop((x1, y1, x2, y2))
                crop.save(crop_path, format="JPEG")

            detections.append({
                "class": model.names[int(box.cls[0])],
                "confidence": round(float(box.conf[0]), 4),
                "bounding_box": {
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                    "crop_path": str(crop_path),
                },
            })

    return detections


def box_iou(
    left: tuple[float, float, float, float],
    right: tuple[float, float, float, float],
) -> float:
    left_x1, left_y1 = left[0] - left[2] / 2, left[1] - left[3] / 2
    left_x2, left_y2 = left[0] + left[2] / 2, left[1] + left[3] / 2
    right_x1, right_y1 = right[0] - right[2] / 2, right[1] - right[3] / 2
    right_x2, right_y2 = right[0] + right[2] / 2, right[1] + right[3] / 2

    intersection = max(0.0, min(left_x2, right_x2) - max(left_x1, right_x1)) * max(
        0.0, min(left_y2, right_y2) - max(left_y1, right_y1)
    )
    union = left[2] * left[3] + right[2] * right[3] - intersection
    return intersection / union if union else 0.0


def create_pseudo_labeled_dataset() -> int:
    """Use animal detections as provisional tiger box labels."""
    if not SOURCE_DIR.is_dir():
        raise FileNotFoundError(f"Tiger image directory not found: {SOURCE_DIR}")

    images = sorted(SOURCE_DIR.glob("*.jpg"))
    if not images:
        raise FileNotFoundError(f"No .jpg images found in {SOURCE_DIR}")

    annotator = YOLO(str(TRAINING_WEIGHTS))

    labeled_images: list[tuple[Path, str]] = []
    predictions = annotator.predict(
        source=str(SOURCE_DIR),
        imgsz=640,
        conf=LABEL_CONFIDENCE,
        batch=8,
        stream=True,
        verbose=False,
    )
    for result in predictions:
        candidates: list[tuple[float, tuple[float, float, float, float]]] = []
        for box in result.boxes:
            if annotator.names[int(box.cls[0])] not in ANIMAL_CLASSES:
                continue
            confidence = float(box.conf[0])
            normalized_box = tuple(
                float(value) for value in box.xywhn[0]
            )
            score = confidence * math.sqrt(normalized_box[2] * normalized_box[3])
            candidates.append((score, normalized_box))

        candidates.sort(key=lambda candidate: candidate[0], reverse=True)
        selected_boxes: list[tuple[float, float, float, float]] = []
        for _, candidate in candidates:
            if all(box_iou(candidate, selected) <= 0.7 for selected in selected_boxes):
                selected_boxes.append(candidate)

        if selected_boxes:
            labels = [
                f"0 {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"
                for x_center, y_center, width, height in selected_boxes
            ]
            labeled_images.append((Path(result.path), "\n".join(labels) + "\n"))

    if len(labeled_images) < 2:
        raise RuntimeError(
            "Tiger auto-labeling found fewer than two usable images. "
            "No training dataset was created."
        )

    random.Random(42).shuffle(labeled_images)
    validation_count = max(1, round(len(labeled_images) * VALIDATION_FRACTION))
    splits = {
        "train": labeled_images[validation_count:],
        "val": labeled_images[:validation_count],
    }

    for split, samples in splits.items():
        image_dir = DATASET_DIR / "images" / split
        label_dir = DATASET_DIR / "labels" / split
        image_dir.mkdir(parents=True, exist_ok=True)
        label_dir.mkdir(parents=True, exist_ok=True)
        for image, label_text in samples:
            shutil.copy2(image, image_dir / image.name)
            (label_dir / f"{image.stem}.txt").write_text(
                label_text, encoding="utf-8"
            )

    DATA_YAML.write_text(
        f"path: {DATASET_DIR.as_posix()}\n"
        "train: images/train\n"
        "val: images/val\n"
        "names:\n"
        "  0: tiger\n",
        encoding="utf-8",
    )
    return len(labeled_images)


def main() -> None:
    if not DATA_YAML.exists():
        image_count = create_pseudo_labeled_dataset()
        print(
            f"Created provisional tiger labels for {image_count} images at "
            f"{DATASET_DIR}"
        )

    if not TRAINING_WEIGHTS.is_file():
        raise FileNotFoundError(
            f"Pretrained YOLO weights not found: {TRAINING_WEIGHTS}"
        )

    model = YOLO(str(TRAINING_WEIGHTS))
    model.train(
        data=str(DATA_YAML),
        epochs=5,
        imgsz=416,
        batch=8,
        workers=0,
        project=str(OUTPUT_DIR),
        name="tiger_detector",
        patience=5,
        exist_ok=True,
    )

    best_weights = OUTPUT_DIR / "tiger_detector" / "weights" / "best.pt"
    if not best_weights.is_file():
        raise FileNotFoundError(
            f"Training completed without producing best weights: {best_weights}"
        )
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(best_weights, MODEL_PATH)
    print(f"Training finished. Backend model saved to {MODEL_PATH}")


if __name__ == "__main__":
    main()
