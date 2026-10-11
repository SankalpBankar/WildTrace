
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.image_utils import load_image, get_image_info
from backend.detector import detect_objects
from backend.reidentifier import compare_with_gallery
from backend.video_tracking import track_tiger_movement


# --------------------------------------------------
# FastAPI Application
# --------------------------------------------------

app = FastAPI(
    title="WildTrace",
    description=(
        "Wildlife Detection, Tracking, and "
        "Individual Re-Identification Prototype"
    ),
    version="0.5.0",
)


# --------------------------------------------------
# CORS Configuration for React Frontend
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Directories
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

UPLOAD_FOLDER = BASE_DIR / "uploads"
IMAGE_FOLDER = UPLOAD_FOLDER / "images"
VIDEO_FOLDER = UPLOAD_FOLDER / "videos"

IMAGE_FOLDER.mkdir(parents=True, exist_ok=True)
VIDEO_FOLDER.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# Supported File Formats and Size Limits
# --------------------------------------------------

ALLOWED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}

ALLOWED_VIDEO_EXTENSIONS = {
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
    ".webm",
}

MAX_IMAGE_SIZE = 15 * 1024 * 1024       # 15 MB
MAX_VIDEO_SIZE = 200 * 1024 * 1024      # 200 MB


# --------------------------------------------------
# Utility: Save Uploaded File with Size Limit
# --------------------------------------------------

async def save_upload(
    file: UploadFile,
    destination: Path,
    max_size: int,
) -> int:
    """Save an uploaded file in chunks with a maximum size limit."""

    total_size = 0

    try:
        with destination.open("wb") as output:
            while True:
                chunk = await file.read(1024 * 1024)

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > max_size:
                    raise HTTPException(
                        status_code=413,
                        detail=(
                            "File exceeds the maximum allowed size "
                            f"of {max_size // (1024 * 1024)} MB."
                        ),
                    )

                output.write(chunk)

        if total_size == 0:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is empty.",
            )

        return total_size

    except Exception:
        destination.unlink(missing_ok=True)
        raise


# --------------------------------------------------
# Home Route
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "project": "WildTrace",
        "message": "WildTrace API is running.",
        "version": "0.5.0",
        "available_endpoints": {
            "health": "/health",
            "image_upload": "/upload",
            "video_upload": "/upload-video",
            "api_documentation": "/docs",
        },
    }


# --------------------------------------------------
# Health Check
# --------------------------------------------------

@app.get("/health")
def health():
    return {
        "project": "WildTrace",
        "status": "healthy",
    }


# --------------------------------------------------
# Image Upload and Processing
# --------------------------------------------------

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    try:
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="No filename provided.",
            )

        extension = Path(file.filename).suffix.lower()

        if extension not in ALLOWED_IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Unsupported image format. Upload JPG, "
                    "JPEG, PNG, or WEBP."
                ),
            )

        file_path = IMAGE_FOLDER / f"{uuid4().hex}{extension}"

        file_size = await save_upload(
            file=file,
            destination=file_path,
            max_size=MAX_IMAGE_SIZE,
        )

        # Validate the uploaded image.
        try:
            image = load_image(file_path)
            image_info = get_image_info(image)
        except Exception as error:
            file_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=400,
                detail=f"Invalid or unreadable image: {error}",
            ) from error

        # Detect animals in the image.
        try:
            detections = detect_objects(str(file_path))
        except FileNotFoundError as error:
            raise HTTPException(
                status_code=503,
                detail=f"Detection model or required file missing: {error}",
            ) from error
        except Exception as error:
            raise HTTPException(
                status_code=500,
                detail=f"Object detection failed: {error}",
            ) from error

        # Re-identify each detection using its image crop.
        reidentification_results = []

        for detection in detections:
            bounding_box = detection.get("bounding_box", {})
            crop_path = bounding_box.get("crop_path")

            if not crop_path or not Path(crop_path).is_file():
                reidentification_results.append({
                    "detection": detection,
                    "reidentification": {
                        "status": "UNKNOWN",
                        "message": "Detection crop is missing.",
                        "matches": [],
                    },
                })
                continue

            try:
                match_result = compare_with_gallery(crop_path)

                reidentification_results.append({
                    "detection": detection,
                    "reidentification": match_result,
                })

            except (FileNotFoundError, ValueError) as error:
                reidentification_results.append({
                    "detection": detection,
                    "reidentification": {
                        "status": "UNKNOWN",
                        "message": str(error),
                        "matches": [],
                    },
                })

            except Exception as error:
                # Preserve successful detections even if one gallery
                # comparison fails.
                reidentification_results.append({
                    "detection": detection,
                    "reidentification": {
                        "status": "ERROR",
                        "message": f"Gallery comparison failed: {error}",
                        "matches": [],
                    },
                })

        return {
            "project": "WildTrace",
            "input_type": "image",
            "filename": file.filename,
            "file_size_bytes": file_size,
            "message": "Image processed successfully.",
            "image_info": image_info,
            "detection_count": len(detections),
            "detections": detections,
            "reidentification_results": reidentification_results,
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Image processing failed: {error}",
        ) from error

    finally:
        await file.close()


# --------------------------------------------------
# Video Upload and Tiger Tracking
# --------------------------------------------------

@app.post("/upload-video")
async def upload_video(file: UploadFile = File(...)):
    try:
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="No filename provided.",
            )

        extension = Path(file.filename).suffix.lower()

        if extension not in ALLOWED_VIDEO_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Unsupported video format. Upload MP4, AVI, "
                    "MOV, MKV, or WEBM."
                ),
            )

        video_path = VIDEO_FOLDER / f"{uuid4().hex}{extension}"

        file_size = await save_upload(
            file=file,
            destination=video_path,
            max_size=MAX_VIDEO_SIZE,
        )

        # Keep the existing video tracking implementation.
        results = track_tiger_movement(video_path)

        return {
            "project": "WildTrace",
            "input_type": "video",
            "filename": file.filename,
            "file_size_bytes": file_size,
            "message": "Video processed successfully.",
            "results": results,
        }

    except HTTPException:
        raise

    except (FileNotFoundError, ValueError) as error:
        raise HTTPException(
            status_code=400,
            detail=f"Tiger video tracking failed: {error}",
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Tiger video tracking failed: {error}",
        ) from error

    finally:
        await file.close()
