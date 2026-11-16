import cv2
import numpy as np
from app.services.highlight_detector import detect_highlight_regions_in_image
from app.services.search_service import _cosine_similarity, _sanitize_fts_query


def _make_png_bytes(img_bgr: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".png", img_bgr)
    assert ok
    return buf.tobytes()


def test_detect_yellow_highlight_region():
    # White background (600x800) with a yellow highlight rectangle
    img = np.full((600, 800, 3), 255, dtype=np.uint8)
    # BGR for bright yellow: (0, 255, 255)
    cv2.rectangle(img, (100, 150), (500, 210), (0, 255, 255), -1)
    regions = detect_highlight_regions_in_image(_make_png_bytes(img))
    assert len(regions) >= 1
    assert any(r.color == "yellow" for r in regions)


def test_skip_blank_page_without_highlights():
    img = np.full((600, 800, 3), 255, dtype=np.uint8)
    # Draw black text-like lines (no highlight color)
    cv2.rectangle(img, (80, 100), (400, 115), (0, 0, 0), -1)
    regions = detect_highlight_regions_in_image(_make_png_bytes(img))
    assert regions == []


def test_cosine_similarity_and_fts_sanitize():
    v1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    v2 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    v3 = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    assert abs(_cosine_similarity(v1, v2) - 1.0) < 1e-5
    assert abs(_cosine_similarity(v1, v3) - 0.0) < 1e-5
    assert _sanitize_fts_query("đạo hàm bậc hai") == '"đạo" OR "hàm" OR "bậc" OR "hai"'
