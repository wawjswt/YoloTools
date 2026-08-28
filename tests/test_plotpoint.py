from pathlib import Path

from PIL import Image

import tools.plotpoint as plotpoint
from tools.plotpoint import PointPicker, PointRecord


class _Canvas:
    def delete(self, *_args):
        pass

    def create_image(self, *_args, **_kwargs):
        return 1

    def create_rectangle(self, *_args, **_kwargs):
        return 2


class _CountingImage:
    def __init__(self):
        self.size = (100, 80)
        self.resize_calls = 0

    def resize(self, size, _resampling):
        self.resize_calls += 1
        return Image.new("RGB", size)


def _picker_without_window(points=None):
    picker = PointPicker.__new__(PointPicker)
    picker.root = object()
    picker.points = list(points or [])
    picker.closed = False
    picker.active_index = None
    picker.export_path = None
    picker.image_path = None
    picker.orig_image = None
    picker.photo = None
    picker.image_id = None
    picker._set_status = lambda _text: None
    picker._refresh_list = lambda: None
    picker.redraw = lambda: None
    return picker


def test_txt_export_keeps_legacy_plain_flat_coordinate_line(tmp_path, monkeypatch):
    output = tmp_path / "points.txt"
    picker = _picker_without_window(
        [PointRecord(0.1, 0.2), PointRecord(0.3, 0.4), PointRecord(0.5, 0.6)]
    )
    monkeypatch.setattr(plotpoint.filedialog, "asksaveasfilename", lambda **_kwargs: str(output))

    picker.export_points()

    assert output.read_text(encoding="utf-8") == "0.100000,0.200000,0.300000,0.400000,0.500000,0.600000"


def test_declining_image_load_keeps_existing_blank_canvas_points(tmp_path, monkeypatch):
    image_path = tmp_path / "reference.png"
    Image.new("RGB", (8, 8)).save(image_path)
    original_points = [PointRecord(0.1, 0.2), PointRecord(0.3, 0.4)]
    picker = _picker_without_window(original_points)
    picker._set_status = lambda text: setattr(picker, "last_status", text)
    monkeypatch.setattr(plotpoint.filedialog, "askopenfilename", lambda **_kwargs: str(image_path))
    monkeypatch.setattr(plotpoint.messagebox, "askyesno", lambda *_args, **_kwargs: False, raising=False)

    picker.load_image()

    assert picker.points == original_points
    assert picker.orig_image is None
    assert "取消" in picker.last_status


def test_redraw_reuses_scaled_image_when_canvas_size_does_not_change(monkeypatch):
    source = _CountingImage()
    picker = PointPicker.__new__(PointPicker)
    picker.canvas = _Canvas()
    picker.orig_image = source
    picker.points = []
    picker.photo = None
    picker.image_id = None
    picker._display_cache_key = None
    picker._set_status = lambda _text: None
    picker._display_rect = lambda: (0, 0, 50, 40)
    photo_calls = []
    monkeypatch.setattr(
        plotpoint.ImageTk,
        "PhotoImage",
        lambda image: photo_calls.append(image) or image,
    )

    picker.redraw()
    picker.redraw()

    assert source.resize_calls == 1
    assert len(photo_calls) == 1
