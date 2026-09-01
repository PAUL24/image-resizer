from io import BytesIO

from PIL import Image, UnidentifiedImageError

MAX_PIXELS = 25_000_000


def resize(data, width, height, output="PNG"):
    if width < 1 or height < 1 or width > 4096 or height > 4096:
        raise ValueError("dimensions out of range")
    try:
        image = Image.open(BytesIO(data))
        image.verify()
        image = Image.open(BytesIO(data))
    except UnidentifiedImageError as exc:
        raise ValueError("invalid image") from exc
    if image.width * image.height > MAX_PIXELS:
        raise ValueError("image pixel limit exceeded")
    image.thumbnail((width, height))
    out = BytesIO()
    if output.upper() == "JPEG":
        image.convert("RGB").save(out, "JPEG", quality=85)
    elif output.upper() == "PNG":
        image.save(out, "PNG")
    else:
        raise ValueError("output must be PNG or JPEG")
    return out.getvalue(), image.size


def process_upload(data, filename, content_type):
    return resize(data, 256, 256, "JPEG" if content_type == "image/jpeg" else "PNG")[0]


def process(payload):
    raise ValueError("use the file-oriented CLI or provider adapter")
