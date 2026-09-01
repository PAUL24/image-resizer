from io import BytesIO

import pytest
from PIL import Image, features

from app.core import ImageResizerError, resize


def sample():
    out = BytesIO()
    Image.new("RGB", (200, 100), "red").save(out, "PNG")
    return out.getvalue()


def heif_sample():
    out = BytesIO()
    Image.new("RGB", (120, 80), "blue").save(out, "HEIF", quality=90)
    return out.getvalue()


def test_preserves_aspect_ratio():
    assert resize(sample(), 50, 50)[1] == (50, 25)


def test_png_output():
    assert resize(sample(), 20, 20)[0].startswith(b"\x89PNG")


def test_jpeg_output():
    assert resize(sample(), 20, 20, "JPEG")[0].startswith(b"\xff\xd8")


@pytest.mark.skipif(not features.check("webp"), reason="Pillow build has no WebP support")
def test_webp_output():
    data = resize(sample(), 20, 20, "WEBP")[0]
    assert data[:4] == b"RIFF"
    assert data[8:12] == b"WEBP"


@pytest.mark.skipif(not features.check("avif"), reason="Pillow build has no AVIF support")
def test_avif_output():
    data = resize(sample(), 20, 20, "AVIF")[0]
    assert data[4:8] == b"ftyp"
    assert data[8:12] in {b"avif", b"avis"}


def test_heif_input_can_be_resized():
    data, size = resize(heif_sample(), 60, 60, "PNG")
    assert data.startswith(b"\x89PNG")
    assert size == (60, 40)


def test_invalid_bytes():
    with pytest.raises(ImageResizerError, match="invalid or unsupported image"):
        resize(b"bad", 20, 20)


def test_dimension_limit():
    with pytest.raises(ImageResizerError, match="dimensions out of range"):
        resize(sample(), 0, 20)


def test_invalid_output_format():
    with pytest.raises(ImageResizerError, match="output must be"):
        resize(sample(), 20, 20, "GIF")


def test_invalid_quality():
    with pytest.raises(ImageResizerError, match="quality must be"):
        resize(sample(), 20, 20, "WEBP", quality=101)
