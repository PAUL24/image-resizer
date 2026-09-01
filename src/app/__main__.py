import argparse
from pathlib import Path

from .core import ImageResizerError, resize

EXTENSION_TO_FORMAT = {
    ".png": "PNG",
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".webp": "WEBP",
    ".avif": "AVIF",
}


def main():
    parser = argparse.ArgumentParser(
        description="Resize JPEG, PNG, WebP, AVIF, HEIC, or HEIF images while preserving aspect ratio."
    )
    parser.add_argument("input", type=Path, help="Source image, including .heic/.heif")
    parser.add_argument("output", type=Path, help="Destination .png/.jpg/.webp/.avif file")
    parser.add_argument("--width", type=int, default=256, help="Maximum output width (default: 256)")
    parser.add_argument("--height", type=int, default=256, help="Maximum output height (default: 256)")
    parser.add_argument("--format", choices=["png", "jpeg", "jpg", "webp", "avif"], help="Override output format")
    parser.add_argument("--quality", type=int, help="JPEG/WebP/AVIF quality, 0-100")
    args = parser.parse_args()

    output_format = args.format.upper() if args.format else EXTENSION_TO_FORMAT.get(args.output.suffix.lower())
    if output_format == "JPG":
        output_format = "JPEG"
    if output_format is None:
        parser.error("cannot infer output format; use .png/.jpg/.webp/.avif or --format")

    try:
        data = args.input.read_bytes()
        resized, size = resize(data, args.width, args.height, output_format, args.quality)
        args.output.write_bytes(resized)
    except (ImageResizerError, OSError) as exc:
        parser.error(str(exc))

    print(f"Wrote {args.output} ({size[0]}x{size[1]}, {output_format})")


if __name__ == "__main__":
    main()
