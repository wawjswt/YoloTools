from __future__ import annotations

import json
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


@dataclass
class BBox:
    class_name: str
    class_id: int
    x_center: float
    y_center: float
    width: float
    height: float


def _clip(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _iter_files(path: str, suffixes: Sequence[str]) -> List[Path]:
    p = Path(path)
    if p.is_file():
        return [p] if p.suffix.lower() in suffixes else []
    return [x for x in p.rglob("*") if x.suffix.lower() in suffixes]


def _find_image_size(base_path: Path) -> Tuple[int, int]:
    for ext in (".jpg", ".jpeg", ".png", ".bmp", ".webp"):
        img = base_path.with_suffix(ext)
        if img.exists():
            try:
                from PIL import Image

                with Image.open(img) as im:
                    return im.size
            except Exception:
                continue
    return 0, 0


def read_yolo_classes(classes_file: Optional[str]) -> List[str]:
    if not classes_file or not os.path.exists(classes_file):
        return []
    with open(classes_file, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def parse_yolo_file(label_path: str) -> List[Tuple[int, float, float, float, float]]:
    out = []
    with open(label_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 5:
                continue
            try:
                out.append((int(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])))
            except ValueError:
                continue
    return out


def yolo_to_voc_xml(image_size: Tuple[int, int], labels: List[BBox], image_name: str) -> str:
    w, h = image_size
    ann = ET.Element("annotation")
    ET.SubElement(ann, "filename").text = image_name
    size = ET.SubElement(ann, "size")
    ET.SubElement(size, "width").text = str(w)
    ET.SubElement(size, "height").text = str(h)
    ET.SubElement(size, "depth").text = "3"
    for box in labels:
        xmin = int(round((box.x_center - box.width / 2) * w))
        ymin = int(round((box.y_center - box.height / 2) * h))
        xmax = int(round((box.x_center + box.width / 2) * w))
        ymax = int(round((box.y_center + box.height / 2) * h))
        obj = ET.SubElement(ann, "object")
        ET.SubElement(obj, "name").text = box.class_name
        bnd = ET.SubElement(obj, "bndbox")
        ET.SubElement(bnd, "xmin").text = str(max(0, xmin))
        ET.SubElement(bnd, "ymin").text = str(max(0, ymin))
        ET.SubElement(bnd, "xmax").text = str(max(0, xmax))
        ET.SubElement(bnd, "ymax").text = str(max(0, ymax))
    return ET.tostring(ann, encoding="unicode")


def voc_xml_to_yolo(xml_path: str, class_map: Dict[str, int]) -> Tuple[Tuple[int, int], List[BBox]]:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    size = root.find("size")
    w = int(size.findtext("width", "0")) if size is not None else 0
    h = int(size.findtext("height", "0")) if size is not None else 0
    boxes = []
    for obj in root.findall("object"):
        name = (obj.findtext("name", "") or "").strip()
        if name not in class_map:
            continue
        bnd = obj.find("bndbox")
        if bnd is None:
            continue
        xmin = float(bnd.findtext("xmin", "0"))
        ymin = float(bnd.findtext("ymin", "0"))
        xmax = float(bnd.findtext("xmax", "0"))
        ymax = float(bnd.findtext("ymax", "0"))
        xc = ((xmin + xmax) / 2) / w if w else 0
        yc = ((ymin + ymax) / 2) / h if h else 0
        bw = (xmax - xmin) / w if w else 0
        bh = (ymax - ymin) / h if h else 0
        boxes.append(BBox(name, class_map[name], _clip(xc), _clip(yc), _clip(bw), _clip(bh)))
    return (w, h), boxes


def yolo_to_labelme(size: Tuple[int, int], labels: List[BBox], image_path: str) -> dict:
    w, h = size
    return {
        "version": "5.0.1",
        "flags": {},
        "shapes": [
            {
                "label": box.class_name,
                "points": [
                    [(box.x_center - box.width / 2) * w, (box.y_center - box.height / 2) * h],
                    [(box.x_center + box.width / 2) * w, (box.y_center + box.height / 2) * h],
                ],
                "group_id": None,
                "shape_type": "rectangle",
                "flags": {},
            }
            for box in labels
        ],
        "imagePath": Path(image_path).name,
        "imageData": None,
        "imageHeight": h,
        "imageWidth": w,
    }


def labelme_to_yolo(json_path: str, class_map: Dict[str, int]) -> Tuple[Tuple[int, int], List[BBox], str]:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    w = int(data.get("imageWidth") or 0)
    h = int(data.get("imageHeight") or 0)
    labels: List[BBox] = []
    for shape in data.get("shapes", []):
        if shape.get("shape_type") not in ("rectangle", None):
            continue
        name = (shape.get("label") or "").strip()
        if name not in class_map:
            continue
        pts = shape.get("points") or []
        if len(pts) < 2:
            continue
        (x1, y1), (x2, y2) = pts[0], pts[1]
        xmin, xmax = sorted([float(x1), float(x2)])
        ymin, ymax = sorted([float(y1), float(y2)])
        xc = ((xmin + xmax) / 2) / w if w else 0
        yc = ((ymin + ymax) / 2) / h if h else 0
        bw = (xmax - xmin) / w if w else 0
        bh = (ymax - ymin) / h if h else 0
        labels.append(BBox(name, class_map[name], _clip(xc), _clip(yc), _clip(bw), _clip(bh)))
    return (w, h), labels, str(data.get("imagePath") or Path(json_path).stem)


def convert_file(src_format: str, dst_format: str, input_path: str, output_dir: Optional[str], classes_file: Optional[str]) -> List[str]:
    classes = read_yolo_classes(classes_file)
    class_map = {name: idx for idx, name in enumerate(classes)}
    out_dir = Path(output_dir or Path(input_path).parent)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs: List[str] = []

    if src_format == "VOC XML" and dst_format == "YOLO":
        for xml in _iter_files(input_path, [".xml"]):
            size, boxes = voc_xml_to_yolo(str(xml), {name: idx for idx, name in enumerate(classes)}) if classes else voc_xml_to_yolo(str(xml), {})
            txt = out_dir / f"{xml.stem}.txt"
            with txt.open("w", encoding="utf-8") as f:
                for box in boxes:
                    f.write(f"{box.class_id} {box.x_center:.6f} {box.y_center:.6f} {box.width:.6f} {box.height:.6f}\n")
            outputs.append(str(txt))
        return outputs

    if src_format == "YOLO" and dst_format == "VOC XML":
        for txt in _iter_files(input_path, [".txt"]):
            image_size = _find_image_size(txt)
            boxes = []
            for cid, xc, yc, bw, bh in parse_yolo_file(str(txt)):
                name = classes[cid] if cid < len(classes) else str(cid)
                boxes.append(BBox(name, cid, xc, yc, bw, bh))
            xml = out_dir / f"{txt.stem}.xml"
            xml.write_text(yolo_to_voc_xml(image_size, boxes, f"{txt.stem}.jpg"), encoding="utf-8")
            outputs.append(str(xml))
        return outputs

    if src_format == "YOLO" and dst_format == "LabelMe":
        for txt in _iter_files(input_path, [".txt"]):
            image_size = _find_image_size(txt)
            boxes = []
            for cid, xc, yc, bw, bh in parse_yolo_file(str(txt)):
                name = classes[cid] if cid < len(classes) else str(cid)
                boxes.append(BBox(name, cid, xc, yc, bw, bh))
            json_path = out_dir / f"{txt.stem}.json"
            payload = yolo_to_labelme(image_size, boxes, f"{txt.stem}.jpg")
            json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            outputs.append(str(json_path))
        return outputs

    if src_format == "LabelMe" and dst_format == "YOLO":
        for js in _iter_files(input_path, [".json"]):
            _, boxes, _ = labelme_to_yolo(str(js), class_map)
            txt = out_dir / f"{js.stem}.txt"
            with txt.open("w", encoding="utf-8") as f:
                for box in boxes:
                    f.write(f"{box.class_id} {box.x_center:.6f} {box.y_center:.6f} {box.width:.6f} {box.height:.6f}\n")
            outputs.append(str(txt))
        return outputs

    raise NotImplementedError(f"Unsupported conversion: {src_format} -> {dst_format}")
