"""
src/ui/menu.py
Menu hệ thống đơn giản hiển thị khi mở game (màn hình chào).
Bắt đầu bằng phím SPACE hoặc CLICK vào nút "BAT DAU".
"""
import pygame

from config import settings
from src.ui.button import Button


class MainMenu:
    def __init__(self):
        pygame.font.init()
        self.font_title = pygame.font.SysFont(settings.FONT_NAME, 60, bold=True)
        self.font_sub = pygame.font.SysFont(settings.FONT_NAME, 24)

        btn_w, btn_h = 220, 56
        cx = settings.FRAME_W // 2
        cy = settings.FRAME_H // 2 + 40
        self.start_button = Button(
            (cx - btn_w // 2, cy, btn_w, btn_h), "BAT DAU (SPACE)",
            bg=(40, 130, 40), bg_hover=(60, 170, 60),
        )

    def draw(self, surface):
        surface.fill(settings.COLOR_BG_SKY)
        title = self.font_title.render("ANGRY BIRDS", True, (200, 30, 30))
        rect = title.get_rect(center=(settings.FRAME_W // 2, settings.FRAME_H // 2 - 60))
        surface.blit(title, rect)

        hint = self.font_sub.render(
            "Dieu khien: giu chuot gan na, keo ra, tha de ban", True, (50, 50, 50)
        )
        hint_rect = hint.get_rect(center=(settings.FRAME_W // 2, settings.FRAME_H // 2 - 10))
        surface.blit(hint, hint_rect)

        self.start_button.draw(surface)

    def is_start_clicked(self, events):
        return self.start_button.is_clicked(events)