import cv2
import numpy as np
from PIL import Image, ImageOps
from pathlib import Path


def fix_orientation(image_path: str | Path) -> np.ndarray:
    """
    Reads an image file, corrects its orientation based on EXIF metadata,
    and returns a BGR NumPy array (OpenCV format).
    """
    pil_img = Image.open(image_path)
    pil_img = ImageOps.exif_transpose(pil_img)
    
    if pil_img.mode != "RGB":
        pil_img = pil_img.convert("RGB")
        
    img_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    return img_bgr


def order_points(pts: np.ndarray) -> np.ndarray:
    """
    Orders 4 coordinates in top-left, top-right, bottom-right, bottom-left order.
    """
    rect = np.zeros((4, 2), dtype="float32")

    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]  # Top-Left
    rect[2] = pts[np.argmax(s)]  # Bottom-Right

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # Top-Right
    rect[3] = pts[np.argmax(diff)]  # Bottom-Left

    return rect


def auto_crop_paper(image: np.ndarray) -> np.ndarray:
    """
    Detects paper contour and applies 4-point perspective transform.
    Falls back to original image if paper contour is not clearly detected.
    """
    orig_h, orig_w = image.shape[:2]

    # Resize temporarily for faster contour processing
    ratio = orig_h / 500.0
    small_h, small_w = int(orig_h / ratio), int(orig_w / ratio)
    small_img = cv2.resize(image, (small_w, small_h))

    # Pre-processing: Grayscale + Gaussian Blur + Canny Edge Detection
    gray = cv2.cvtColor(small_img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 75, 200)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    edges = cv2.dilate(edges, kernel, iterations=1)

    contours, _ = cv2.findContours(edges.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

    paper_cnt = None
    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)

        if len(approx) == 4 and cv2.contourArea(c) > (small_h * small_w * 0.20):
            paper_cnt = approx
            break

    if paper_cnt is not None:
        pts = paper_cnt.reshape(4, 2) * ratio
        rect = order_points(pts)
        (tl, tr, br, bl) = rect

        width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        max_width = max(int(width_a), int(width_b))

        height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        max_height = max(int(height_a), int(height_b))

        dst = np.array([
            [0, 0],
            [max_width - 1, 0],
            [max_width - 1, max_height - 1],
            [0, max_height - 1]
        ], dtype="float32")

        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, M, (max_width, max_height))
        return warped

    # Fallback Strategy: Return original image without aggressive crop
    return image


def enhance_scanner_effect(image: np.ndarray) -> np.ndarray:
    """
    Applies experimental scanner enhancement filter (Grayscale + Adaptive Threshold).
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    dilated = cv2.dilate(gray, np.ones((7, 7), np.uint8))
    bg_img = cv2.medianBlur(dilated, 21)
    diff_img = 255 - cv2.absdiff(gray, bg_img)
    norm_img = cv2.normalize(diff_img, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)

    scanned = cv2.adaptiveThreshold(
        norm_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 15
    )
    return scanned


def process_image_pipeline(input_path: str | Path, output_path: str | Path, use_scanner_effect: bool = False) -> str:
    """
    Full image processing pipeline:
    1. EXIF Orientation Fix
    2. Auto Crop / Perspective Transform
    3. Scanner Filter (Optional - BETA)
    4. Save Output.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Step 1: Fix Orientation
    img = fix_orientation(input_path)

    # Step 2: Auto Crop / Perspective Transform
    cropped = auto_crop_paper(img)

    # Step 3: Apply Scanner Filter if requested (BETA option)
    if use_scanner_effect:
        final_img = enhance_scanner_effect(cropped)
    else:
        final_img = cropped

    # Step 4: Save to file
    cv2.imwrite(str(output_path), final_img)
    return str(output_path)
