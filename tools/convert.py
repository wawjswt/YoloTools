# tools/convert.py
import os
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    size = root.find("size")
    if size is None:
        return None, []

    width = int(size.findtext("width", "0"))
    height = int(size.findtext("height", "0"))

    objects = []
    for obj in root.findall("object"):
        name = obj.findtext("name", "").strip()
        bnd = obj.find("bndbox")
        if not name or bnd is None:
            continue

        xmin = float(bnd.findtext("xmin", "0"))
        ymin = float(bnd.findtext("ymin", "0"))
        xmax = float(bnd.findtext("xmax", "0"))
        ymax = float(bnd.findtext("ymax", "0"))

        objects.append({
            "name": name,
            "bbox": (xmin, ymin, xmax, ymax)
        })

    return (width, height), objects


def convert_box(size, box):
    w, h = size
    xmin, ymin, xmax, ymax = box
    x_center = (xmin + xmax) / 2.0 / w
    y_center = (ymin + ymax) / 2.0 / h
    bw = (xmax - xmin) / w
    bh = (ymax - ymin) / h
    return x_center, y_center, bw, bh


def load_class_file(class_file):
    if not os.path.exists(class_file):
        print(f"类别文件不存在：{class_file}")
        return None
    with open(class_file, "r", encoding="utf-8") as f:
        classes = [x.strip() for x in f.readlines() if x.strip()]
    return {name: idx for idx, name in enumerate(classes)}


def collect_classes(folder):
    class_set = set()
    for xml in Path(folder).rglob("*.xml"):
        _, objects = parse_xml(xml)
        for obj in objects:
            class_set.add(obj["name"])
    return sorted(class_set)


def process_single_file(xml_file, out_dir, class_map):
    size, objects = parse_xml(xml_file)
    if not size:
        print(f"跳过无效文件：{xml_file}")
        return

    out_dir = out_dir or os.path.dirname(xml_file)
    os.makedirs(out_dir, exist_ok=True)

    txt_path = os.path.join(out_dir, Path(xml_file).stem + ".txt")
    lines = []
    for obj in objects:
        cls = obj["name"]
        if cls not in class_map:
            continue
        cls_id = class_map[cls]
        x, y, w, h = convert_box(size, obj["bbox"])
        lines.append(f"{cls_id} {x:.6f} {y:.6f} {w:.6f} {h:.6f}")

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"已转换：{xml_file} -> {txt_path}")


def process_folder(folder, out_dir, class_map):
    folder = Path(folder)
    xml_files = list(folder.rglob("*.xml"))
    if not xml_files:
        print("未找到 XML 文件")
        return

    for xml_file in xml_files:
        process_single_file(str(xml_file), out_dir, class_map)