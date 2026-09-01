import argparse
import json

from .core import process


def main():
    parser = argparse.ArgumentParser(description="Safe aspect-preserving JPEG and PNG thumbnail generation.")
    parser.add_argument("payload", nargs="?", default="{}", help="JSON input")
    args = parser.parse_args()
    print(json.dumps(process(json.loads(args.payload)), indent=2, default=str))


if __name__ == "__main__":
    main()
