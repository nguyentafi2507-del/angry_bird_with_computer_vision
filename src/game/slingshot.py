"""
src/game/slingshot.py
Cầu nối giữa tọa độ điều khiển (CHUỘT hoặc TAY qua webcam) và điểm sinh lực
phóng chim.

Thiết kế theo interface InputProvider: MouseInputProvider (chuột) và
HandInputProvider (tay, dùng src/vision/) đều implement chung 1 interface,
nên Slingshot và game_engine.py không cần biết nguồn điều khiển là gì.
"""
import pygame

from config import settings
from src.utils import vector2d as v2
from src.game import physics


class InputProvider:
    """Interface trừu tượng cho nguồn điều khiển ná (chuột / tay)."""

    def get_control_point(self):
        """Trả về (x, y) toạ độ điều khiển trong hệ Pygame của viewport game."""
        raise NotImplementedError

    def is_grabbing(self):
        """True nếu người chơi đang 'nắm' (chụm ngón tay hoặc giữ chuột)."""
        raise NotImplementedError

    def just_released(self):
        """True đúng 1 frame khi vừa thả tay/chuột (dùng để bắn)."""
        raise NotImplementedError


class MouseInputProvider(InputProvider):
    """Điều khiển tạm bằng chuột: giữ trái chuột trong bán kính anchor để nắm,
    kéo ra xa rồi thả chuột để bắn. Chỉ nhận input khi con trỏ nằm trong
    viewport game (x < settings.FRAME_W), để không xung đột với panel camera.
    """

    def __init__(self):
        self._was_down = False
        self._released_this_frame = False

    def update(self, events):
        self._released_this_frame = False
        for event in events:
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self._was_down:
                    self._released_this_frame = True
                self._was_down = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()
                if mx < settings.FRAME_W:
                    self._was_down = True

    def get_control_point(self):
        mx, my = pygame.mouse.get_pos()
        return (min(mx, settings.FRAME_W), my)

    def is_grabbing(self):
        return self._was_down

    def just_released(self):
        return self._released_this_frame


class Slingshot:
    """Quản lý trạng thái kéo-thả và tính vận tốc bắn cho 1 chim đang DOCKED."""

    STATE_IDLE = "IDLE"
    STATE_GRABBED = "GRABBED"

    def __init__(self, input_provider):
        self.input_provider = input_provider
        self.state = self.STATE_IDLE
        self.anchor = (settings.ANCHOR_X, settings.ANCHOR_Y)
        self.current_pull_screen = self.anchor  # vị trí kéo hiện tại (toạ độ pygame)

    def update_input(self, events):
        """Đọc trạng thái mới nhất từ nguồn điều khiển (chuột hoặc webcam).
        Gọi mỗi frame, TÁCH RIÊNG khỏi apply_pull() để camera/hand-tracking vẫn
        chạy mượt kể cả khi chim đang bay (không có chim DOCKED để kéo)."""
        if hasattr(self.input_provider, "update"):
            self.input_provider.update(events)

    def apply_pull(self, bird):
        """bird: đối tượng Bird đang ở trạng thái DOCKED. Trả về velocity (vx, vy)
        theo hệ pymunk nếu vừa bắn, ngược lại trả về None.
        Giả định update_input() đã được gọi trước đó trong cùng frame này."""
        control_point = self.input_provider.get_control_point()
        grabbing = self.input_provider.is_grabbing()

        if self.state == self.STATE_IDLE:
            if grabbing and v2.distance(control_point, self.anchor) <= settings.GRAB_ENTER_THRESHOLD * 2.5:
                self.state = self.STATE_GRABBED

        if self.state == self.STATE_GRABBED:
            raw_pull_vec = v2.sub(control_point, self.anchor)
            pull_vec, pull_distance = physics.compute_pull(raw_pull_vec)
            drag_pos_screen = (self.anchor[0] + pull_vec[0], self.anchor[1] + pull_vec[1])
            self.current_pull_screen = drag_pos_screen

            bird.dock_at(self._screen_to_pymunk_anchor(drag_pos_screen))

            released = self.input_provider.just_released()
            if released or not grabbing:
                self.state = self.STATE_IDLE
                self.current_pull_screen = self.anchor
                if not physics.is_pull_valid(pull_distance):
                    return None  # kéo quá ít -> không bắn
                velocity_screen = physics.compute_launch_velocity_screen(pull_vec)
                velocity = physics.screen_velocity_to_pymunk(*velocity_screen)
                return velocity

        return None

    def _screen_to_pymunk_anchor(self, screen_pos):
        """Chuyển vị trí kéo (toạ độ pygame) thành vị trí pymunk cho chim,
        giữ nguyên độ lệch so với anchor nhưng đảo trục Y."""
        dx = screen_pos[0] - self.anchor[0]
        dy = screen_pos[1] - self.anchor[1]
        anchor_pymunk = (settings.ANCHOR_X, settings.FRAME_H - settings.ANCHOR_Y)
        return (anchor_pymunk[0] + dx, anchor_pymunk[1] - dy)

    def get_pull_line(self):
        """Trả về (anchor_screen, current_pull_screen) để vẽ dây ná + đường kéo."""
        return self.anchor, self.current_pull_screen

    def is_pulling(self):
        return self.state == self.STATE_GRABBED


