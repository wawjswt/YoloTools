from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


@dataclass
class LabelFileResult:
    path: str
    modified: bool
    changed_count: int


def read_classes_file(path: str) -> List[str]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def write_classes_file(path: str, classes: Sequence[str]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        f.write("\n".join(classes))


def _parse_label_line(line: str):
    parts = line.strip().split()
    if len(parts) < 5 or not parts[0].lstrip("-").isdigit():
        return None
    try:
        return int(parts[0]), parts[1:]
    except ValueError:
        return None


def _write_label_line(class_id: int, rest: Sequence[str]) -> str:
    return " ".join([str(class_id), *rest]) + "\n"


def collect_label_classes(folder: str) -> List[int]:
    ids = set()
    for txt in Path(folder).rglob("*.txt"):
        with txt.open("r", encoding="utf-8") as f:
            for line in f:
                parsed = _parse_label_line(line)
                if parsed is None:
                    continue
                cid, _ = parsed
                ids.add(cid)
    return sorted(ids)


def rewrite_label_file(path: Path, mapping: Dict[int, Optional[int]]) -> LabelFileResult:
    changed = 0
    modified = False
    out_lines = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            parsed = _parse_label_line(line)
            if parsed is None:
                out_lines.append(line)
                continue

            cid, rest = parsed
            if cid not in mapping:
                out_lines.append(_write_label_line(cid, rest))
                continue

            new_cid = mapping[cid]
            modified = True
            changed += 1
            if new_cid is None:
                continue
            out_lines.append(_write_label_line(new_cid, rest))

    if modified:
        with path.open("w", encoding="utf-8") as f:
            f.writelines(out_lines)

    return LabelFileResult(path=str(path), modified=modified, changed_count=changed)


def apply_mapping_to_folder(folder: str, mapping: Dict[int, Optional[int]]) -> List[LabelFileResult]:
    results = []
    for txt in Path(folder).rglob("*.txt"):
        results.append(rewrite_label_file(txt, mapping))
    return results


def build_remap_from_new_classes(old_classes: Sequence[str], new_classes: Sequence[str]) -> Dict[int, Optional[int]]:
    name_to_old = {name: idx for idx, name in enumerate(old_classes)}
    mapping: Dict[int, Optional[int]] = {}
    for new_idx, name in enumerate(new_classes):
        if name in name_to_old:
            mapping[name_to_old[name]] = new_idx
    for old_idx, name in enumerate(old_classes):
        if name not in new_classes:
            mapping[old_idx] = None
    return mapping


def reorder_classes(classes: Sequence[str], order: Sequence[int]) -> List[str]:
    return [classes[i] for i in order if 0 <= i < len(classes)]


def merge_classes(classes: Sequence[str], groups: Sequence[Sequence[int]], target_names: Sequence[str]) -> Tuple[List[str], Dict[int, Optional[int]]]:
    new_classes = list(classes)
    mapping: Dict[int, Optional[int]] = {}
    taken = set()
    for target_name, group in zip(target_names, groups):
        target_idx = len(new_classes)
        new_classes.append(target_name)
        for old_idx in group:
            mapping[old_idx] = target_idx
            taken.add(old_idx)
    for idx in range(len(classes)):
        if idx not in taken and idx not in mapping:
            mapping[idx] = idx
    return new_classes, mapping


def remap_classes_by_index(classes: Sequence[str], mapping: Dict[int, Optional[int]]) -> List[str]:
    out = list(classes)
    for old_idx, new_idx in mapping.items():
        if new_idx is None or not (0 <= old_idx < len(out)) or not (0 <= new_idx < len(out)):
            continue
        out[new_idx] = classes[old_idx]
    return out


def swap_class_names(classes: Sequence[str], src: int, dst: int) -> List[str]:
    out = list(classes)
    if 0 <= src < len(out) and 0 <= dst < len(out):
        out[src], out[dst] = out[dst], out[src]
    return out
