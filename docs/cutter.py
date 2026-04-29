# vibe coding
"""
上海地铁线路色块提取器
功能：从拍摄的照片中检测任意四边形色块，透视变换还原为标准长方形
方法：HSV 颜色分割
"""

import cv2
import numpy as np
import os
import glob


# ──────────────────────────────────────────
# 配置参数（可按需调整）
# ──────────────────────────────────────────
INPUT_DIR = "source"     # 输入图片目录
OUTPUT_DIR = "selected"  # 输出目录
# 输出尺寸自动根据检测到的四边形实际大小计算，无需手动指定

# 轮廓面积过滤（太小/太大的忽略）
MIN_AREA = 2000
MAX_AREA = 500_000

# HSV 通用高饱和度过滤阈值（不依赖任何具体颜色）
# 饱和度阈值：调低可检测浅色色块，调高可减少背景干扰
HSV_S_MIN = 60
# 亮度范围（排除纯黑暗部）
HSV_V_MIN = 40
HSV_V_MAX = 255


# ──────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────

def hsv_mask(image: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    通用 HSV 颜色分割。
    返回 (mask_filled, mask_raw)：
      mask_filled —— 经过闭运算+填充的完整色块掩码（用于检测外轮廓）
      mask_raw    —— 仅 inRange 轻微处理的原始掩码（用于检测嵌套小色块）
    """
    # 1. 高斯模糊去噪
    blurred = cv2.GaussianBlur(image, (7, 7), 0)

    # 2. 转 HSV，按饱和度 + 亮度过滤
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    lower = np.array([  0, HSV_S_MIN, HSV_V_MIN])
    upper = np.array([179, 255,       HSV_V_MAX])
    raw = cv2.inRange(hsv, lower, upper)

    # raw：轻度开运算去噪点即可，保留细节/嵌套结构
    k_small = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    mask_raw = cv2.morphologyEx(raw, cv2.MORPH_OPEN, k_small)

    # filled：大核闭运算 → 轮廓填充 → 开运算，得到完整实心色块
    k_close = cv2.getStructuringElement(cv2.MORPH_RECT, (31, 31))
    filled = cv2.morphologyEx(raw, cv2.MORPH_CLOSE, k_close)
    contours, _ = cv2.findContours(filled, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    mask_filled = np.zeros_like(raw)
    cv2.drawContours(mask_filled, contours, -1, 255, cv2.FILLED)
    k_open = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    mask_filled = cv2.morphologyEx(mask_filled, cv2.MORPH_OPEN, k_open)

    return mask_filled, mask_raw


def order_points(pts: np.ndarray) -> np.ndarray:
    """
    将四边形四个顶点按质心角度排列为 [左上, 右上, 右下, 左下]。
    按角度排列可保证多边形无自相交，适用于任意朝向的色块。
    """
    # 1. 按质心角度排成顺时针序列（0°=右, 顺时针增大）
    center = pts.mean(axis=0)
    angles = np.arctan2(pts[:, 1] - center[1], pts[:, 0] - center[0])
    cw = pts[np.argsort(angles)]  # 按角度从小（左）到大排列

    # 2. 在顺时针序列里找 x+y 最小的点作为「左上」起点
    start = np.argmin(cw.sum(axis=1))
    cw = np.roll(cw, -start, axis=0)  # 旋转到以左上为首

    # 3. 返回 [左上, 右上, 右下, 左下]
    return cw.astype(np.float32)


def four_point_transform(image: np.ndarray, pts: np.ndarray) -> np.ndarray:
    """
    透视变换：将任意四边形映射到标准长方形。
    输出尺寸根据四边形实际边长自动计算，尽量保留原始大小。
    """
    src = order_points(pts)  # [左上, 右上, 右下, 左下]

    # 计算上、下边的宽度，取较大值作为输出宽
    w_top    = np.linalg.norm(src[1] - src[0])
    w_bottom = np.linalg.norm(src[2] - src[3])
    out_w = max(int(round(w_top)), int(round(w_bottom)))

    # 计算左、右边的高度，取较大值作为输出高
    h_left  = np.linalg.norm(src[3] - src[0])
    h_right = np.linalg.norm(src[2] - src[1])
    out_h = max(int(round(h_left)), int(round(h_right)))

    # 至少 1 像素，防止极端情况
    out_w = max(out_w, 1)
    out_h = max(out_h, 1)

    dst = np.array([
        [0,         0        ],
        [out_w - 1, 0        ],
        [out_w - 1, out_h - 1],
        [0,         out_h - 1],
    ], dtype=np.float32)

    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(image, M, (out_w, out_h),
                                 flags=cv2.INTER_LANCZOS4)
    return warped




def _merge_to_quad(pts: np.ndarray) -> np.ndarray:
    """
    将多于 4 个顶点的凸多边形，反复合并距离最近的相邻两点，直到剩 4 个顶点。
    用于 approxPolyDP 跳过 4 直接到 3 时的兜底处理。
    """
    pts = pts.copy()
    while len(pts) > 4:
        n = len(pts)
        dists = [np.linalg.norm(pts[i] - pts[(i + 1) % n]) for i in range(n)]
        i = int(np.argmin(dists))
        j = (i + 1) % n
        mid = (pts[i] + pts[j]) / 2
        # 删掉 j，把 mid 写到 i
        pts = np.delete(pts, j, axis=0)
        pts[i % len(pts)] = mid
    return pts


def approx_to_quad(contour: np.ndarray) -> np.ndarray | None:
    """
    将轮廓自适应近似为恰好 4 个顶点的凸四边形。
    - 逐步放宽 epsilon，优先找到恰好 4 顶点的结果。
    - 若 epsilon 跳过了 4（>4 直接变 <4），用 _merge_to_quad 强制降到 4。
    """
    hull = cv2.convexHull(contour)
    peri = cv2.arcLength(hull, True)

    best_gt4 = None  # 记录顶点数 > 4 的最后一次结果

    for ratio in np.arange(0.01, 0.35, 0.01):
        approx = cv2.approxPolyDP(hull, ratio * peri, True)
        n = len(approx)
        if n == 4:
            return approx.reshape(4, 2).astype(np.float32)
        if n > 4:
            best_gt4 = approx.reshape(-1, 2).astype(np.float32)
        else:  # n < 4：跳过了 4，用上次 >4 的结果合并
            break

    if best_gt4 is not None:
        return _merge_to_quad(best_gt4)

    return None


def quad_iou(a: np.ndarray, b: np.ndarray) -> float:
    """
    用外接轴对齐矩形近似计算两个四边形的 IoU，用于去重。
    """
    ax1, ay1 = a.min(axis=0)
    ax2, ay2 = a.max(axis=0)
    bx1, by1 = b.min(axis=0)
    bx2, by2 = b.max(axis=0)
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    if inter == 0:
        return 0.0
    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    return inter / (area_a + area_b - inter)


def find_quads(mask: np.ndarray) -> list[np.ndarray]:
    """
    在单张掩码中寻找所有层级的四边形候选（含嵌套）。
    使用 RETR_LIST 获取全部轮廓，不过滤宽高比。
    """
    contours, _ = cv2.findContours(
        mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
    )
    quads = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if not (MIN_AREA <= area <= MAX_AREA):
            continue
        pts = approx_to_quad(cnt)
        if pts is not None:
            quads.append(pts)
    return quads


def merge_quads(lists: list[list[np.ndarray]], iou_thresh: float = 0.85) -> list[np.ndarray]:
    """
    合并多路 find_quads 结果，用 IoU 去除高度重叠的重复候选。
    """
    all_quads: list[np.ndarray] = []
    for q_list in lists:
        all_quads.extend(q_list)

    kept: list[np.ndarray] = []
    for q in all_quads:
        duplicate = any(quad_iou(q, k) > iou_thresh for k in kept)
        if not duplicate:
            kept.append(q)
    return kept


# ──────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────

def process_image(img_path: str, out_dir: str) -> int:
    """
    处理单张图片，返回找到的色块数量
    """
    image = cv2.imread(img_path)
    if image is None:
        print(f"  [跳过] 无法读取: {img_path}")
        return 0

    # 缩放至合理尺寸（防止巨图太慢），保持比例
    h, w = image.shape[:2]
    max_dim = 1920
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        image = cv2.resize(image, (int(w * scale), int(h * scale)),
                           interpolation=cv2.INTER_AREA)

    mask_filled, mask_raw = hsv_mask(image)

    # 两路检测：filled 掩码检外轮廓，raw 掩码检嵌套小色块
    quads = merge_quads([
        find_quads(mask_filled),
        find_quads(mask_raw),
    ])

    base_name = os.path.splitext(os.path.basename(img_path))[0]
    count = 0

    for i, pts in enumerate(quads):
        warped = four_point_transform(image, pts)
        out_path = os.path.join(out_dir, f"{base_name}_rect_{i:02d}.png")
        cv2.imwrite(out_path, warped)
        count += 1
        print(f"  [{i}] 保存: {out_path}")

    # 调试图1：两张掩码并排（filled | raw）
    mask_both = np.hstack([
        cv2.cvtColor(mask_filled, cv2.COLOR_GRAY2BGR),
        cv2.cvtColor(mask_raw,    cv2.COLOR_GRAY2BGR),
    ])
    cv2.imwrite(os.path.join(out_dir, f"{base_name}_mask.jpg"), mask_both)

    # 调试图2：原图叠加所有候选轮廓 + 编号
    debug = image.copy()
    for i, pts in enumerate(quads):
        ordered = order_points(pts).astype(np.int32)
        # 用不同颜色区分候选（循环 8 种颜色）
        colors = [
            (0, 255, 0), (0, 128, 255), (255, 0, 0), (0, 255, 255),
            (255, 0, 255), (255, 255, 0), (128, 255, 128), (255, 128, 0),
        ]
        color = colors[i % len(colors)]
        cv2.polylines(debug, [ordered], True, color, 2)
        # 在左上角附近标注编号
        label_pt = tuple(ordered[np.argmin(ordered.sum(axis=1))].tolist())
        cv2.putText(debug, str(i), label_pt,
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2, cv2.LINE_AA)
    cv2.imwrite(os.path.join(out_dir, f"{base_name}_debug.jpg"), debug)

    return count


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    patterns = ["*.jpg", "*.jpeg", "*.png", "*.bmp", "*.webp"]
    img_files = []
    for pat in patterns:
        img_files.extend(glob.glob(os.path.join(INPUT_DIR, pat)))
        img_files.extend(glob.glob(os.path.join(INPUT_DIR, pat.upper())))

    if not img_files:
        print(f"[错误] {INPUT_DIR}/ 目录下没有找到图片！")
        return

    total = 0
    for path in sorted(set(img_files)):
        print(f"\n处理: {path}")
        total += process_image(path, OUTPUT_DIR)

    print(f"\n完成，共提取色块: {total} 个，结果保存在 {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
