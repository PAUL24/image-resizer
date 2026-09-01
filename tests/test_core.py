from io import BytesIO

import pytest
from PIL import Image

from app.core import resize


def sample():
    out = BytesIO()
    Image.new("RGB", (200, 100), "red").save(out, "PNG")
    return out.getvalue()


def test_preserves_aspect_ratio():
    assert resize(sample(), 50, 50)[1] == (50, 25)


def test_png_output():
    assert resize(sample(), 20, 20)[0].startswith(b"\x89PNG")


def test_jpeg_output():
    assert resize(sample(), 20, 20, "JPEG")[0].startswith(b"\xff\xd8")


def test_invalid_bytes():
    with pytest.raises(ValueError):
        resize(b"bad", 20, 20)


def test_dimension_limit():
    with pytest.raises(ValueError):
        resize(sample(), 0, 20)
