def get_image_overlay_anchor(image_width, image_height, padding=8):
    """返回位于原图左下角内侧的浮层数据坐标。"""
    return min(padding, image_width), max(0, image_height - padding)
