from PIL import Image


def load_image(image_path):
    """
    Opens an image and converts it to RGB format.
    """
    image = Image.open(image_path).convert("RGB")
    return image


def get_image_info(image):
    """
    Returns basic information about an image.
    """
    width, height = image.size

    return {
        "width": width,
        "height": height,
        "format": image.format
    }


def check_image_size(image):
    """
    Checks whether the image is large enough for analysis.
    """
    width, height = image.size

    if width < 300 or height < 300:
        return False

    return True