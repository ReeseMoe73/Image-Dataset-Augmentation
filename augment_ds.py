"""
- The module will copy three original un-augmented photos to an output folder dataset, the
auto racing photo is png, the boat photo is small, and photo labeled underexposure is
underexposed. The module writes 13 augmentations per image to a folder labeled augmented_images_out.
The program requires pillow to be installed.
"""

import argparse
from pathlib import Path
import shutil
from PIL import Image, ImageOps, ImageEnhance, ImageFilter

# images to rgb if png
def convert_rgb(img: Image.Image, background=(255, 255, 255)) -> Image.Image:

    mode = img.mode
    if mode == "RGB":
        return img
    if mode in ("RGBA", "LA"):
        base = Image.new("RGB", img.size, background)
        rgb = img.convert("RGB")
        alpha = img.getchannel("A")
        base.paste(rgb, mask=alpha)
        return base
    return img.convert("RGB")


recognize_formats = {'.bmp', '.jpeg', '.jpg', '.png', '.tif', '.tiff', '.webp'}
# this will return true if it points a path of real image
def true_image(p: Path) -> bool:
    return p.is_file() and p.suffix.lower() in recognize_formats

def guarantee_rgb_for_jpeg(img: Image.Image, ext: str) -> Image.Image:
    #JPEG can't save RGBA/CMYK; convert to RGB as necessary #
    if ext in {'.jpg', '.jpeg'} and img.mode not in ('RGB', 'L'):
        return img.convert('RGB')
    return img
# Image transformations
def augmentations(img: Image.Image):

    yield "flipHorizontal", ImageOps.mirror(img)
    yield "flipVertical", ImageOps.flip(img)
    yield "rotate90degrees", img.rotate(90, expand=True)
    yield "rotate270", img.rotate(270, expand=True)
    yield "bright125", ImageEnhance.Brightness(img).enhance(1.50)
    yield "contrast125", ImageEnhance.Contrast(img).enhance(1.50)
    yield "sharp150", ImageEnhance.Sharpness(img).enhance(1.5)
    yield "blur", img.filter(ImageFilter.BLUR)


def save_image(img: Image.Image, ext: str) -> bytes:
    #import ByteIO module
    from io import BytesIO
    bio = BytesIO()
    fmt = {
        '.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG', '.bmp': 'BMP',
        '.tif': 'TIFF', '.tiff': 'TIFF', '.webp': 'WEBP',
    }.get(ext.lower(), 'PNG')
    save_options = {}
    if fmt == 'JPEG':
        save_options.update(dict(quality=95, optimize=True))
    img.save(bio, format=fmt, **save_options)
    return bio.getvalue()


def process_dataset(input_dir: Path, output_dir: Path, copy_originals: bool = True) -> int:
    images = [p for p in input_dir.rglob("*") if true_image(p)]
    if not images:
        print(f"No images found in {input_dir} with extensions: {sorted(recognize_formats)}")
        return 1

    num_originals, num_augmented = 0, 0

    for src in images:
        rel = src.relative_to(input_dir)
        dest_dir = (output_dir / rel).parent
        dest_dir.mkdir(parents=True, exist_ok=True)

        # 1) Copy original
        if copy_originals:
            try:
                shutil.copy2(src, dest_dir / src.name)
                num_originals += 1
            except Exception as e:
                print(f"[ERROR] Copy failed for {src}: {e}")

        # 2) Create and save augmented variants
        try:
            with Image.open(src) as im:
                im.load()
                ext = src.suffix.lower()
                base = convert_rgb(im)  # normalize modes for enhancers

                for suffix, aug in augmentations(base):
                    aug = guarantee_rgb_for_jpeg(aug, ext)
                    out_name = f"{src.stem}__{suffix}{ext}"
                    (dest_dir / out_name).write_bytes(save_image(aug, ext))
                    num_augmented += 1
        except Exception as e:
            print(f"[ERROR] Skipping {src}: {e}")

    print(f"[COMPLETED] Dataset output to: {output_dir}")
    print(f"[DATA] Originals copied to: {num_originals} | Augmented files written: {num_augmented}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Simple, deterministic image dataset augmenter.")
    parser.add_argument(
        "-i", "--input",
        required=False,
        default=r"C:\Users\might\OneDrive\Desktop\augmented_images",
        help="Path to the input folder containing images. Defaults to your OneDrive Desktop 'augmented_images'."
    )
    parser.add_argument(
        "-o", "--output", default=None,
        help="Path to output folder. Default: <input>_out"
    )
    parser.add_argument(
        "--no-copy-originals", action="store_true",
        help="If set, will not copy original images (only augmentations)."
    )
    args = parser.parse_args()

    input_dir = Path(args.input).expanduser()
    if not input_dir.exists():
        parser.error(f"Input folder not found: {input_dir}")

    output_dir = Path(args.output).expanduser() if args.output else input_dir.parent / (input_dir.name + "_out")
    output_dir.mkdir(parents=True, exist_ok=True)

    exit_code = process_dataset(
        input_dir=input_dir,
        output_dir=output_dir,
        copy_originals=not args.no_copy_originals
    )
    raise SystemExit(exit_code)

if __name__ == "__main__":
    main()
