
from pathlib import Path

from PIL import (
    Image,
    ImageStat,
    ImageChops,
    UnidentifiedImageError,
)


# --------------------------------------------------
# Configuration
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

# User uploads are NOT automatically the reference gallery.
UPLOADS_FOLDER = BASE_DIR / "uploads"

# Store previously registered tiger reference images here.
GALLERY_FOLDER = BASE_DIR / "tiger_gallery"

# Location for crops extracted from uploaded media.
CROPS_FOLDER = BASE_DIR / "tiger_crops"

SUPPORTED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp"
}

# Demonstration threshold only; not validated for identity.
SIMILARITY_THRESHOLD = 0.90

IMAGE_SIZE = (128, 128)


# --------------------------------------------------
# Compare Two Images
# --------------------------------------------------

def compare_images(image_path_1, image_path_2):
    """Calculate basic pixel similarity, not verified identity."""

    image_path_1 = Path(image_path_1)
    image_path_2 = Path(image_path_2)

    if not image_path_1.is_file():
        raise FileNotFoundError(
            f"Image not found: {image_path_1}"
        )

    if not image_path_2.is_file():
        raise FileNotFoundError(
            f"Image not found: {image_path_2}"
        )

    try:
        with Image.open(image_path_1) as image:
            image_1 = image.convert("RGB").resize(IMAGE_SIZE)

        with Image.open(image_path_2) as image:
            image_2 = image.convert("RGB").resize(IMAGE_SIZE)

    except (UnidentifiedImageError, OSError) as error:
        raise ValueError(
            f"Could not read an image: {error}"
        ) from error

    difference = ImageChops.difference(image_1, image_2)

    mean_difference = sum(
        ImageStat.Stat(difference).mean
    ) / 3

    similarity = max(
        0.0,
        1.0 - mean_difference / 255.0
    )

    return round(similarity, 3)


# --------------------------------------------------
# Compare Against Tiger Gallery
# --------------------------------------------------

def compare_with_gallery(
    query_path,
    gallery_folder=None,
    top_k=5,
):
    """
    Rank reference images against a query tiger crop.

    Supports images directly inside the gallery and
    images nested inside individual tiger folders.

    A possible match is not verified identity.
    """

    query_path = Path(query_path).resolve()

    gallery_path = (
        Path(gallery_folder).resolve()
        if gallery_folder is not None
        else GALLERY_FOLDER.resolve()
    )

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    if not query_path.is_file():
        return {
            "status": "UNKNOWN",
            "message": f"Query image not found: {query_path}",
            "matches": [],
        }

    if not gallery_path.is_dir():
        return {
            "status": "UNKNOWN",
            "message": (
                f"Reference gallery not found: {gallery_path}. "
                "Create tiger_gallery and add reference images."
            ),
            "matches": [],
        }

    # Search recursively, but include only supported image files.
    gallery_images = sorted(
        path for path in gallery_path.rglob("*")
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_EXTENSIONS
        and path.resolve() != query_path
    )

    if not gallery_images:
        return {
            "status": "UNKNOWN",
            "message": (
                "The tiger gallery is empty. Add reference "
                "images before attempting re-identification."
            ),
            "matches": [],
        }

    matches = []

    for image_path in gallery_images:
        try:
            score = compare_images(query_path, image_path)

            # If stored inside tiger_001/, use tiger_001
            # as the candidate identity.
            # Otherwise, use the image filename.
            relative_path = image_path.relative_to(gallery_path)

            if len(relative_path.parts) > 1:
                candidate = relative_path.parts[0]
            else:
                candidate = image_path.stem

            matches.append({
                "candidate": candidate,
                "similarity": score,
                "image_path": str(image_path.resolve()),
            })

        except (FileNotFoundError, ValueError) as error:
            print(f"Skipping {image_path}: {error}")

    matches.sort(
        key=lambda item: item["similarity"],
        reverse=True,
    )

    top_matches = matches[:top_k]

    if not top_matches:
        return {
            "status": "UNKNOWN",
            "message": "No usable gallery images were found.",
            "matches": [],
        }

    best_match = top_matches[0]

    if best_match["similarity"] < SIMILARITY_THRESHOLD:
        return {
            "status": "UNKNOWN",
            "message": (
                "Best visual similarity is below the "
                "demonstration threshold."
            ),
            "best_similarity": best_match["similarity"],
            "matches": top_matches,
        }

    return {
        "status": "POSSIBLE_MATCH",
        "candidate": best_match["candidate"],
        "similarity": best_match["similarity"],
        "score_type": "Basic pixel similarity",
        "identity_verified": False,
        "matches": top_matches,
    }


# --------------------------------------------------
# Local Testing
# --------------------------------------------------

if __name__ == "__main__":
    query_image = CROPS_FOLDER / "tiger_1.jpg"

    results = compare_with_gallery(query_image)

    print("WildTrace re-identification result:")
    print(results)
