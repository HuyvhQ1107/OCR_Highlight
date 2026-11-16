from dataclasses import dataclass
from pathlib import Path
import cv2
import fitz  # PyMuPDF
import numpy as np


# HSV color ranges for common highlighter markers (OpenCV H: 0-179, S: 0-255, V: 0-255)
HIGHLIGHT_HSV_RANGES: dict[str, list[tuple[tuple[int, int, int], tuple[int, int, int]]]] = {
    "yellow": [((18, 55, 120), (38, 255, 255))],
    "green": [((39, 45, 100), (85, 255, 255))],
    "blue": [((86, 45, 100), (130, 255, 255))],
    "pink": [((131, 40, 110), (179, 255, 255)), ((0, 50, 120), (10, 255, 255))],
    "orange": [((11, 60, 120), (17, 255, 255))],
}


@dataclass
class DetectedRegion:
    color: str
    bbox: dict[str, float]  # normalized {x, y, width, height}


@dataclass
class PageRenderResult:
    page_number: int
    image_bytes: bytes
    page_text_hint: str
    detected_regions: list[DetectedRegion]

    @property
    def candidate_colors(self) -> list[str]:
        return sorted({r.color for r in self.detected_regions})


def inspect_pdf_metadata(pdf_path: Path) -> tuple[int, bool]:
    """Return (total_pages, is_scanned_pdf) or raise ValueError if encrypted/corrupted."""
    try:
        doc = fitz.open(pdf_path)
    except Exception as exc:
        raise ValueError("Tệp PDF bị hỏng hoặc không thể đọc.") from exc

    try:
        if doc.is_encrypted:
            raise ValueError("Tệp PDF đang được bảo vệ bằng mật khẩu. Vui lòng mở khóa trước khi tải lên.")
        total_pages = len(doc)
        if total_pages == 0:
            raise ValueError("Tệp PDF không có trang nào.")
        # Heuristic: check up to first 5 pages for embedded text layer
        sample_pages = min(total_pages, 5)
        text_chars = sum(len(doc[i].get_text("text").strip()) for i in range(sample_pages))
        is_scanned = text_chars < (sample_pages * 30)
        return total_pages, is_scanned
    finally:
        doc.close()


def detect_highlight_regions_in_image(image_bytes: bytes, min_area_ratio: float = 0.0005) -> list[DetectedRegion]:
    """Detect colored highlight regions in an image using OpenCV HSV thresholding."""
    np_arr = np.frombuffer(image_bytes, dtype=np.uint8)
    bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if bgr is None:
        return []

    height, width = bgr.shape[:2]
    total_area = float(height * width)
    min_area = max(120.0, total_area * min_area_ratio)

    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 5))
    regions: list[DetectedRegion] = []

    for color_name, ranges in HIGHLIGHT_HSV_RANGES.items():
        mask = np.zeros((height, width), dtype=np.uint8)
        for lower, upper in ranges:
            mask = cv2.bitwise_or(
                mask, cv2.inRange(hsv, np.array(lower, dtype=np.uint8), np.array(upper, dtype=np.uint8))
            )
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_area:
                continue
            x, y, w, h = cv2.boundingRect(cnt)
            regions.append(
                DetectedRegion(
                    color=color_name,
                    bbox={
                        "x": round(x / width, 4),
                        "y": round(y / height, 4),
                        "width": round(w / width, 4),
                        "height": round(h / height, 4),
                    },
                )
            )
    return regions


def render_pdf_pages_with_highlights(pdf_path: Path, dpi: int = 150) -> list[PageRenderResult]:
    """Render PDF pages at >=150 DPI and detect highlight regions on each page."""
    results: list[PageRenderResult] = []
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)

    doc = fitz.open(pdf_path)
    try:
        for idx in range(len(doc)):
            page = doc[idx]
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            img_bytes = pix.tobytes("png")
            regions = detect_highlight_regions_in_image(img_bytes)

            # Also check native PDF highlight annotations if present
            annots = list(page.annots() or [])
            for annot in annots:
                if annot.type[0] == 8:  # PDF Highlight annotation
                    rect = annot.rect
                    pw = page.rect.width or 1.0
                    ph = page.rect.height or 1.0
                    regions.append(
                        DetectedRegion(
                            color="yellow",
                            bbox={
                                "x": round(rect.x0 / pw, 4),
                                "y": round(rect.y0 / ph, 4),
                                "width": round((rect.x1 - rect.x0) / pw, 4),
                                "height": round((rect.y1 - rect.y0) / ph, 4),
                            },
                        )
                    )

            results.append(
                PageRenderResult(
                    page_number=idx + 1,
                    image_bytes=img_bytes,
                    page_text_hint=page.get_text("text").strip(),
                    detected_regions=regions,
                )
            )
    finally:
        doc.close()
    return results
