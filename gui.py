import customtkinter as ctk
from customtkinter import filedialog
from PIL import Image, ImageTk
import os
import math
import sys
from tkinterdnd2 import DND_FILES, TkinterDnD

# ---------- 主题 ----------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ---------- 工具：资源路径（兼容 exe 打包） ----------
def resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class YoruShikaApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("夜鹿风格色散工具")
        self.geometry("1200x750")
        self.minsize(1000, 650)

        # ----- 数据 -----
        self.original_img = None
        self.processed_img = None

        # 贴纸原始素材
        self.sticker_original = None   # 当前已“添加到画面”的贴纸原图
        self.pending_original = None   # 侧边栏选中但未添加的贴纸

        # 变换参数（基于中心）
        self.sticker_cx = 0.0
        self.sticker_cy = 0.0
        self.sticker_scale = 100       # 百分比
        self.sticker_angle = 0.0       # 角度（度）

        # 显示控制
        self.sticker_visible = False   # 贴纸是否显示
        self.sticker_selected = False  # 是否显示编辑框

        # 当前渲染后的贴纸（缩放+旋转后的 PIL 图像）
        self.sticker_transformed = None
        # 渲染后贴纸的尺寸（用于绘制手柄、点击检测）
        self.trans_w, self.trans_h = 0, 0
        # 渲染后贴纸在画布上的左上角（用于合成，从中心反推）
        self.sticker_x = 0.0
        self.sticker_y = 0.0

        # 拖动/调整状态
        self.drag_type = None          # "move", "scale", "rotate"
        self.drag_start = (0, 0)
        self.drag_orig_cx = 0.0
        self.drag_orig_cy = 0.0
        self.drag_orig_scale = 100
        self.drag_orig_angle = 0.0

        self.handle_size = 14
        self.scale_handle_rect = None
        self.rotate_handle_rect = None

        # ----- 注册拖放功能 -----
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.on_file_drop)

        # ----- UI 搭建 -----
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 左侧面板
        self.control_frame = ctk.CTkFrame(self, width=270, corner_radius=10)
        self.control_frame.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        self.control_frame.grid_propagate(False)

        # 打开照片
        self.btn_load = ctk.CTkButton(self.control_frame, text="📷 打开照片", command=self.load_image)
        self.btn_load.pack(pady=(15, 10), padx=15, fill="x")

        # 色散
        disp_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        disp_frame.pack(pady=5, padx=15, fill="x")
        ctk.CTkLabel(disp_frame, text="色散强度").pack(anchor="w")
        self.strength_slider = ctk.CTkSlider(disp_frame, from_=0, to=15, number_of_steps=30,
                                            command=self.update_aberration)
        self.strength_slider.set(5)
        self.strength_slider.pack(fill="x", pady=(0, 5))

        # 贴纸库
        sticker_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        sticker_frame.pack(pady=5, padx=15, fill="x")
        ctk.CTkLabel(sticker_frame, text="小人贴纸库").pack(anchor="w")

        select_row = ctk.CTkFrame(sticker_frame, fg_color="transparent")
        select_row.pack(fill="x", pady=(0, 5))
        self.sticker_listbox = ctk.CTkOptionMenu(select_row, values=[], width=140,
                                                command=self.on_sticker_select)
        self.sticker_listbox.pack(side="left", expand=True, fill="x")
        self.sticker_preview_label = ctk.CTkLabel(select_row, text="", width=60, height=60,
                                                  fg_color="#3a3a3a", corner_radius=5)
        self.sticker_preview_label.pack(side="left", padx=(5, 0))

        # 添加贴纸按钮
        self.btn_add_sticker = ctk.CTkButton(sticker_frame, text="➕ 添加到画面",
                                             command=self.add_sticker_to_canvas,
                                             state="disabled")
        self.btn_add_sticker.pack(fill="x", pady=(0, 5))

        # 调整控件
        ctk.CTkLabel(sticker_frame, text="大小 (%)").pack(anchor="w")
        self.scale_slider = ctk.CTkSlider(sticker_frame, from_=20, to=200, number_of_steps=36,
                                          command=self.update_sticker_scale)
        self.scale_slider.set(100)
        self.scale_slider.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(sticker_frame, text="旋转 (°)").pack(anchor="w")
        self.rotate_slider = ctk.CTkSlider(sticker_frame, from_=-180, to=180, number_of_steps=72,
                                           command=self.update_sticker_rotation)
        self.rotate_slider.set(0)
        self.rotate_slider.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(sticker_frame, text="💡 拖动贴纸移动 | 右下手柄缩放 | 顶手柄旋转\n拖拽图片文件到窗口可直接加载",
                     text_color="#aaaaaa", font=ctk.CTkFont(size=10)).pack(anchor="w")

        self.btn_deselect = ctk.CTkButton(sticker_frame, text="取消选中", command=self.deselect_sticker,
                                          fg_color="#555")
        self.btn_deselect.pack(pady=(5, 0))

        # 导出
        self.btn_export = ctk.CTkButton(self.control_frame, text="💾 导出效果图", command=self.export_image)
        self.btn_export.pack(pady=(10, 15), padx=15, fill="x")

        self.status_label = ctk.CTkLabel(self.control_frame, text="尚未打开图片", text_color="gray")
        self.status_label.pack(side="bottom", pady=(0, 10))

        # 预览画布
        self.canvas = ctk.CTkCanvas(self, bg="#1a1a1a", highlightthickness=1, highlightbackground="#444")
        self.canvas.grid(row=0, column=1, padx=(0, 15), pady=15, sticky="nsew")
        self.canvas.bind("<ButtonPress-1>", self.canvas_mouse_down)
        self.canvas.bind("<B1-Motion>", self.canvas_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.canvas_mouse_up)

        # 初始化贴纸目录
        self.sticker_dir = resource_path("stickers")
        if not os.path.exists(self.sticker_dir):
            os.makedirs(self.sticker_dir, exist_ok=True)
            with open(os.path.join(self.sticker_dir, "放置PNG贴纸.txt"), "w") as f:
                f.write("请将透明背景小人PNG放入此文件夹。")
        self.refresh_sticker_list()

    # ==================== 拖拽文件处理 ====================
    def on_file_drop(self, event):
        # 拖拽获得的文件路径列表（用花括号包裹）
        file_list = self.tk.splitlist(event.data)
        if file_list:
            path = file_list[0].strip('{}')   # 去掉两端的花括号
            self.load_image_from_path(path)

    # ==================== 坐标转换 ====================
    def _canvas_to_original(self, canvas_x, canvas_y):
        ratio = self._get_canvas_scale()
        return (canvas_x - 10) / ratio, (canvas_y - 10) / ratio

    def _get_canvas_scale(self):
        if self.original_img is None:
            return 1.0
        canvas_w = self.canvas.winfo_width()
        max_w = canvas_w - 20 if canvas_w > 50 else 800
        img_w = self.original_img.width
        return max_w / img_w if img_w > max_w else 1.0

    # ==================== 贴纸管理 ====================
    def refresh_sticker_list(self):
        files = []
        if os.path.exists(self.sticker_dir):
            for f in os.listdir(self.sticker_dir):
                if f.lower().endswith('.png'):
                    files.append(f)
        self.sticker_listbox.configure(values=files)
        if files:
            self.sticker_listbox.set(files[0])
            self.on_sticker_select(files[0])
        else:
            self.sticker_listbox.set("")
            self.pending_original = None
            self.sticker_preview_label.configure(image=None, text="无贴纸")
            self.btn_add_sticker.configure(state="disabled")

    def on_sticker_select(self, choice):
        """仅预览缩略图，不自动添加到画面"""
        if not choice:
            return
        path = os.path.join(self.sticker_dir, choice)
        try:
            self.pending_original = Image.open(path).convert("RGBA")
            thumb = self.pending_original.copy()
            thumb.thumbnail((60, 60), Image.LANCZOS)
            self._thumb_tk = ImageTk.PhotoImage(thumb)
            self.sticker_preview_label.configure(image=self._thumb_tk, text="")
            self.status_label.configure(text=f"已选择：{choice}")
            self.btn_add_sticker.configure(state="normal")
        except Exception as e:
            self.status_label.configure(text=f"加载失败：{e}")

    def add_sticker_to_canvas(self):
        """将侧边栏选中的贴纸正式添加到画面"""
        if self.pending_original is None:
            return
        self.sticker_original = self.pending_original
        self.sticker_scale = int(self.scale_slider.get())
        self.sticker_angle = 0.0
        self.rotate_slider.set(0)
        # 放到照片中央
        if self.original_img:
            self.sticker_cx = self.original_img.width / 2
            self.sticker_cy = self.original_img.height / 2
        else:
            self.sticker_cx, self.sticker_cy = 0, 0
        self.sticker_visible = True
        self.sticker_selected = True
        self.update_sticker_transform()
        self.update_preview()

    def update_sticker_transform(self):
        """根据 scale + angle 生成当前贴纸图像，并计算左上角坐标"""
        if self.sticker_original is None:
            return
        w_orig, h_orig = self.sticker_original.size
        # 缩放
        new_w = max(1, int(w_orig * self.sticker_scale / 100))
        new_h = max(1, int(h_orig * self.sticker_scale / 100))
        scaled = self.sticker_original.resize((new_w, new_h), Image.LANCZOS)
        # 旋转（expand=True 保证完整显示）
        rotated = scaled.rotate(self.sticker_angle, resample=Image.BICUBIC, expand=True)
        self.sticker_transformed = rotated
        self.trans_w, self.trans_h = rotated.size
        # 左上角坐标 = 中心 - 新尺寸/2
        self.sticker_x = self.sticker_cx - self.trans_w / 2
        self.sticker_y = self.sticker_cy - self.trans_h / 2

    def update_sticker_scale(self, event=None):
        if self.sticker_original is None or not self.sticker_visible:
            return
        self.sticker_scale = int(self.scale_slider.get())
        self.update_sticker_transform()
        self.update_preview()

    def update_sticker_rotation(self, event=None):
        if self.sticker_original is None or not self.sticker_visible:
            return
        self.sticker_angle = float(self.rotate_slider.get())
        self.update_sticker_transform()
        self.update_preview()

    def deselect_sticker(self):
        self.sticker_selected = False
        self.update_preview()

    # ==================== 鼠标交互 ====================
    def canvas_mouse_down(self, event):
        if self.original_img is None or not self.sticker_visible:
            if self.sticker_selected:
                self.sticker_selected = False
                self.update_preview()
            return

        # ------ 用画布坐标优先检测手柄 ------
        # 检测旋转手柄
        if self.rotate_handle_rect is not None:
            rx1, ry1, rx2, ry2 = self.rotate_handle_rect
            if rx1 <= event.x <= rx2 and ry1 <= event.y <= ry2:
                self.drag_type = "rotate"
                self.drag_start = (event.x, event.y)
                self.drag_orig_angle = self.sticker_angle
                self.drag_orig_cx = self.sticker_cx
                self.drag_orig_cy = self.sticker_cy
                if not self.sticker_selected:
                    self.sticker_selected = True
                    self.update_preview()
                return

        # 检测缩放手柄
        if self.scale_handle_rect is not None:
            sx1, sy1, sx2, sy2 = self.scale_handle_rect
            if sx1 <= event.x <= sx2 and sy1 <= event.y <= sy2:
                self.drag_type = "scale"
                self.drag_start = (event.x, event.y)
                self.drag_orig_cx = self.sticker_cx
                self.drag_orig_cy = self.sticker_cy
                self.drag_orig_scale = self.sticker_scale
                if not self.sticker_selected:
                    self.sticker_selected = True
                    self.update_preview()
                return

        # ------ 检测贴纸本体 ------
        # 将鼠标画布坐标转为原图坐标
        orig_x, orig_y = self._canvas_to_original(event.x, event.y)
        sx, sy = self.sticker_x, self.sticker_y
        sw, sh = self.trans_w, self.trans_h
        if sx <= orig_x <= sx + sw and sy <= orig_y <= sy + sh:
            self.drag_type = "move"
            self.drag_start = (event.x, event.y)
            self.drag_orig_cx = self.sticker_cx
            self.drag_orig_cy = self.sticker_cy
            if not self.sticker_selected:
                self.sticker_selected = True
                self.update_preview()
            return

        # ------ 空白区域：取消选中 ------
        if self.sticker_selected:
            self.sticker_selected = False
            self.update_preview()
    def canvas_mouse_move(self, event):
        if self.drag_type is None:
            return
        ratio = self._get_canvas_scale()
        if self.drag_type == "move":
            dx = (event.x - self.drag_start[0]) / ratio
            dy = (event.y - self.drag_start[1]) / ratio
            self.sticker_cx = self.drag_orig_cx + dx
            self.sticker_cy = self.drag_orig_cy + dy
            self.update_sticker_transform()
            self.update_preview()
        elif self.drag_type == "scale":
            # 根据鼠标到中心距离缩放
            dx = event.x - (10 + self.sticker_cx * ratio)
            dy = event.y - (10 + self.sticker_cy * ratio)
            dist = math.hypot(dx, dy)
            init_dx = self.drag_start[0] - (10 + self.drag_orig_cx * ratio)
            init_dy = self.drag_start[1] - (10 + self.drag_orig_cy * ratio)
            init_dist = math.hypot(init_dx, init_dy)
            if init_dist == 0: return
            scale_change = dist / init_dist
            new_scale = max(20, min(200, self.drag_orig_scale * scale_change))
            self.sticker_scale = int(new_scale)
            self.scale_slider.set(self.sticker_scale)
            self.update_sticker_transform()
            self.update_preview()
        elif self.drag_type == "rotate":
            # 计算鼠标相对于中心的方位角
            center_cx = 10 + self.sticker_cx * ratio
            center_cy = 10 + self.sticker_cy * ratio
            angle1 = math.atan2(self.drag_start[1] - center_cy, self.drag_start[0] - center_cx)
            angle2 = math.atan2(event.y - center_cy, event.x - center_cx)
            delta = math.degrees(angle2 - angle1)
            new_angle = (self.drag_orig_angle + delta) % 360
            if new_angle > 180: new_angle -= 360
            self.sticker_angle = new_angle
            self.rotate_slider.set(new_angle)
            self.update_sticker_transform()
            self.update_preview()

    def canvas_mouse_up(self, event):
        self.drag_type = None

    # ==================== 预览绘制 ====================
    def update_preview(self):
        if self.processed_img is None and self.original_img is None:
            return
        if self.processed_img is None:
            self.processed_img = self.original_img.copy()

        base = self.processed_img.convert("RGBA")
        # 合成贴纸（若可见）
        if self.sticker_visible and self.sticker_transformed is not None:
            px, py = int(self.sticker_x), int(self.sticker_y)
            base.paste(self.sticker_transformed, (px, py), self.sticker_transformed)

        self.display_img = base

        # 画布显示
        img_width, img_height = self.display_img.size
        canvas_w = self.canvas.winfo_width()
        max_w = canvas_w - 20 if canvas_w > 50 else 800
        if img_width > max_w:
            scale = max_w / img_width
            new_w = max_w
            new_h = int(img_height * scale)
        else:
            scale = 1.0
            new_w, new_h = img_width, img_height
        resized = self.display_img.resize((new_w, new_h), Image.LANCZOS)
        self._preview_tk = ImageTk.PhotoImage(resized)
        self.canvas.delete("all")
        self.canvas.create_image(10, 10, anchor="nw", image=self._preview_tk)

        # 绘制编辑框（如果选中且可见）
        if self.sticker_visible and self.sticker_selected and self.sticker_transformed is not None:
            sx, sy = self.sticker_x, self.sticker_y
            sw, sh = self.trans_w, self.trans_h
            rx1 = 10 + sx * scale
            ry1 = 10 + sy * scale
            rx2 = 10 + (sx + sw) * scale
            ry2 = 10 + (sy + sh) * scale
            # 缩放手柄（右下角）
            sx1 = rx2 - self.handle_size
            sy1 = ry2 - self.handle_size
            sx2 = rx2 + self.handle_size
            sy2 = ry2 + self.handle_size
            self.canvas.create_rectangle(sx1, sy1, sx2, sy2, fill="#00aaff", outline="")
            self.scale_handle_rect = (sx1, sy1, sx2, sy2)

            # 旋转手柄（顶部中心）
            top_cx = (rx1 + rx2) / 2
            top_cy = ry1
            rx1_rot = top_cx - self.handle_size
            ry1_rot = top_cy - self.handle_size * 2
            rx2_rot = top_cx + self.handle_size
            ry2_rot = top_cy
            self.canvas.create_oval(rx1_rot, ry1_rot, rx2_rot, ry2_rot, fill="#ffaa00", outline="")
            self.rotate_handle_rect = (rx1_rot, ry1_rot, rx2_rot, ry2_rot)

    # ==================== 色散 ====================
    def chromatic_aberration(self, img, strength):
        if strength == 0 or img is None:
            return img.copy() if img else None
        sx = int(strength)
        sy = int(strength * 0.7)
        r, g, b = img.split()
        r = r.transform(img.size, Image.AFFINE, (1, 0, -sx, 0, 1, -sy))
        b = b.transform(img.size, Image.AFFINE, (1, 0, sx, 0, 1, sy))
        return Image.merge("RGB", (r, g, b))

    # ==================== 图片加载 ====================
    def load_image_from_path(self, path):
        """通过文件路径加载图片"""
        try:
            self.original_img = Image.open(path).convert("RGB")
            self.status_label.configure(text=f"已加载：{os.path.basename(path)}")
            self.apply_aberration()
            self.auto_fit_window()
        except Exception as e:
            self.status_label.configure(text=f"加载失败：{e}")
    def auto_fit_window(self):
        if self.original_img is None:
            return
        # 获取屏幕可用尺寸（留出边缘）
        screen_width = self.winfo_screenwidth() - 100
        screen_height = self.winfo_screenheight() - 120
        img_w, img_h = self.original_img.size
        # 计算合适的窗口大小（左侧面板约 270px，右侧留边距）
        panel_width = 270 + 40
        target_w = img_w + panel_width
        target_h = img_h + 40
        # 如果太大，等比缩放
        if target_w > screen_width or target_h > screen_height:
            scale = min(screen_width / target_w, screen_height / target_h)
            target_w = int(target_w * scale)
            target_h = int(target_h * scale)
        self.geometry(f"{target_w}x{target_h}")

    def load_image(self):
        """按钮打开文件对话框加载"""
        path = filedialog.askopenfilename(filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp")])
        if not path:
            return
        self.load_image_from_path(path)

    def apply_aberration(self):
        if self.original_img is None:
            return
        strength = self.strength_slider.get()
        self.processed_img = self.chromatic_aberration(self.original_img, strength)
        self.update_preview()

    def update_aberration(self, event=None):
        self.apply_aberration()

    # ==================== 导出 ====================
    def export_image(self):
        if self.processed_img is None:
            self.status_label.configure(text="没有图片可导出")
            return
        self.update_preview()
        path = filedialog.asksaveasfilename(defaultextension=".png",
                                            filetypes=[("PNG 图片", "*.png"), ("JPEG 图片", "*.jpg")])
        if not path:
            return
        try:
            self.display_img.convert("RGB").save(path)
            self.status_label.configure(text=f"已保存：{os.path.basename(path)}")
        except Exception as e:
            self.status_label.configure(text=f"保存失败：{e}")

if __name__ == "__main__":
    app = YoruShikaApp()
    app.mainloop()