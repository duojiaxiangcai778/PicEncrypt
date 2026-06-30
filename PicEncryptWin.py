#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片混淆 - Windows 桌面版
基于 https://github.com/jiarandiana0307/PicEncrypt 移植
支持6种图片混淆方法
"""

import os
import sys

# ─── 依赖检测 ───
try:
    from PIL import Image as PILImage, ImageTk
except ImportError:
    import sys
    msg = (
        "❌ 缺少依赖: Pillow (PIL)\n\n"
        "请用以下任意一种方式运行：\n\n"
        "  ✅ 方案一：双击「图片混淆.exe」（推荐，免安装）\n"
        "  ✅ 方案二：双击「运行源码.bat」（自动用 uv 运行）\n"
        "  ✅ 方案三：在终端执行：uv run python PicEncryptWin.py\n"
        "  ✅ 方案四：安装依赖后运行：uv pip install pillow numpy\n"
    )
    out = sys.stderr or sys.__stderr__ or sys.stdout or open(os.devnull, 'w')
    out.write(msg + "\n")
    out.flush()
    os._exit(1)  # 直接终止，避免 sys.exit 在 except 块中产生异常链 traceback

try:
    import numpy as np
except ImportError:
    import sys
    msg = (
        "❌ 缺少依赖: numpy\n\n"
        "请用以下任意一种方式运行：\n\n"
        "  ✅ 双击「图片混淆.exe」（推荐，免安装）\n"
        "  ✅ 双击「运行源码.bat」\n"
        "  ✅ uv run python PicEncryptWin.py\n"
        "  ✅ uv pip install numpy\n"
    )
    out = sys.stderr or sys.__stderr__ or sys.stdout or open(os.devnull, 'w')
    out.write(msg + "\n")
    out.flush()
    os._exit(1)

import json
import math
import hashlib
import traceback as _tb
import threading
from datetime import datetime

# ─── tkinter ───
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ═══════════════════════════════════════════════
# 日志
# ═══════════════════════════════════════════════
_LOG_FILE = None

def _log_path():
    global _LOG_FILE
    if _LOG_FILE:
        return _LOG_FILE
    try:
        if getattr(sys, 'frozen', False):
            d = os.path.dirname(os.path.abspath(sys.executable))
        else:
            d = os.path.dirname(os.path.abspath(__file__))
        _LOG_FILE = os.path.join(d, "_picencrypt.log")
    except Exception:
        _LOG_FILE = "_picencrypt.log"
    return _LOG_FILE

def _log_error(context, exc=None):
    try:
        if exc is None:
            exc = _tb.format_exc()
        elif isinstance(exc, BaseException):
            exc = f"{type(exc).__name__}: {exc}\n{_tb.format_exc()}"
        with open(_log_path(), 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{context}]\n{exc}\n---\n")
    except Exception:
        pass

# ═══════════════════════════════════════════════
# 算法模块
# ═══════════════════════════════════════════════

def _md5_shuffle(length, key):
    """基于 MD5 的 Fisher-Yates 洗牌 (对应 BasePixelScramble.shuffle)"""
    arr = list(range(length))
    for i in range(length - 1, 0, -1):
        md5 = hashlib.md5(f"{key}{i}".encode('utf-8')).hexdigest()
        # 取前7位十六进制转 int
        rand = int(md5[:7], 16) % (i + 1)
        arr[rand], arr[i] = arr[i], arr[rand]
    return arr


def _generate_logistic(x1, n):
    """生成 Logistic 映射序列 (对应 BasePicEncryptScramble.generateLogistic)"""
    arr = np.zeros((n, 2))
    x = x1
    arr[0, 0] = x
    arr[0, 1] = 0
    for i in range(1, n):
        x = 3.9999999 * x * (1 - x)
        arr[i, 0] = x
        arr[i, 1] = i
    return arr


def _get_sorted_positions(logistic_map):
    """按 Logistic 值排序得到索引序列 (对应 BasePicEncryptScramble.getSortedPositions)"""
    n = len(logistic_map)
    sorted_indices = np.argsort(logistic_map[:, 0])
    positions = np.zeros(n, dtype=int)
    for i in range(n):
        positions[i] = int(logistic_map[sorted_indices[i], 1])
    return positions


# ─── 算法1: 小番茄图片混淆 (TomatoScramble) ───
def tomato_scramble(pixels, width, height, key, encrypt=True):
    """Gilbert 2D 空间填充曲线 + 黄金比例偏移"""
    pixel_count = len(pixels)
    offset_val = int(round((math.sqrt(5) - 1) / 2 * pixel_count * key))
    positions = _gilbert2d(width, height)
    loop_pos = pixel_count - offset_val
    new_pixels = np.zeros(pixel_count, dtype=np.int32)

    if encrypt:
        # ENCRYPT: new[positions[i+offset]] = pixels[positions[i]]
        for i in range(loop_pos):
            new_pixels[positions[i + offset_val]] = pixels[positions[i]]
        for i in range(loop_pos, pixel_count):
            new_pixels[positions[i - loop_pos]] = pixels[positions[i]]
    else:
        # DECRYPT: new[positions[i]] = pixels[positions[i+offset]]
        for i in range(loop_pos):
            new_pixels[positions[i]] = pixels[positions[i + offset_val]]
        for i in range(loop_pos, pixel_count):
            new_pixels[positions[i]] = pixels[positions[i - loop_pos]]

    return new_pixels.tolist(), width, height


def _gilbert2d(width, height):
    """生成 Gilbert 2D 空间填充曲线坐标序列"""
    pixel_count = width * height
    positions = np.zeros(pixel_count, dtype=int)
    pos = [0]

    def generate2d(x, y, ax, ay, bx, by):
        w = abs(ax + ay)
        h = abs(bx + by)
        dax = int(math.copysign(1, ax)) if ax != 0 else 0
        day = int(math.copysign(1, ay)) if ay != 0 else 0
        dbx = int(math.copysign(1, bx)) if bx != 0 else 0
        dby = int(math.copysign(1, by)) if by != 0 else 0

        if h == 1:
            for _ in range(w):
                positions[pos[0]] = x + y * width
                pos[0] += 1
                x += dax
                y += day
            return

        if w == 1:
            for _ in range(h):
                positions[pos[0]] = x + y * width
                pos[0] += 1
                x += dbx
                y += dby
            return

        ax2 = ax // 2
        ay2 = ay // 2
        bx2 = bx // 2
        by2 = by // 2
        w2 = abs(ax2 + ay2)
        h2 = abs(bx2 + by2)

        if 2 * w > 3 * h:
            if (w2 & 1) == 1 and w > 2:
                ax2 += dax
                ay2 += day
            generate2d(x, y, ax2, ay2, bx, by)
            generate2d(x + ax2, y + ay2, ax - ax2, ay - ay2, bx, by)
        else:
            if (h2 & 1) == 1 and h > 2:
                bx2 += dbx
                by2 += dby
            generate2d(x, y, bx2, by2, ax2, ay2)
            generate2d(x + bx2, y + by2, ax, ay, bx - bx2, by - by2)
            generate2d(x + (ax - dax) + (bx2 - dbx),
                       y + (ay - day) + (by2 - dby),
                       -bx2, -by2, -(ax - ax2), -(ay - ay2))

    if width >= height:
        generate2d(0, 0, width, 0, 0, height)
    else:
        generate2d(0, 0, 0, height, width, 0)

    return positions


# ─── 算法2: 块混淆 (BlockScramble) ───
def block_scramble(pixels, width, height, key, encrypt=True,
                   x_block_count=None, y_block_count=None):
    """将图片分割为块，对块进行洗牌重排
    
    块数自动适应图片尺寸，避免padding导致的信息损失。
    最大32块，如果图片某一维小于32就用那一维的大小。
    返回 (pixels, new_width, new_height)
    """
    if x_block_count is None:
        x_block_count = min(32, width)
    if y_block_count is None:
        y_block_count = min(32, height)
    
    x_array = _md5_shuffle(x_block_count, key)
    y_array = _md5_shuffle(y_block_count, key)

    # 自动调整块大小，使块大小×块数=图片尺寸，无需padding
    new_width = width
    new_height = height
    while new_width % x_block_count != 0:
        new_width += 1
    while new_height % y_block_count != 0:
        new_height += 1

    # 如果用原始尺寸就能整除，则无需padding
    # 否则就增加几行/列进行padding（最小化padding）
    block_w = new_width // x_block_count
    block_h = new_height // y_block_count
    new_pixels = np.zeros(new_width * new_height, dtype=np.int32)

    # 将输入填充到new尺寸（pad区域用周边像素镜像填充以减少伪影）
    padded = np.zeros(new_width * new_height, dtype=np.int32)
    for y in range(new_height):
        for x in range(new_width):
            sx = min(x, width - 1)
            sy = min(y, height - 1)
            padded[x + y * new_width] = pixels[sx + sy * width]

    if encrypt:
        for i in range(new_width):
            for j in range(new_height):
                n = j
                m = (x_array[(n // block_h) % x_block_count] * block_w + i) % new_width
                m = x_array[m // block_w] * block_w + m % block_w
                n = (y_array[m // block_w % y_block_count] * block_h + n) % new_height
                n = y_array[n // block_h] * block_h + n % block_h
                new_pixels[i + j * new_width] = padded[m + n * new_width]
    else:
        for i in range(new_width):
            for j in range(new_height):
                n = j
                m = (x_array[(n // block_h) % x_block_count] * block_w + i) % new_width
                m = x_array[m // block_w] * block_w + m % block_w
                n = (y_array[m // block_w % y_block_count] * block_h + n) % new_height
                n = y_array[n // block_h] * block_h + n % block_h
                new_pixels[m + n * new_width] = padded[i + j * new_width]

    return new_pixels.tolist(), new_width, new_height


# ─── 算法3: 行像素混淆 (RowPixelScramble) ───
def row_pixel_scramble(pixels, width, height, key, encrypt=True):
    """对每行的像素进行列洗牌"""
    x_array = _md5_shuffle(width, key)
    new_pixels = np.zeros(len(pixels), dtype=np.int32)

    if encrypt:
        for i in range(width):
            for j in range(height):
                m = x_array[(x_array[j % width] + i) % width]
                new_pixels[i + j * width] = pixels[m + j * width]
    else:
        for i in range(width):
            for j in range(height):
                m = x_array[(x_array[j % width] + i) % width]
                new_pixels[m + j * width] = pixels[i + j * width]

    return new_pixels.tolist(), width, height


# ─── 算法4: 逐像素混淆 (PerPixelScramble) ───
def per_pixel_scramble(pixels, width, height, key, encrypt=True):
    """对图片的每个像素进行XY二维洗牌"""
    x_array = _md5_shuffle(width, key)
    y_array = _md5_shuffle(height, key)
    new_pixels = np.zeros(len(pixels), dtype=np.int32)

    if encrypt:
        for i in range(width):
            for j in range(height):
                m = x_array[(x_array[j % width] + i) % width]
                n = y_array[(y_array[m % height] + j) % height]
                new_pixels[i + j * width] = pixels[m + n * width]
    else:
        for i in range(width):
            for j in range(height):
                m = x_array[(x_array[j % width] + i) % width]
                n = y_array[(y_array[m % height] + j) % height]
                new_pixels[m + n * width] = pixels[i + j * width]

    return new_pixels.tolist(), width, height


# ─── 算法5: 兼容PicEncrypt 行模式 (PicEncryptRowScramble) ───
def picencrypt_row_scramble(pixels, width, height, key, encrypt=True):
    """Logistic 映射行洗牌"""
    logistic_map = _generate_logistic(key, width)
    positions = _get_sorted_positions(logistic_map)
    new_pixels = np.zeros(len(pixels), dtype=np.int32)
    offset = (height - 1) * width

    if encrypt:
        for i in range(width):
            m = positions[i]
            for j in range(offset, -1, -width):
                new_pixels[i + j] = pixels[m + j]
    else:
        for i in range(width):
            m = positions[i]
            for j in range(offset, -1, -width):
                new_pixels[m + j] = pixels[i + j]

    return new_pixels.tolist(), width, height


# ─── 算法6: 兼容PicEncrypt 行+列模式 (PicEncryptRowColumnScramble) ───
def picencrypt_rowcol_scramble(pixels, width, height, key, encrypt=True):
    """Logistic 映射行+列洗牌"""
    p = np.array(pixels, dtype=np.int32)
    tmp = p.copy()

    if encrypt:
        x = key
        # 逐行行内洗牌 (Encrypt: newPixels[pos[i]+offset] = pixels[i+offset])
        for j in range(height):
            off = j * width
            logistic_map = _generate_logistic(x, width)
            x = logistic_map[width - 1, 0]
            positions = _get_sorted_positions(logistic_map)
            for i in range(width):
                p[i + off] = tmp[positions[i] + off]

        x = key
        # 逐列列内洗牌
        for i in range(width):
            logistic_map = _generate_logistic(x, height)
            x = logistic_map[height - 1, 0]
            positions = _get_sorted_positions(logistic_map)
            for j in range(height):
                tmp[i + j * width] = p[i + positions[j] * width]

    else:
        x = key
        # Decrypt: 先列逆
        for i in range(width):
            logistic_map = _generate_logistic(x, height)
            x = logistic_map[height - 1, 0]
            positions = _get_sorted_positions(logistic_map)
            for j in range(height):
                p[i + positions[j] * width] = tmp[i + j * width]

        x = key
        # 再行逆
        for j in range(height):
            off = j * width
            logistic_map = _generate_logistic(x, width)
            x = logistic_map[width - 1, 0]
            positions = _get_sorted_positions(logistic_map)
            for i in range(width):
                tmp[positions[i] + off] = p[i + off]

    return tmp.tolist(), width, height


# ─── 算法调度表 ───
ALGORITHMS = {
    "小番茄图片混淆": {
        "fn": tomato_scramble,
        "key_type": "float",       # 浮点数
        "key_range": "(0, 1.618)",
        "desc": "使用 Gilbert 2D 空间填充曲线 + 黄金比例偏移"
    },
    "块混淆": {
        "fn": block_scramble,
        "key_type": "string",
        "key_range": "任意字符串",
        "desc": "将图片分割为 32×32 块，基于MD5密钥洗牌重排"
    },
    "行像素混淆": {
        "fn": row_pixel_scramble,
        "key_type": "string",
        "key_range": "任意字符串",
        "desc": "基于MD5密钥对每行像素进行列洗牌"
    },
    "逐像素混淆": {
        "fn": per_pixel_scramble,
        "key_type": "string",
        "key_range": "任意字符串",
        "desc": "基于MD5密钥对每个像素进行XY二维洗牌"
    },
    "兼容PicEncrypt: 行模式": {
        "fn": picencrypt_row_scramble,
        "key_type": "float",
        "key_range": "(0, 1)",
        "desc": "使用 Logistic 映射对每行进行列洗牌"
    },
    "兼容PicEncrypt: 行+列模式": {
        "fn": picencrypt_rowcol_scramble,
        "key_type": "float",
        "key_range": "(0, 1)",
        "desc": "Logistic 映射行+列二维洗牌"
    }
}

# ═══════════════════════════════════════════════
# 配置管理
# ═══════════════════════════════════════════════

def _config_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def _config_path():
    return os.path.join(_config_dir(), "config.json")


def load_config():
    try:
        if os.path.isfile(_config_path()):
            with open(_config_path(), 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            # 字段迁移
            if isinstance(cfg, dict):
                return cfg
    except Exception:
        _log_error("load_config")
    return {}


def save_config(cfg):
    try:
        with open(_config_path(), 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        _log_error("save_config")


# ═══════════════════════════════════════════════
# 图片处理（像素级）
# ═══════════════════════════════════════════════

def _pixels_to_pil(pixels, width, height, mode='RGB'):
    """将 packed int 像素列表 [0xRRGGBB, ...] 转为 PIL Image"""
    arr = np.array(pixels, dtype=np.int32)
    # 解包: 0xRRGGBB → (R, G, B)
    rs = ((arr >> 16) & 0xFF).astype(np.uint8)
    gs = ((arr >> 8) & 0xFF).astype(np.uint8)
    bs = (arr & 0xFF).astype(np.uint8)
    rgb_arr = np.stack([rs, gs, bs], axis=-1).reshape(height, width, 3)
    return PILImage.fromarray(rgb_arr, mode='RGB')


def _pil_to_pixels(img):
    """PIL Image 转为 packed int 列表 [0xRRGGBB, ...]"""
    if img.mode != 'RGB':
        img = img.convert('RGB')
    arr = np.array(img, dtype=np.int32)  # (H, W, 3)
    # 打包: (R, G, B) → 0x00RRGGBB
    packed = (arr[:, :, 0] << 16) | (arr[:, :, 1] << 8) | arr[:, :, 2]
    return packed.flatten().tolist(), img.width, img.height


def process_image_pixels(pil_img, algo_name, key, encrypt=True, in_w=None, in_h=None):
    """核心处理函数：对 PIL Image 应用指定的混淆算法
    
    返回 (pil_image_result, actual_width, actual_height)
    in_w/in_h 可选：指定当前像素数组的实际宽度/高度（用于块混淆的padded尺寸）
    """
    pixels, w, h = _pil_to_pixels(pil_img)
    # 如果调用方传入了实际尺寸（padded后），用它
    work_w, work_h = (in_w or w), (in_h or h)
    algo = ALGORITHMS[algo_name]
    result_pixels, nw, nh = algo["fn"](pixels, work_w, work_h, key, encrypt=encrypt)
    return _pixels_to_pil(result_pixels, nw, nh), nw, nh


# ═══════════════════════════════════════════════
# GUI 应用
# ═══════════════════════════════════════════════

class PicEncryptApp:
    # 配色
    BG = "#1E1E2E"
    FG = "#CDD6F4"
    CARD_BG = "#313244"
    ACCENT = "#89B4FA"
    ACCENT2 = "#A6E3A1"
    WARN = "#F9E2AF"
    ERROR = "#F38BA8"
    BORDER = "#45475A"
    TEXT_LIGHT = "#6C7086"

    FONT_FAMILY = "Microsoft YaHei"

    def __init__(self, root):
        self.root = root
        self.root.title("图片混淆")
        self.root.geometry("960x680")
        self.root.minsize(800, 600)

        # 状态
        self._original_img = None       # PIL Image - 原始加载的图
        self._processed_img = None      # PIL Image - 当前处理结果
        self._orig_size = (0, 0)        # 原始尺寸 (w, h)
        self._work_size = (0, 0)        # 当前工作尺寸 (w, h) — 块混淆可能padding
        self._processing = False
        self._tk_orig = None
        self._tk_proc = None

        # 加载配置
        cfg = load_config()
        self._last_dir = cfg.get("last_dir", "")
        self._last_algo = cfg.get("last_algo", "小番茄图片混淆")
        self._last_key = cfg.get("last_key", "")

        # 构建 UI
        self._build_ui()

        # 恢复上次设置
        if self._last_algo in ALGORITHMS:
            self.algo_var.set(self._last_algo)
        if self._last_key:
            self.key_var.set(self._last_key)
        self._on_algo_change()
        self._update_status("就绪")

        # 窗口关闭保存配置
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── UI 构建 ──

    def _build_ui(self):
        root = self.root
        root.configure(bg=self.BG)

        # 样式
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", font=(self.FONT_FAMILY, 10), padding=6)
        style.configure("TLabel", background=self.BG, foreground=self.FG,
                        font=(self.FONT_FAMILY, 10))
        style.configure("TFrame", background=self.BG)
        style.configure("TLabelframe", background=self.BG, foreground=self.FG)
        style.configure("TLabelframe.Label", background=self.BG,
                        foreground=self.FG, font=(self.FONT_FAMILY, 10, "bold"))
        style.configure("TEntry", fieldbackground=self.CARD_BG,
                        foreground=self.FG, insertcolor=self.FG)
        style.configure("TCombobox", fieldbackground=self.CARD_BG,
                        foreground=self.FG, arrowcolor=self.FG)
        style.map("TCombobox", fieldbackground=[("readonly", self.CARD_BG)])
        style.map("TButton",
                  background=[("active", self.ACCENT)],
                  foreground=[("active", self.BG)])

        # ─── 顶部栏 ───
        top = tk.Frame(root, bg=self.BG)
        top.pack(fill=tk.X, padx=12, pady=(12, 4))

        lbl_title = tk.Label(top, text="🔒 图片混淆", font=(self.FONT_FAMILY, 18, "bold"),
                             bg=self.BG, fg=self.ACCENT)
        lbl_title.pack(side=tk.LEFT)

        lbl_sub = tk.Label(top, text="6种算法 · 兼容 Android PicEncrypt",
                           font=(self.FONT_FAMILY, 10), bg=self.BG, fg=self.TEXT_LIGHT)
        lbl_sub.pack(side=tk.LEFT, padx=(12, 0), pady=(6, 0))

        # ─── 控制区 ───
        ctrl_frame = tk.Frame(root, bg=self.CARD_BG, highlightbackground=self.BORDER,
                              highlightthickness=1)
        ctrl_frame.pack(fill=tk.X, padx=12, pady=4)

        # 行1: 文件
        row1 = tk.Frame(ctrl_frame, bg=self.CARD_BG)
        row1.pack(fill=tk.X, padx=10, pady=(8, 4))

        tk.Label(row1, text="图片文件:", bg=self.CARD_BG, fg=self.FG,
                 font=(self.FONT_FAMILY, 10)).pack(side=tk.LEFT)
        self.file_var = tk.StringVar()
        self.entry_file = tk.Entry(row1, textvariable=self.file_var,
                                   bg=self.CARD_BG, fg=self.FG, insertbackground=self.FG,
                                   relief=tk.FLAT, font=(self.FONT_FAMILY, 9),
                                   highlightbackground=self.BORDER, highlightthickness=1)
        self.entry_file.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 6))
        self.btn_browse = tk.Button(row1, text="📁 浏览",
                                    bg=self.BG, fg=self.ACCENT,
                                    activebackground=self.ACCENT, activeforeground=self.BG,
                                    relief=tk.FLAT, padx=12, cursor="hand2",
                                    font=(self.FONT_FAMILY, 9),
                                    command=self._on_browse)
        self.btn_browse.pack(side=tk.LEFT)

        # 行2: 算法 + 密钥
        row2 = tk.Frame(ctrl_frame, bg=self.CARD_BG)
        row2.pack(fill=tk.X, padx=10, pady=4)

        tk.Label(row2, text="算法:", bg=self.CARD_BG, fg=self.FG,
                 font=(self.FONT_FAMILY, 10)).pack(side=tk.LEFT)
        self.algo_var = tk.StringVar(value="小番茄图片混淆")
        self.algo_combo = ttk.Combobox(row2, textvariable=self.algo_var,
                                       values=list(ALGORITHMS.keys()),
                                       state="readonly", width=28,
                                       font=(self.FONT_FAMILY, 9))
        self.algo_combo.pack(side=tk.LEFT, padx=(6, 12))
        self.algo_combo.bind("<<ComboboxSelected>>", lambda e: self._on_algo_change())

        tk.Label(row2, text="密钥:", bg=self.CARD_BG, fg=self.FG,
                 font=(self.FONT_FAMILY, 10)).pack(side=tk.LEFT)
        self.key_var = tk.StringVar()
        self.entry_key = tk.Entry(row2, textvariable=self.key_var,
                                  bg=self.BG, fg=self.FG, insertbackground=self.FG,
                                  relief=tk.FLAT, font=(self.FONT_FAMILY, 9),
                                  highlightbackground=self.BORDER, highlightthickness=1,
                                  width=30)
        self.entry_key.pack(side=tk.LEFT, padx=(6, 12))

        self.key_info_label = tk.Label(row2, text="", bg=self.CARD_BG,
                                       fg=self.WARN, font=(self.FONT_FAMILY, 8))
        self.key_info_label.pack(side=tk.LEFT)

        # 行3: 按钮
        row3 = tk.Frame(ctrl_frame, bg=self.CARD_BG)
        row3.pack(fill=tk.X, padx=10, pady=(4, 8))

        self.btn_encrypt = tk.Button(row3, text="🔐 混淆",
                                     bg="#A6E3A1", fg="#1E1E2E",
                                     activebackground="#89D88A", activeforeground="#1E1E2E",
                                     relief=tk.FLAT, padx=20, pady=4, cursor="hand2",
                                     font=(self.FONT_FAMILY, 11, "bold"),
                                     command=lambda: self._start_process(encrypt=True))
        self.btn_encrypt.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_decrypt = tk.Button(row3, text="🔓 解混淆",
                                     bg="#F9E2AF", fg="#1E1E2E",
                                     activebackground="#F2C94C", activeforeground="#1E1E2E",
                                     relief=tk.FLAT, padx=20, pady=4, cursor="hand2",
                                     font=(self.FONT_FAMILY, 11, "bold"),
                                     command=lambda: self._start_process(encrypt=False))
        self.btn_decrypt.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_save = tk.Button(row3, text="💾 保存",
                                  bg=self.ACCENT, fg=self.BG,
                                  activebackground="#74C7EC", activeforeground=self.BG,
                                  relief=tk.FLAT, padx=16, pady=4, cursor="hand2",
                                  font=(self.FONT_FAMILY, 10),
                                  command=self._on_save)
        self.btn_save.pack(side=tk.LEFT, padx=(0, 8))
        self.btn_save.config(state=tk.DISABLED)

        self.btn_reset = tk.Button(row3, text="↺ 还原",
                                   bg=self.BORDER, fg=self.FG,
                                   activebackground="#585B70", activeforeground=self.FG,
                                   relief=tk.FLAT, padx=12, pady=4, cursor="hand2",
                                   font=(self.FONT_FAMILY, 10),
                                   command=self._on_reset)
        self.btn_reset.pack(side=tk.LEFT)
        self.btn_reset.config(state=tk.DISABLED)

        # 状态
        self.status_label = tk.Label(ctrl_frame, text="", bg=self.CARD_BG,
                                     fg=self.TEXT_LIGHT, font=(self.FONT_FAMILY, 9),
                                     anchor=tk.W)
        self.status_label.pack(fill=tk.X, padx=10, pady=(0, 6))

        # ─── 图片预览区 ───
        preview_frame = tk.Frame(root, bg=self.BG)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)

        # 原始图
        orig_frame = tk.LabelFrame(preview_frame, text=" 原图 ", bg=self.CARD_BG,
                                   fg=self.FG, font=(self.FONT_FAMILY, 10, "bold"),
                                   highlightbackground=self.BORDER, highlightthickness=1,
                                   labelanchor="n")
        orig_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))

        self.orig_canvas = tk.Canvas(orig_frame, bg=self.BG,
                                     highlightthickness=0)
        self.orig_canvas.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # 处理后
        proc_frame = tk.LabelFrame(preview_frame, text=" 处理后 ", bg=self.CARD_BG,
                                   fg=self.FG, font=(self.FONT_FAMILY, 10, "bold"),
                                   highlightbackground=self.BORDER, highlightthickness=1,
                                   labelanchor="n")
        proc_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(6, 0))

        self.proc_canvas = tk.Canvas(proc_frame, bg=self.BG,
                                     highlightthickness=0)
        self.proc_canvas.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # 算法说明栏
        self.desc_label = tk.Label(root, text="", bg=self.BG, fg=self.TEXT_LIGHT,
                                   font=(self.FONT_FAMILY, 9), anchor=tk.W,
                                   wraplength=900)
        self.desc_label.pack(fill=tk.X, padx=12, pady=(0, 8))

    # ── 事件处理 ──

    def _on_algo_change(self):
        algo_name = self.algo_var.get()
        info = ALGORITHMS.get(algo_name)
        if info:
            self.key_info_label.config(text=f"密钥范围: {info['key_range']}")
            self.desc_label.config(text=f"📖 {algo_name}: {info['desc']}")

    def _on_browse(self):
        try:
            path = filedialog.askopenfilename(
                title="选择图片",
                initialdir=self._last_dir if self._last_dir else os.path.expanduser("~"),
                filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp"),
                           ("所有文件", "*.*")]
            )
            if path:
                self.file_var.set(path)
                self._last_dir = os.path.dirname(path)
                self._load_image(path)
        except Exception as e:
            _log_error("browse", e)
            messagebox.showerror("错误", f"打开文件失败:\n{e}")

    def _load_image(self, path):
        try:
            img = PILImage.open(path)
            self._original_img = img.copy()
            self._orig_size = (img.width, img.height)
            self._work_size = (img.width, img.height)  # 初始工作尺寸=原始尺寸
            self._processed_img = None
            self._show_image(self.orig_canvas, img)
            self._clear_canvas(self.proc_canvas)
            self._tk_proc = None
            self.btn_save.config(state=tk.DISABLED)
            self.btn_reset.config(state=tk.NORMAL)
            self._update_status(f"已加载: {os.path.basename(path)} ({img.width}×{img.height})")
        except Exception as e:
            _log_error("load_image", e)
            messagebox.showerror("错误", f"无法加载图片:\n{e}")

    def _show_image(self, canvas, pil_img):
        """在 Canvas 中显示 PIL Image，等比例缩放"""
        try:
            cw = canvas.winfo_width() or 400
            ch = canvas.winfo_height() or 300
            if cw < 50:
                cw = 400
            if ch < 50:
                ch = 300

            # 等比例缩放
            iw, ih = pil_img.size
            scale = min(cw / iw, ch / ih, 1.0)  # 不放大
            nw, nh = int(iw * scale), int(ih * scale)
            if nw < 1:
                nw, nh = 1, 1

            disp = pil_img.resize((nw, nh), PILImage.LANCZOS)
            tk_img = ImageTk.PhotoImage(disp)

            canvas.delete("all")
            cx, cy = cw // 2, ch // 2
            canvas.create_image(cx, cy, image=tk_img, anchor=tk.CENTER)
            # 保持引用
            if canvas == self.orig_canvas:
                self._tk_orig = tk_img
            else:
                self._tk_proc = tk_img
        except Exception as e:
            _log_error("show_image", e)

    def _clear_canvas(self, canvas):
        canvas.delete("all")
        if canvas == self.proc_canvas:
            self._tk_proc = None

    def _update_status(self, msg):
        self.status_label.config(text=msg)

    def _set_buttons_enabled(self, enabled):
        state = tk.NORMAL if enabled else tk.DISABLED
        self.btn_encrypt.config(state=state)
        self.btn_decrypt.config(state=state)
        self.btn_browse.config(state=state)
        self.algo_combo.config(state="readonly" if enabled else tk.DISABLED)
        self.entry_key.config(state=tk.NORMAL if enabled else tk.DISABLED)

    # ── 处理流程（线程安全） ──

    def _start_process(self, encrypt=True):
        if self._processing:
            return
        if self._original_img is None:
            messagebox.showinfo("提示", "请先选择一张图片")
            return

        algo_name = self.algo_var.get()
        raw_key = self.key_var.get().strip()

        # 验证密钥
        try:
            parsed_key = self._validate_key(algo_name, raw_key)
        except ValueError as e:
            messagebox.showerror("密钥错误", str(e))
            return

        self._processing = True
        self._set_buttons_enabled(False)
        action = "混淆" if encrypt else "解混淆"
        self._update_status(f"正在{action} ({algo_name})...")

        # 在后台线程中处理 — 从当前状态开始
        def task():
            try:
                # 从当前处理结果出发（或原始图）
                if self._processed_img is not None:
                    src_img = self._processed_img.copy()
                else:
                    src_img = self._original_img.copy()

                result_img, nw, nh = process_image_pixels(
                    src_img, algo_name, parsed_key, encrypt=encrypt
                )
                self.root.after(0, self._on_process_done, result_img, nw, nh, encrypt)
            except Exception as e:
                _log_error("process", e)
                self.root.after(0, self._on_process_error, str(e))

        threading.Thread(target=task, daemon=True).start()

    def _validate_key(self, algo_name, raw_key):
        """验证密钥并返回正确的类型"""
        info = ALGORITHMS[algo_name]
        if info["key_type"] == "float":
            if not raw_key:
                raise ValueError("此算法需要输入一个数值密钥（浮点数）")
            try:
                val = float(raw_key)
            except ValueError:
                raise ValueError("密钥必须是一个数值")

            if algo_name == "小番茄图片混淆":
                if not (0 < val < 1.618):
                    raise ValueError("小番茄混淆密钥范围: (0, 1.618)")
            elif algo_name in ("兼容PicEncrypt: 行模式", "兼容PicEncrypt: 行+列模式"):
                if not (0 < val < 1):
                    raise ValueError(f"{algo_name} 密钥范围: (0, 1)")
            return val
        else:
            if not raw_key:
                raise ValueError("密钥不能为空")
            return raw_key

    def _on_process_done(self, result_img, nw, nh, encrypt):
        self._processed_img = result_img
        self._work_size = (nw, nh)
        self._show_image(self.proc_canvas, result_img)
        self.btn_save.config(state=tk.NORMAL)
        action = "混淆完成" if encrypt else "解混淆完成"
        size_info = f" ({nw}×{nh})" if (nw, nh) != self._orig_size else ""
        self._update_status(f"✅ {action}{size_info}")
        self._processing = False
        self._set_buttons_enabled(True)

    def _on_process_error(self, err_msg):
        self._update_status(f"❌ 处理失败")
        self._processing = False
        self._set_buttons_enabled(True)
        messagebox.showerror("处理错误", f"图片处理失败:\n{err_msg}")

    # ── 保存 ──

    def _on_save(self):
        if self._processed_img is None:
            return
        try:
            default_name = "encrypted.png"
            if self._original_img:
                base = os.path.splitext(os.path.basename(self.file_var.get() or "image"))[0]
                default_name = f"{base}_encrypted.png"

            path = filedialog.asksaveasfilename(
                title="保存图片",
                initialdir=self._last_dir or os.path.expanduser("~"),
                initialfile=default_name,
                defaultextension=".png",
                filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg;*.jpeg"),
                           ("BMP", "*.bmp"), ("所有文件", "*.*")]
            )
            if path:
                save_img = self._processed_img
                # 如果工作尺寸不同于原始尺寸，裁剪回原始尺寸再保存
                if self._work_size != self._orig_size and self._orig_size != (0, 0):
                    save_img = save_img.crop((0, 0, self._orig_size[0], self._orig_size[1]))
                save_img.save(path)
                self._update_status(f"✅ 已保存: {os.path.basename(path)}")
        except Exception as e:
            _log_error("save", e)
            messagebox.showerror("保存失败", str(e))

    def _on_reset(self):
        """还原到原图"""
        if self._original_img is None:
            return
        self._processed_img = None
        self._clear_canvas(self.proc_canvas)
        self.btn_save.config(state=tk.DISABLED)
        self._update_status("已还原到原图")

    # ── 关闭 ──

    def _on_close(self):
        try:
            cfg = load_config()
            cfg["last_dir"] = self._last_dir
            cfg["last_algo"] = self.algo_var.get()
            cfg["last_key"] = self.key_var.get()
            save_config(cfg)
        except Exception:
            _log_error("save_on_close")
        self.root.destroy()


# ═══════════════════════════════════════════════
# 入口
# ═══════════════════════════════════════════════

def main():
    try:
        root = tk.Tk()
        root.configure(bg="#1E1E2E")
        root.withdraw()
        root.update_idletasks()
        app = PicEncryptApp(root)
        root.update_idletasks()
        root.deiconify()
        root.mainloop()
    except Exception as e:
        _log_error("main", e)
        messagebox.showerror("启动失败", f"应用程序启动时发生错误:\n{e}")


if __name__ == "__main__":
    main()
