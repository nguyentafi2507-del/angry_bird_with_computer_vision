"""
src/ui/camera_overlay.py
Panel camera bên phải màn hình (chia 2 màn hình: Game | Camera).

Nếu có frame webcam thật (từ HandInputProvider) thì hiển thị webcam + vẽ
khung xương 21 điểm landmark lên trên. Nếu không (đang dùng MouseInputProvider,
hoặc webcam/CV lỗi) thì hiển thị placeholder như cũ.
"""
import cv2
import numpy as np
import pygame

from config import settings

# Các cặp điểm nối xương bàn tay theo chuẩn MediaPipe Hand (21 landmark)
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),          # ngón cái
    (0, 5), (5, 6), (6, 7), (7, 8),          # ngón trỏ
    (5, 9), (9, 10), (10, 11), (11, 12),     # ngón giữa
    (9, 13), (13, 14), (14, 15), (15, 16),   # ngón áp út
    (13, 17), (17, 18), (18, 19), (19, 20),  # ngón út
    (0, 17),                                 # cổ tay - gốc ngón út
]


class CameraOverlay:
    def __init__(self):
        pygame.font.init()
        self.font = pygame.font.SysFont(settings.FONT_NAME, 20)
        self.font_small = pygame.font.SysFont(settings.FONT_NAME, 15)
        self._pulse_t = 0.0

    def render(self, panel_surface, dt=0.0, frame=None, hand_landmarks=None):
        """frame: numpy array BGR (từ OpenCV) hoặc None.
        hand_landmarks: list 21 điểm chuẩn hoá (0..1) từ MediaPipe hoặc None.
        """
        if frame is not None:
            self._draw_camera_frame(panel_surface, frame, hand_landmarks)
        else:
            panel_surface.fill(settings.COLOR_PANEL_BG)
            self._draw_placeholder(panel_surface, dt)

    # ------------------------------------------------------------------
    # Webcam thật + khung xương tay
    # ------------------------------------------------------------------
    def _draw_camera_frame(self, panel_surface, frame_bgr, hand_landmarks):
        panel_w, panel_h = panel_surface.get_size()
        frame_h, frame_w = frame_bgr.shape[:2]

        # Vẽ khung xương tay trực tiếp lên frame OpenCV (toạ độ theo frame gốc)
        if hand_landmarks:
            self._draw_hand_skeleton(frame_bgr, hand_landmarks, frame_w, frame_h)

        # Resize frame cho vừa khung panel, giữ tỉ lệ, căn giữa (letterbox)
        scale = min(panel_w / frame_w, panel_h / frame_h)
        new_w, new_h = int(frame_w * scale), int(frame_h * scale)
        resized = cv2.resize(frame_bgr, (new_w, new_h))

        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        # numpy (H, W, 3) -> pygame Surface cần mảng theo trục (W, H, 3)
        rgb = np.transpose(rgb, (1, 0, 2))
        cam_surface = pygame.surfarray.make_surface(rgb)

        panel_surface.fill(settings.COLOR_PANEL_BG)
        offset_x = (panel_w - new_w) // 2
        offset_y = (panel_h - new_h) // 2
        panel_surface.blit(cam_surface, (offset_x, offset_y))

        # Chấm đỏ "LIVE" góc trên trái để biết webcam đang chạy thật
        self._pulse_t += 0.016
        pulse = int(150 + 60 * abs((self._pulse_t % 2.0) - 1.0))
        pygame.draw.circle(panel_surface, (pulse, 60, 60), (22, 22), 6)
        label = self.font_small.render("LIVE", True, settings.COLOR_PANEL_TEXT)
        panel_surface.blit(label, (34, 15))

    def _draw_hand_skeleton(self, frame_bgr, hand_landmarks, frame_w, frame_h):
        points = [(int(lm.x * frame_w), int(lm.y * frame_h)) for lm in hand_landmarks]
        for a, b in HAND_CONNECTIONS:
            if a < len(points) and b < len(points):
                cv2.line(frame_bgr, points[a], points[b], (60, 220, 60), 2)
        for (x, y) in points:
            cv2.circle(frame_bgr, (x, y), 4, (60, 60, 230), -1)
        # Tô đậm 2 đầu ngón cái/trỏ - đây là điểm quyết định điều khiển ná
        if len(points) > 8:
            cv2.circle(frame_bgr, points[4], 7, (0, 220, 255), -1)
            cv2.circle(frame_bgr, points[8], 7, (0, 220, 255), -1)
            cv2.line(frame_bgr, points[4], points[8], (0, 220, 255), 2)

    # ------------------------------------------------------------------
    # Placeholder (khi chưa có webcam / CV chưa sẵn sàng)
    # ------------------------------------------------------------------
    def _draw_placeholder(self, panel_surface, dt):
        w, h = panel_surface.get_size()

        pygame.draw.rect(panel_surface, (60, 60, 60), (10, 10, w - 20, h - 20), border_radius=8)
        pygame.draw.rect(panel_surface, (90, 90, 90), (10, 10, w - 20, h - 20), width=2, border_radius=8)

        title = self.font.render("CAMERA PREVIEW", True, settings.COLOR_PANEL_TEXT)
        panel_surface.blit(title, (w // 2 - title.get_width() // 2, 30))

        self._pulse_t += dt
        pulse = int(150 + 60 * abs((self._pulse_t % 2.0) - 1.0))
        dot_color = (pulse, 60, 60)
        pygame.draw.circle(panel_surface, dot_color, (30, 36), 6)

        msg_lines = [
            "Chua ket noi webcam.",
            "(Kiem tra CAM_INDEX trong",
            "config/settings.py, hoac",
            "webcam dang bi ung dung",
            "khac chiem dung)",
            "",
            "Hien tai dieu khien ná",
            "bang CHUOT trong khung",
            "game ben trai.",
        ]
        y = h // 2 - 60
        for line in msg_lines:
            img = self.font_small.render(line, True, (170, 170, 170))
            panel_surface.blit(img, (w // 2 - img.get_width() // 2, y))
            y += 22

    def get_size(self):
        return settings.CAMERA_PANEL_W, settings.CAMERA_PANEL_H