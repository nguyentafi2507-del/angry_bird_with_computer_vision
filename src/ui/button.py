"""
src/ui/button.py
Nút bấm chuột tái sử dụng cho Menu / HUD (Start, Restart, Next Level, Thoat man...).
Toạ độ rect dùng chung hệ với surface được vẽ lên (game_surface, offset (0,0)
trùng với cửa sổ nên pygame.mouse.get_pos() dùng trực tiếp được).
"""
import pygame

from config import settings


class Button:
    def __init__(self, rect, text, font=None, bg=(70, 70, 70),
                 bg_hover=(110, 110, 110), fg=(255, 255, 255), border=(255, 255, 255)):
        self.rect = pygame.Rect(rect)
        self.text = text
        pygame.font.init()
        self.font = font or pygame.font.SysFont(settings.FONT_NAME, 20, bold=True)
        self.bg = bg
        self.bg_hover = bg_hover
        self.fg = fg
        self.border = border

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        hovered = self.rect.collidepoint(mouse_pos)
        color = self.bg_hover if hovered else self.bg
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, self.border, self.rect, width=2, border_radius=8)
        text_img = self.font.render(self.text, True, self.fg)
        text_rect = text_img.get_rect(center=self.rect.center)
        surface.blit(text_img, text_rect)

    def is_clicked(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.rect.collidepoint(event.pos):
                    return True
        return False