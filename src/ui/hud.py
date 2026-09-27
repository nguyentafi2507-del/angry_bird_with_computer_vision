"""
src/ui/hud.py
Hiển thị điểm số, số chim/heo còn lại, màn hình Thắng/Thua/Pause, và các nút
bấm chuột: Restart (góc trên phải, luôn hiện khi đang chơi), Thoát màn (về
menu), Tiếp tục (khi pause), Màn tiếp theo (khi thắng).
"""
import math

import pygame

from config import settings
from src.ui.button import Button


def _star_points(cx, cy, outer_r, inner_r):
    """Sinh 10 điểm góc của 1 ngôi sao 5 cánh (xen kẽ bán kính ngoài/trong)."""
    points = []
    for i in range(10):
        angle = -math.pi / 2 + i * math.pi / 5  # bắt đầu từ đỉnh trên cùng
        r = outer_r if i % 2 == 0 else inner_r
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    return points


class HUD:
    def __init__(self):
        pygame.font.init()
        self.font = pygame.font.SysFont(settings.FONT_NAME, 26)
        self.font_big = pygame.font.SysFont(settings.FONT_NAME, 54, bold=True)
        self.font_small = pygame.font.SysFont(settings.FONT_NAME, 18)

        # --- Nút góc trên phải: luôn hiện khi có level đang load ---
        self.btn_restart_corner = Button(
            (settings.FRAME_W - 264, 10, 120, 34), "Restart",
            bg=(150, 110, 20), bg_hover=(190, 140, 30),
        )
        self.btn_exit_corner = Button(
            (settings.FRAME_W - 134, 10, 120, 34), "Thoat man",
            bg=(140, 40, 40), bg_hover=(180, 60, 60),
        )

        # --- Nút overlay Pause ---
        cx = settings.FRAME_W // 2
        self.btn_pause_resume = Button(
            (cx - 100, settings.FRAME_H // 2 + 10, 200, 44), "Tiep tuc (P)",
            bg=(40, 130, 40), bg_hover=(60, 170, 60),
        )

        # --- Nút overlay Win ---
        self.btn_win_next = Button(
            (cx - 100, settings.FRAME_H // 2 + 60, 200, 44), "Man tiep theo (N)",
            bg=(40, 130, 40), bg_hover=(60, 170, 60),
        )

        # --- Nút overlay Lose ---
        self.btn_lose_restart = Button(
            (cx - 100, settings.FRAME_H // 2 + 60, 200, 44), "Choi lai (R)",
            bg=(150, 110, 20), bg_hover=(190, 140, 30),
        )

    # ------------------------------------------------------------------
    def draw_top_bar(self, surface, level_number, score, birds_left, pigs_left):
        text = f"Level {level_number}    Score: {score}    Birds: {birds_left}    Pigs: {pigs_left}"
        img = self.font.render(text, True, settings.COLOR_HUD_TEXT)
        surface.blit(img, (16, 12))

    def draw_controls_hint(self, surface):
        hints = "P: Pause  R: Restart  N: Next  M: Thoat man  W: Wall  S: Space  G: Gravity  Q/ESC: Quit"
        img = self.font_small.render(hints, True, settings.COLOR_HUD_TEXT)
        surface.blit(img, (16, settings.FRAME_H - 26))

    def draw_corner_buttons(self, surface):
        """Nút Restart / Thoát màn - luôn hiện khi đang trong 1 level (PLAYING/PAUSED/WON/LOST)."""
        self.btn_restart_corner.draw(surface)
        self.btn_exit_corner.draw(surface)

    def _overlay(self, surface, title, subtitle, color=(0, 0, 0)):
        overlay = pygame.Surface((settings.FRAME_W, settings.FRAME_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        surface.blit(overlay, (0, 0))

        title_img = self.font_big.render(title, True, color)
        rect = title_img.get_rect(center=(settings.FRAME_W // 2, settings.FRAME_H // 2 - 40))
        surface.blit(title_img, rect)

        if subtitle:
            sub_img = self.font.render(subtitle, True, (255, 255, 255))
            sub_rect = sub_img.get_rect(center=(settings.FRAME_W // 2, settings.FRAME_H // 2 - 5))
            surface.blit(sub_img, sub_rect)

    def draw_pause(self, surface):
        self._overlay(surface, "PAUSED", "Nhan P hoac bam nut de tiep tuc", color=(255, 255, 255))
        self.btn_pause_resume.draw(surface)

    def draw_win(self, surface, score, stars_earned=0):
        self._overlay(surface, "BAN THANG!", f"Diem: {score}", color=(255, 220, 60))
        self._draw_stars(surface, stars_earned)
        self.btn_win_next.draw(surface)

    def _draw_stars(self, surface, stars_earned):
        """Vẽ 3 ngôi sao giữa dòng điểm số và nút 'Màn tiếp theo': sao đã đạt
        tô vàng đầy, sao chưa đạt chỉ viền xám."""
        cx = settings.FRAME_W // 2
        cy = settings.FRAME_H // 2 + 30
        spacing = 62
        outer_r, inner_r = 20, 9

        for i, x in enumerate((cx - spacing, cx, cx + spacing)):
            pts = _star_points(x, cy, outer_r, inner_r)
            if i < stars_earned:
                pygame.draw.polygon(surface, (255, 210, 40), pts)       # sao đã đạt: vàng đầy
                pygame.draw.polygon(surface, (170, 120, 0), pts, 2)
            else:
                pygame.draw.polygon(surface, (90, 90, 90), pts, 2)      # sao chưa đạt: chỉ viền xám

    def draw_lose(self, surface):
        self._overlay(surface, "THUA ROI!", "Het chim ma van con heo song sot", color=(255, 80, 80))
        self.btn_lose_restart.draw(surface)

    # ------------------------------------------------------------------
    # Click checks (engine gọi các hàm này trong handle_events)
    # ------------------------------------------------------------------
    def is_restart_corner_clicked(self, events):
        return self.btn_restart_corner.is_clicked(events)

    def is_exit_corner_clicked(self, events):
        return self.btn_exit_corner.is_clicked(events)

    def is_pause_resume_clicked(self, events):
        return self.btn_pause_resume.is_clicked(events)

    def is_win_next_clicked(self, events):
        return self.btn_win_next.is_clicked(events)

    def is_lose_restart_clicked(self, events):
        return self.btn_lose_restart.is_clicked(events)