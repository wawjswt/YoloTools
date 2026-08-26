from PIL import Image
import pytest

from tools.image_concat_service import get_image_info, tile_image


def test_tile_image_repeats_source_in_row_major_grid():
    source = Image.new("RGB", (2, 3), (10, 20, 30))

    result = tile_image(source, rows=2, columns=4)

    assert result.size == (8, 6)
    assert result.getpixel((0, 0)) == (10, 20, 30)
    assert result.getpixel((2, 3)) == (10, 20, 30)
    assert result.getpixel((7, 5)) == (10, 20, 30)


@pytest.mark.parametrize("rows, columns", [(0, 2), (2, 0), (-1, 2), (2, -1)])
def test_tile_image_rejects_non_positive_grid_size(rows, columns):
    source = Image.new("RGB", (2, 2))

    with pytest.raises(ValueError, match="正整数"):
        tile_image(source, rows=rows, columns=columns)


def test_concat_image_file_converts_transparency_for_jpeg(tmp_path):
    input_path = tmp_path / "source.png"
    output_path = tmp_path / "result.jpg"
    Image.new("RGBA", (2, 2), (10, 20, 30, 128)).save(input_path)

    from tools.image_concat_service import concat_image_file

    concat_image_file(str(input_path), str(output_path), rows=1, columns=1)

    with Image.open(output_path) as result:
        assert result.format == "JPEG"
        assert result.mode == "RGB"


def test_get_image_info_reports_dimensions_and_mode():
    source = Image.new("RGBA", (3, 4), (10, 20, 30, 128))

    info = get_image_info(source)

    assert info == {"width": 3, "height": 4, "mode": "RGBA"}
