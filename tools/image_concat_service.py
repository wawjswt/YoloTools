from PIL import Image
from pathlib import Path


def get_image_info(image: Image.Image) -> dict:
    width, height = image.size
    return {"width": width, "height": height, "mode": image.mode}


def tile_image(source: Image.Image, rows: int, columns: int) -> Image.Image:
    if rows <= 0 or columns <= 0:
        raise ValueError("行数和列数必须是正整数")

    width, height = source.size
    result = Image.new(source.mode, (width * columns, height * rows))
    for row in range(rows):
        for column in range(columns):
            result.paste(source, (column * width, row * height))
    return result


def concat_image_file(input_path: str, output_path: str, rows: int, columns: int) -> str:
    with Image.open(input_path) as source:
        result = tile_image(source, rows, columns)
        if Path(output_path).suffix.lower() in {".jpg", ".jpeg"} and result.mode not in {"RGB", "L"}:
            result = result.convert("RGB")
        result.save(output_path)
    return output_path
