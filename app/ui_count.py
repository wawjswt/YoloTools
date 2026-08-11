import csv
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from .theme import *
from .ui_convert import SectionCard
from tools.count_labels import analyze_folder, export_csv, export_xlsx


class CountPage(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app
        self.stats = None
        self._build()

    def _build(self):
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(20, 12))
        tk.Label(top, text="类别统计增强", bg=BG, fg=TEXT, font=("Microsoft YaHei UI", 20, "bold")).pack(anchor="w")
        tk.Label(top, text="统计类别实例、图片覆盖、空标签、尺寸分布与宽高比分布，输出会同步刷新图表与摘要。", bg=BG, fg=MUTED, font=("Microsoft YaHei UI", 10)).pack(anchor="w", pady=(4, 0))

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(1, weight=1)

        left = SectionCard(body, "统计参数")
        left.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 10))
        left.grid_propagate(False)

        self.var_folder = tk.StringVar()

        form = tk.Frame(left, bg=PANEL)
        form.pack(fill="x", padx=16, pady=(0, 12))
        form.grid_columnconfigure(1, weight=1)
        tk.Label(form, text="标注文件夹", bg=PANEL, fg=TEXT, font=("Microsoft YaHei UI", 10)).grid(row=0, column=0, sticky="w", pady=8)
        ttk.Entry(form, textvariable=self.var_folder).grid(row=0, column=1, sticky="ew", padx=10, pady=8)
        ttk.Button(form, text="浏览", command=self.browse).grid(row=0, column=2, pady=8)

        actions = tk.Frame(left, bg=PANEL)
        actions.pack(fill="x", padx=16, pady=(0, 12))
        ttk.Button(actions, text="开始统计", style="Primary.TButton", command=self.run).pack(fill="x")
        ttk.Button(actions, text="导出 CSV", command=self.export_csv).pack(fill="x", pady=(8, 0))
        ttk.Button(actions, text="导出 Excel", command=self.export_excel).pack(fill="x", pady=(8, 0))
        ttk.Button(actions, text="清空结果", command=self.clear_results).pack(fill="x", pady=(8, 0))

        self.summary_box = tk.LabelFrame(left, text="摘要", bg=PANEL, fg=TEXT, padx=10, pady=10)
        self.summary_box.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self.summary_text = tk.Text(self.summary_box, height=14, wrap="word", bg="#08111d", fg="#dbeafe", relief="flat", insertbackground="white")
        self.summary_text.pack(fill="both", expand=True)

        right = SectionCard(body, "统计结果")
        right.grid(row=0, column=1, rowspan=2, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        self.notebook = ttk.Notebook(right)
        self.notebook.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self.table_tab = tk.Frame(self.notebook, bg=PANEL)
        self.chart_tab = tk.Frame(self.notebook, bg=PANEL)
        self.dist_tab = tk.Frame(self.notebook, bg=PANEL)
        self.pie_tab = tk.Frame(self.notebook, bg=PANEL)

        self.notebook.add(self.table_tab, text="表格")
        self.notebook.add(self.chart_tab, text="柱状图")
        self.notebook.add(self.dist_tab, text="分布图")
        self.notebook.add(self.pie_tab, text="饼图")

        self.tree = ttk.Treeview(self.table_tab, columns=("class_id", "instances", "images"), show="headings")
        self.tree.heading("class_id", text="类别ID")
        self.tree.heading("instances", text="实例数")
        self.tree.heading("images", text="出现图片数")
        self.tree.column("class_id", width=120, anchor="center")
        self.tree.column("instances", width=120, anchor="center")
        self.tree.column("images", width=120, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=12, pady=12)

        self.fig = Figure(figsize=(8, 5), dpi=100)
        self.ax_bar = self.fig.add_subplot(211)
        self.ax_empty = self.fig.add_subplot(212)
        self.chart_canvas = FigureCanvasTkAgg(self.fig, master=self.chart_tab)
        self.chart_canvas.get_tk_widget().pack(fill="both", expand=True)

        self.fig2 = Figure(figsize=(8, 5), dpi=100)
        self.ax_area = self.fig2.add_subplot(211)
        self.ax_aspect = self.fig2.add_subplot(212)
        self.dist_canvas = FigureCanvasTkAgg(self.fig2, master=self.dist_tab)
        self.dist_canvas.get_tk_widget().pack(fill="both", expand=True)

        self.fig3 = Figure(figsize=(6, 4), dpi=100)
        self.ax_pie = self.fig3.add_subplot(111)
        self.pie_canvas = FigureCanvasTkAgg(self.fig3, master=self.pie_tab)
        self.pie_canvas.get_tk_widget().pack(fill="both", expand=True)

    def browse(self):
        p = filedialog.askdirectory(title="选择标注文件夹")
        if p:
            self.var_folder.set(p)

    def clear_results(self):
        self.stats = None
        self.summary_text.delete("1.0", tk.END)
        for item in self.tree.get_children():
            self.tree.delete(item)
        for ax in (self.ax_bar, self.ax_empty, self.ax_area, self.ax_aspect, self.ax_pie):
            ax.clear()
        self.chart_canvas.draw_idle()
        self.dist_canvas.draw_idle()
        self.pie_canvas.draw_idle()

    def run(self):
        folder = self.var_folder.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("错误", "请选择有效文件夹")
            return

        def task():
            try:
                stats = analyze_folder(folder)
                self.after(0, lambda: self.render_stats(stats))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("错误", str(e)))

        threading.Thread(target=task, daemon=True).start()

    def render_stats(self, stats):
        self.stats = stats
        self.summary_text.delete("1.0", tk.END)
        summary = [
            f"文件夹: {stats.folder}",
            f"图片总数: {stats.total_images}",
            f"有标注图片数: {stats.labeled_images}",
            f"空标签图片数: {stats.empty_images}",
            f"总框数: {stats.total_boxes}",
            f"每张图平均框数: {stats.avg_boxes_per_image:.4f}",
            f"小目标: {stats.small_count}",
            f"中目标: {stats.medium_count}",
            f"大目标: {stats.large_count}",
            f"类别数: {len(stats.class_stats)}",
            f"面积分布项: {len(stats.area_bins)}",
            f"宽高比分布项: {len(stats.aspect_ratio_bins)}",
        ]
        self.summary_text.insert("1.0", "\n".join(summary))

        for item in self.tree.get_children():
            self.tree.delete(item)
        for item in stats.class_stats:
            self.tree.insert("", "end", values=(item.class_id, item.instance_count, item.image_count))

        self._draw_bar(stats)
        self._draw_dist(stats)
        self._draw_pie(stats)

    def _draw_bar(self, stats):
        self.ax_bar.clear()
        self.ax_empty.clear()

        class_ids = [str(x.class_id) for x in stats.class_stats]
        instances = [x.instance_count for x in stats.class_stats]
        images = [x.image_count for x in stats.class_stats]

        self.ax_bar.bar(class_ids, instances, color="#2563eb")
        self.ax_bar.set_title("各类别实例数")
        self.ax_bar.set_ylabel("Instances")
        self.ax_bar.tick_params(axis="x", rotation=45)

        self.ax_empty.bar(["空标签", "有标注"], [stats.empty_images, stats.labeled_images], color=["#ef4444", "#10b981"])
        self.ax_empty.set_title("空标签图片 vs 有标注图片")

        self.fig.tight_layout()
        self.chart_canvas.draw_idle()

    def _draw_dist(self, stats):
        self.ax_area.clear()
        self.ax_aspect.clear()

        area_keys = list(stats.area_bins.keys())
        area_vals = list(stats.area_bins.values())
        aspect_keys = list(stats.aspect_ratio_bins.keys())
        aspect_vals = list(stats.aspect_ratio_bins.values())

        self.ax_area.bar(area_keys, area_vals, color="#0ea5e9")
        self.ax_area.set_title("框面积分布")
        self.ax_area.tick_params(axis="x", rotation=30)

        self.ax_aspect.bar(aspect_keys, aspect_vals, color="#f59e0b")
        self.ax_aspect.set_title("宽高比分布")
        self.ax_aspect.tick_params(axis="x", rotation=30)

        self.fig2.tight_layout()
        self.dist_canvas.draw_idle()

    def _draw_pie(self, stats):
        self.ax_pie.clear()
        labels = ["小目标", "中目标", "大目标"]
        values = [stats.small_count, stats.medium_count, stats.large_count]
        self.ax_pie.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
        self.ax_pie.set_title("小中大目标比例")
        self.fig3.tight_layout()
        self.pie_canvas.draw_idle()

    def export_csv(self):
        if not self.stats:
            messagebox.showwarning("提示", "请先统计")
            return
        path = filedialog.asksaveasfilename(title="导出 CSV", defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not path:
            return
        export_csv(self.stats, path)
        messagebox.showinfo("提示", f"已导出到 {path}")

    def export_excel(self):
        if not self.stats:
            messagebox.showwarning("提示", "请先统计")
            return
        path = filedialog.asksaveasfilename(title="导出 Excel", defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if not path:
            return
        try:
            export_xlsx(self.stats, path)
            messagebox.showinfo("提示", f"已导出到 {path}")
        except Exception as e:
            messagebox.showerror("错误", str(e))
