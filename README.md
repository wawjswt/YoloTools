# YoloTools

YoloTools is a local desktop toolbox built with `Tkinter` for working with YOLO annotation datasets. It provides utilities for format conversion, statistics, class remapping, annotation editing, and point picking.

## Features

- Annotation format conversion
- Dataset statistics and analysis
- Batch class remapping
- YOLO annotation editor
- Point picking tool for closed shapes
- System settings and theme customization

## Conversion

Supported conversions:

- `VOC XML -> YOLO`
- `YOLO -> VOC XML`
- `YOLO -> LabelMe`
- `LabelMe -> YOLO`

The conversion page supports both single-file and batch-folder modes, and prints detailed logs for each run.

## Statistics

The statistics page analyzes YOLO label folders and reports:

- Total image count
- Labeled image count
- Empty label image count
- Total box count
- Average boxes per image
- Small, medium, and large object counts
- Class instance counts and image counts
- Box area distribution
- Aspect ratio distribution

Exports are supported in:

- `CSV`
- `Excel (.xlsx)`

## Class Remapping

Supported operations:

- Single-class replacement
- Multi-class merging
- Class deletion
- Class reordering
- Automatic mapping from a new `classes.txt`

You can preview changes before applying them, and write the result directly back to label files.

## Tools

- YOLO annotation editor
- Point picking tool for closed shapes

## Settings

Available settings include:

- Multiple theme presets
- Custom theme colors
- Font and scaling preferences
- Grid and axis toggles for charts
- Save-and-apply configuration

## Run

```bash
python main.py

Install pip install -r requirements.txt
```

## Requirements
- Python 3.10+
- tkinter
> tkinter is usually included with Python. If it is missing on your system, install the appropriate OS package first.

## Project Structure
YoloTools/
├── app/                  # Main UI pages and shared components
├── tools/                # Label processing and helper scripts
├── assets/               # Resource files
├── main.py               # Application entry point
├── requirements.txt      # Python dependencies
├── yolo_toolbox_config.json
└── README.md

## Entry Points
- main.py
- app/ui_main.py
- app/ui_convert.py
- app/ui_count.py
- app/ui_replace.py
- app/ui_tools.py
- app/ui_settings.py

## Configuration
The app writes yolo_toolbox_config.json in the project root to store theme and interface preferences.
tools/show_yolo_labels.py uses yolo_viewer_config.json to keep the annotation editor's recent paths and preferences.

## Usage Tips
- Back up your original annotation folder before converting data
- Class remapping edits label files directly, so test on a copy first
- Make sure openpyxl is installed before exporting Excel reports

## Dependencies
- matplotlib
- numpy
- opencv-python
- openpyxl
- Pillow