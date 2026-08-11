# YoloTools

`YoloTools` 是一个基于 `Tkinter` 的本地桌面工具箱，用于处理 YOLO 标注数据的转换、统计、重映射和辅助查看。项目主入口统一在桌面界面中，适合日常标注整理、格式迁移和数据检查。

## 主要功能

- 标注格式转换
- 标注统计分析
- 类别批量重映射
- YOLO 标注编辑器启动
- 封闭图形点位拾取工具启动

## 功能说明

### 1. 格式转换

当前已实现 `VOC XML -> YOLO` 转换。

支持的界面入口已经预留了后续扩展空间，包含：

- `YOLO`
- `VOC XML`
- `COCO JSON`
- `LabelMe`
- `DOTA`

现阶段真正可用的转换逻辑是 `VOC XML -> YOLO`，其余格式后续可继续补充。

### 2. 标注统计

可对某个 YOLO 标注目录进行统计分析，输出内容包括：

- 图片总数
- 有标注图片数
- 空标注图片数
- 总框数
- 平均每图框数
- 小/中/大目标数量
- 类别实例数与出现图片数
- 框面积分布
- 宽高比分布

统计结果可在界面中查看，并支持导出为：

- `CSV`
- `Excel (.xlsx)`

### 3. 类别重映射

支持对 YOLO 标注文件中的类别 ID 进行批量处理，包含：

- 单类替换
- 多类合并
- 类别删除
- 类别重排序
- 按新的 `classes.txt` 自动映射

该功能会同时更新标注文件和 `classes.txt`，适合在整理类别体系时使用。

### 4. 其他工具

工具页提供两个独立窗口入口：

- YOLO 标注编辑器
- 封闭图形点位拾取工具

## 运行方式

```bash
python main.py
```

## 依赖环境

- Python 3.10+
- `tkinter`
- `matplotlib`
- `Pillow`
- `openpyxl`（仅导出 Excel 时需要）

安装示例：

```bash
pip install matplotlib pillow openpyxl
```

如果你的 Python 环境未包含 `tkinter`，需要先安装对应的系统组件。

## 项目结构

```text
YoloTools/
├── app/                  # 主界面与页面组件
├── tools/                # 标注处理与辅助脚本
├── assets/               # 资源文件
├── main.py               # 程序入口
├── yolo_toolbox_config.json
└── README.md
```

## 入口文件

- `main.py`：启动应用
- `app/ui_main.py`：主窗口和导航逻辑
- `app/ui_convert.py`：格式转换页
- `app/ui_count.py`：统计分析页
- `app/ui_replace.py`：类别重映射页
- `app/ui_tools.py`：其他工具页

## 当前实现状态

- `VOC XML -> YOLO` 转换已实现
- YOLO 标注统计已实现
- 类别重映射已实现
- YOLO 编辑器和点位拾取器已接入启动入口
- 其他格式转换入口已预留，尚未完整实现

## 配置说明

程序会在项目根目录写入 `yolo_toolbox_config.json`，当前主要用于保存界面主题等状态信息。

## 使用建议

- 转换前先备份原始标注目录
- 类别重映射会直接修改标注文件，建议先在副本上测试
- 导出 Excel 前确认已安装 `openpyxl`

## 适用场景

- YOLO 标注数据整理
- VOC XML 转 YOLO
- 标注类别统计分析
- 类别批量替换与重排
- 本地查看和编辑 YOLO 标注