class HandInputProvider(InputProvider):
    """Điều khiển bằng CỬ CHỈ TAY qua webcam (MediaPipe HandLandmarker).

    Ghép nối: HandTracker (đọc webcam + landmark thô) -> coordinate_mapper
    (tính điểm điều khiển + khoảng cách 2 ngón) -> GestureDetector (máy trạng
    thái nắm/thả có khử rung). Implement đúng interface InputProvider nên
    Slingshot không cần biết gì về webcam/MediaPipe.

    Khởi tạo có thể ném lỗi (RuntimeError) nếu không mở được webcam hoặc
    không load được model - game_engine.py bắt lỗi này để tự động fallback
    về MouseInputProvider.
    """

    def __init__(self):
        # Import trễ (lazy import) để mouse-only mode không bắt buộc phải cài
        # mediapipe/opencv nếu người dùng chưa cần dùng Computer Vision.
        from src.vision.hand_tracker import HandTracker
        from src.vision.gesture_detector import GestureDetector

        self.tracker = HandTracker()
        self.gesture = GestureDetector()

        self._control_point = (settings.ANCHOR_X, settings.ANCHOR_Y)
        self._finger_tips = None  # ((thumb_x,thumb_y),(index_x,index_y)) - toạ độ màn hình game
        self._last_frame = None
        self._last_landmarks = None

    def update(self, events):
        from src.vision import coordinate_mapper as cm

        landmarks, frame = self.tracker.read()
        self._last_frame = frame
        self._last_landmarks = landmarks

        if landmarks is not None:
            point = cm.compute_control_point(landmarks, settings.FRAME_W, settings.FRAME_H)
            if point is not None:
                self._control_point = point
            self._finger_tips = cm.get_finger_tips(landmarks, settings.FRAME_W, settings.FRAME_H)
            distance = cm.pinch_distance_px(landmarks, settings.FRAME_W, settings.FRAME_H)
        else:
            self._finger_tips = None
            distance = None

        self.gesture.update(distance)

    def get_control_point(self):
        return self._control_point

    def is_grabbing(self):
        return self.gesture.grabbing

    def just_released(self):
        return self.gesture.just_released_flag

    def get_camera_frame(self):
        """Khung hình webcam gốc (BGR, đã lật gương) - dùng cho camera_overlay."""
        return self._last_frame

    def get_hand_landmarks(self):
        """21 điểm landmark thô của frame gần nhất - dùng để vẽ khung xương tay."""
        return self._last_landmarks

    def get_finger_points(self):
        """((thumb_x,thumb_y),(index_x,index_y)) theo toạ độ màn hình GAME
        (settings.FRAME_W x FRAME_H), hoặc None nếu không thấy tay frame này.
        Dùng để vẽ 2 chấm ngón tay trực tiếp lên khung game."""
        return self._finger_tips

    def close(self):
        self.tracker.close()