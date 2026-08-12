# YoloTools

`YoloTools` 是一个基于 `Tkinter` 的本地桌面工具箱，用于处理 YOLO 标注数据的转换、统计、重映射、查看和编辑。

## 主要功能

- 标注格式转换
- 标注统计分析
- 类别批量重映射
- YOLO 标注编辑器启动
- 封闭图形点位拾取工具启动
- 系统设置与主题自定义

## 功能说明

### 格式转换

当前已支持：

- `VOC XML -> YOLO`
- `YOLO -> VOC XML`
- `YOLO -> LabelMe`
- `LabelMe -> YOLO`

转换页支持单文件和批量目录两种模式，并输出详细日志。

### 标注统计

可对 YOLO 标注目录进行统计分析，内容包括：

- 图片总数
- 有标注图片数
- 空标注图片数
- 总框数
- 平均每图框数
- 小/中/大目标数量
- 类别实例数与出现图片数
- 框面积分布
- 宽高比分布

支持导出为：

- `CSV`
- `Excel (.xlsx)`

### 类别重映射

支持以下操作：

- 单类替换
- 多类合并
- 类别删除
- 类别重排序
- 按新的 `classes.txt` 自动映射

支持先预览，再应用并落盘。

### 其他工具

- YOLO 标注编辑器
- 封闭图形点位拾取工具

### 系统设置

支持：

- 多种主题预设
- 自定义主题颜色
- 字体和缩放偏好
- 图表网格与坐标轴开关
- 保存并即时应用设置

## 运行方式

```bash
python main.py
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 依赖环境

- Python 3.10+
- `tkinter`

`tkinter` 通常随 Python 一起安装，如果缺失需要先安装系统组件。

## 项目结构

```text
YoloTools/
├── app/                  # 主界面与页面组件
├── tools/                # 标注处理与辅助脚本
├── assets/               # 资源文件
├── main.py               # 程序入口
├── requirements.txt      # Python 依赖
├── yolo_toolbox_config.json
└── README.md
```

## 入口文件

- `main.py`
- `app/ui_main.py`
- `app/ui_convert.py`
- `app/ui_count.py`
- `app/ui_replace.py`
- `app/ui_tools.py`
- `app/ui_settings.py`

## 配置说明

程序会在项目根目录写入 `yolo_toolbox_config.json`，主要用于保存主题和界面偏好。

## 使用建议

- 转换前先备份原始标注目录
- 类别重映射会直接修改标注文件，建议先在副本上测试
- 导出 Excel 前确认已安装 `openpyxl`

