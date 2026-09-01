from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError, features
from pillow_heif import register_heif_opener

MAX_PIXELS = 25_000_000
MAX_DIMENSION = 4096
SUPPORTED_OUTPUTS = {"PNG", "JPEG", "WEBP", "AVIF"}
OUTPUT_ALIASES = {"JPG": "JPEG"}

# Register HEIC/HEIF as Pillow-readable formats. We only need the primary image,
# so decoding embedded thumbnails is unnecessary work for this service.
register_heif_opener(thumbnails=False)


class ImageResizerError(ValueError):
    """Raised when an uploaded image cannot be safely processed."""


def _normalize_output(output: str) -> str:
    normalized = OUTPUT_ALIASES.get(output.upper(), output.upper())
    if normalized not in SUPPORTED_OUTPUTS:
        raise ImageResizerError("output must be PNG, JPEG, WEBP, or AVIF")
    return normalized


def _validate_dimensions(width: int, height: int) -> None:
    if width < 1 or height < 1 or width > MAX_DIMENSION or height > MAX_DIMENSION:
        raise ImageResizerError("dimensions out of range")


def _validate_quality(quality: int | None) -> None:
    if quality is not None and not 0 <= quality <= 100:
        raise ImageResizerError("quality must be between 0 and 100")


def _check_pixel_limit(image: Image.Image) -> None:
    if image.width * image.height > MAX_PIXELS:
        raise ImageResizerError("image pixel limit exceeded")


def _open_image(data: bytes) -> Image.Image:
    if not data:
        raise ImageResizerError("image data is empty")

    try:
        # Verify the file structure first, then reopen because verify() invalidates
        # the decoder state for subsequent image operations.
        with Image.open(BytesIO(data)) as probe:
            _check_pixel_limit(probe)
            probe.verify()

        with Image.open(BytesIO(data)) as source:
            _check_pixel_limit(source)
            source.load()
            image = ImageOps.exif_transpose(source).copy()
    except ImageResizerError:
        raise
    except Image.DecompressionBombError as exc:
        raise ImageResizerError("image pixel limit exceeded") from exc
    except (UnidentifiedImageError, OSError, EOFError, SyntaxError, RuntimeError, ValueError) as exc:
        raise ImageResizerError("invalid or unsupported image") from exc

    return image


def _ensure_encoder_available(output: str) -> None:
    feature = {"WEBP": "webp", "AVIF": "avif"}.get(output)
    if feature and not features.check(feature):
        raise ImageResizerError(f"{output} encoding is not available in this Pillow build")


def _rgb_or_rgba(image: Image.Image) -> Image.Image:
    has_alpha = "A" in image.getbands() or "transparency" in image.info
    return image.convert("RGBA" if has_alpha else "RGB")


def resize(data: bytes, width: int, height: int, output: str = "PNG", quality: int | None = None):
    _validate_dimensions(width, height)
    _validate_quality(quality)

    output = _normalize_output(output)
    _ensure_encoder_available(output)

    image = _open_image(data)
    image.thumbnail((width, height), Image.Resampling.LANCZOS)

    out = BytesIO()
    try:
        if output == "JPEG":
            _rgb_or_rgba(image).convert("RGB").save(
                out, "JPEG", quality=85 if quality is None else quality, optimize=True
            )
        elif output == "PNG":
            image.save(out, "PNG", optimize=True)
        elif output == "WEBP":
            _rgb_or_rgba(image).save(
                out, "WEBP", quality=80 if quality is None else quality, method=4
            )
        elif output == "AVIF":
            # Pillow's AVIF writer accepts 8-bit RGB/RGBA images.
            _rgb_or_rgba(image).save(
                out, "AVIF", quality=75 if quality is None else quality, speed=6
            )
    except (OSError, ValueError) as exc:
        raise ImageResizerError(f"failed to encode {output}") from exc

    return out.getvalue(), image.size


def process_upload(
    data: bytes,
    filename: str,
    content_type: str,
    output: str | None = None,
    width: int = 256,
    height: int = 256,
    quality: int | None = None,
):
    # Do not trust filename/content_type to decode the file; Pillow sniffs the bytes.
    # content_type is used only to preserve the previous default output behavior.
    default_output = "JPEG" if content_type.lower() == "image/jpeg" else "PNG"
    return resize(data, width, height, output or default_output, quality)[0]


def process(payload):
    raise ValueError("use the file-oriented CLI or provider adapter")
