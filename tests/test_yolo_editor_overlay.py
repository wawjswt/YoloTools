from tools.yolo_editor_overlay import get_image_overlay_anchor


def test_image_overlay_anchor_is_inside_the_source_image_bottom_left_corner():
    assert get_image_overlay_anchor(1000, 500) == (8, 492)


def test_image_overlay_anchor_respects_custom_padding():
    assert get_image_overlay_anchor(120, 80, padding=12) == (12, 68)
