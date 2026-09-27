"""
src/vision/gesture_detector.py
Nhận diện trạng thái Nắm / Thả tay với thuật toán khử rung (hysteresis 2 ngưỡng).

Vì sao cần 2 ngưỡng thay vì 1:
Nếu chỉ dùng 1 ngưỡng, khi khoảng cách 2 ngón tay dao động ngay sát ngưỡng đó
(do tay run nhẹ), trạng thái sẽ nhấp nháy nắm-thả-nắm-thả liên tục mỗi frame.
Dùng 2 ngưỡng (enter < exit) tạo ra một "vùng đệm": phải chụm đủ CHẶT
(< enter_threshold) mới coi là bắt đầu nắm, và phải mở đủ RỘNG
(> exit_threshold) mới coi là thả - ở khoảng giữa 2 ngưỡng, trạng thái cũ
được giữ nguyên.
"""
from config import settings


class GestureDetector:
    def __init__(self, enter_threshold=None, exit_threshold=None):
        self.enter_threshold = (
            settings.GRAB_ENTER_THRESHOLD if enter_threshold is None else enter_threshold
        )
        self.exit_threshold = (
            settings.GRAB_EXIT_THRESHOLD if exit_threshold is None else exit_threshold
        )
        self.grabbing = False
        self.just_released_flag = False

    def update(self, pinch_distance_px):
        """Gọi 1 lần mỗi frame với khoảng cách 2 ngón (px), hoặc None nếu
        không thấy tay trong khung hình. Cập nhật self.grabbing và
        self.just_released_flag (True đúng 1 frame khi vừa chuyển nắm -> thả)."""
        was_grabbing = self.grabbing

        if pinch_distance_px is None:
            # Mất dấu tay -> coi như thả ra để tránh chim bị "kẹt" trên ná mãi
            self.grabbing = False
        elif not self.grabbing and pinch_distance_px <= self.enter_threshold:
            self.grabbing = True
        elif self.grabbing and pinch_distance_px >= self.exit_threshold:
            self.grabbing = False
        # else: nằm giữa 2 ngưỡng -> giữ nguyên trạng thái cũ

        self.just_released_flag = was_grabbing and not self.grabbing
        return self.grabbing

    def reset(self):
        self.grabbing = False
        self.just_released_flag = False