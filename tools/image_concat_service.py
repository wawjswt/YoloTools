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


def concat_images(
    images: list[Image.Image],
    direction: str = "horizontal",
    gap: int = 0,
    background=None,
    alignment: str = "start",
) -> Image.Image:
    if not images:
        raise ValueError("至少需要选择一张图片")
    if direction not in {"horizontal", "vertical"}:
        raise ValueError("拼接方向必须是 horizontal 或 vertical")
    if gap < 0:
        raise ValueError("间距不能为负数")
    if alignment not in {"start", "center", "end"}:
        raise ValueError("对齐方式无效")

    mode = images[0].mode
    normalized = [image.convert(mode) if image.mode != mode else image for image in images]
    if direction == "horizontal":
        result_size = (sum(image.width for image in normalized) + gap * (len(normalized) - 1), max(image.height for image in normalized))
    else:
        result_size = (max(image.width for image in normalized), sum(image.height for image in normalized) + gap * (len(normalized) - 1))
    fill = background if background is not None else (0,) * len(normalized[0].getbands())
    result = Image.new(mode, result_size, fill)
    offset = 0
    for image in normalized:
        if direction == "horizontal":
            extra = result.height - image.height
            aligned = extra // 2 if alignment == "center" else extra if alignment == "end" else 0
            position = (offset, aligned)
            offset += image.width + gap
        else:
            extra = result.width - image.width
            aligned = extra // 2 if alignment == "center" else extra if alignment == "end" else 0
            position = (aligned, offset)
            offset += image.height + gap
        result.paste(image, position)
    return result


def concat_image_file(input_path: str, output_path: str, rows: int, columns: int) -> str:
    with Image.open(input_path) as source:
        result = tile_image(source, rows, columns)
        if Path(output_path).suffix.lower() in {".jpg", ".jpeg"} and result.mode not in {"RGB", "L"}:
            result = result.convert("RGB")
        result.save(output_path)
    return output_path
