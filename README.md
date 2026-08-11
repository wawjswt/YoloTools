# YoloTools

一个基于 Tkinter 的本地桌面工具箱，主要用于 YOLO 标注数据的整理与辅助处理。

## 功能

- 格式转换
- 标注统计
- 类别替换
- YOLO 标注编辑器启动入口

## 项目结构

```text
YoloTools/
├─ app/                  # 主界面与功能页
├─ tools/                # 具体工具逻辑
├─ main.py               # 启动入口
└─ yolo_toolbox_config.json
```

## 当前实现

### 格式转换

`app/ui_convert.py`

当前已实现 `VOC XML -> YOLO`，并预留了 `YOLO`、`COCO JSON`、`LabelMe`、`DOTA` 等入口。

### 标注统计

`app/ui_count.py`

用于统计标注类别数量，并展示表格、图表、分布图和饼图。

### 类别替换

`app/ui_replace.py`

用于批量替换标注类别。

### 其他工具

`app/ui_tools.py`

当前提供 YOLO 标注编辑器入口，核心实现位于 `tools/show_yolo_labels.py`。

## 运行

```bash
python main.py
```

## 依赖

- `tkinter`
- `matplotlib`
- `Pillow`

安装：

```bash
pip install matplotlib pillow
```

## 适用场景

- YOLO 标注数据整理
- VOC XML 转 YOLO
- 标注统计分析
- 类别批量替换
- 本地查看和编辑 YOLO 标注
