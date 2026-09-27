"""
src/vision/hand_tracker.py
Wrapper mở webcam bằng OpenCV và chạy MediaPipe Tasks HandLandmarker ở chế độ
VIDEO (mượt theo thời gian thực, khác với "Image mode" chỉ xử lý ảnh tĩnh).

Module này CHỈ làm 1 việc: lấy 21 điểm landmark thô ra mỗi frame, cùng với
khung hình BGR gốc (để hiển thị lên camera panel). Không tính toán khoảng
cách, không xử lý cử chỉ - việc đó thuộc về coordinate_mapper.py và
gesture_detector.py.
"""
import time

import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    HandLandmarker,
    HandLandmarkerOptions,
    RunningMode,
)

from config import settings
from src.utils.logger import get_logger

logger = get_logger()


class HandTracker:
    """Mở webcam + model HandLandmarker. Gọi read() mỗi frame để lấy
    (landmarks, frame_bgr). landmarks = None nếu không thấy tay trong khung hình.
    """

    def __init__(self, cam_index=None, model_path=None):
        cam_index = settings.CAM_INDEX if cam_index is None else cam_index
        model_path = settings.HAND_MODEL_PATH if model_path is None else model_path

        self.cap = cv2.VideoCapture(cam_index)
        if not self.cap.isOpened():
            raise RuntimeError(
                f"Khong mo duoc webcam (CAM_INDEX={cam_index}). "
                f"Kiem tra webcam co dang bi ung dung khac chiem dung khong, "
                f"hoac doi CAM_INDEX trong config/settings.py."
            )
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.FRAME_W)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.FRAME_H)

        try:
            base_options = BaseOptions(model_asset_path=model_path)
            options = HandLandmarkerOptions(
                base_options=base_options,
                running_mode=RunningMode.VIDEO,
                num_hands=settings.MAX_NUM_HANDS,
                min_hand_detection_confidence=settings.MIN_DETECTION_CONFIDENCE,
                min_hand_presence_confidence=settings.MIN_DETECTION_CONFIDENCE,
                min_tracking_confidence=settings.MIN_TRACKING_CONFIDENCE,
            )
            self.detector = HandLandmarker.create_from_options(options)
        except Exception as e:
            self.cap.release()
            raise RuntimeError(
                f"Khong load duoc model '{model_path}'. Hay tai file "
                f"hand_landmarker.task tu MediaPipe va dat o dung duong dan "
                f"(mac dinh: goc thu muc du an). Loi goc: {e}"
            )

        self._start_time = time.time()
        logger.info("HandTracker: webcam + HandLandmarker da san sang.")

    def read(self):
        """Đọc 1 frame webcam, chạy detect, trả về (landmarks, frame_bgr).
        landmarks: list 21 điểm (có .x, .y, .z chuẩn hoá 0..1) của BÀN TAY ĐẦU
        TIÊN tìm thấy, hoặc None nếu không thấy tay hoặc đọc webcam lỗi.
        frame_bgr: khung hình OpenCV gốc (đã lật gương nếu MIRROR_CAMERA=True),
        dùng để hiển thị lên camera panel; None nếu đọc webcam lỗi.
        """
        ok, frame = self.cap.read()
        if not ok:
            return None, None

        if settings.MIRROR_CAMERA:
            frame = cv2.flip(frame, 1)

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        timestamp_ms = int((time.time() - self._start_time) * 1000)

        result = self.detector.detect_for_video(mp_image, timestamp_ms)

        landmarks = None
        if result.hand_landmarks:
            landmarks = result.hand_landmarks[0]  # chỉ lấy tay đầu tiên

        return landmarks, frame

    def close(self):
        if self.cap is not None:
            self.cap.release()
        if hasattr(self, "detector"):
            self.detector.close()
        logger.info("HandTracker: da giai phong webcam.")