"""
src/game/game_engine.py
Vòng lặp game chính (Game Loop, Event, Render, States).

Màn hình được CHIA LÀM 2:
    - Bên trái  (settings.FRAME_W x settings.FRAME_H)  -> Game (Pymunk + Pygame)
    - Bên phải  (settings.CAMERA_PANEL_W x FRAME_H)     -> Camera panel (placeholder,
      sẽ hiển thị webcam + hand tracking khi tích hợp Computer Vision ở bước sau).

Điều khiển hiện tại: CHUỘT (xem src/game/slingshot.py -> MouseInputProvider).
Khi có hand tracking, chỉ cần thay MouseInputProvider bằng provider mới cùng
interface, không cần sửa gì trong file này.
"""
import math
import sys

import pygame

from config import settings
from src.game.world import GameWorld
from src.game.bird import Bird, DOCKED, FLYING, SETTLED
from src.game.level import Level, TOTAL_LEVELS
from src.game.collisions import setup_collision_handlers
from src.game.slingshot import Slingshot, MouseInputProvider
from src.game import physics
from src.ui.hud import HUD
from src.ui.camera_overlay import CameraOverlay
from src.ui.menu import MainMenu
from src.utils.logger import get_logger

logger = get_logger()

STATE_MENU = "MENU"
STATE_PLAYING = "PLAYING"
STATE_PAUSED = "PAUSED"
STATE_WON = "WON"
STATE_LOST = "LOST"


class GameEngine:
    def __init__(self):
        pygame.init()
        self.window = pygame.display.set_mode((settings.WINDOW_W, settings.WINDOW_H))
        pygame.display.set_caption("Angry Birds - Hand Gesture Edition")
        self.clock = pygame.time.Clock()

        # Hai vùng vẽ con (subsurface) cho 2 màn hình
        self.game_surface = self.window.subsurface(
            pygame.Rect(0, 0, settings.FRAME_W, settings.FRAME_H)
        )
        self.camera_surface = self.window.subsurface(
            pygame.Rect(settings.FRAME_W, 0, settings.CAMERA_PANEL_W, settings.CAMERA_PANEL_H)
        )

        self.hud = HUD()
        self.camera_overlay = CameraOverlay()
        self.menu = MainMenu()

        self.state = STATE_MENU
        self.score = 0
        self.stars_earned = 0
        self.level_number = settings.DEFAULT_LEVEL_NUMBER

        self.world = None
        self.level = None
        self.slingshot = Slingshot(self._create_input_provider())
        self.current_bird = None

        self.running = True

    def _create_input_provider(self):
        """Ưu tiên điều khiển bằng TAY qua webcam (Computer Vision). Nếu không
        khởi tạo được (thiếu webcam, thiếu model, thiếu thư viện...) thì tự
        động dùng lại CHUỘT để game vẫn chơi được bình thường."""
        try:
            from src.game.slingshot import HandInputProvider
            provider = HandInputProvider()
            logger.info("Da bat Computer Vision (hand tracking) de dieu khien na.")
            return provider
        except Exception as e:
            logger.info(
                f"Khong the khoi tao Computer Vision ({e}). "
                f"Dung CHUOT de dieu khien thay the."
            )
            return MouseInputProvider()

    # ------------------------------------------------------------------
    # Load / Reset level
    # ------------------------------------------------------------------
    def load_level(self, level_number):
        self.level_number = level_number
        self.world = GameWorld()
        setup_collision_handlers(
            self.world.space,
            on_pig_killed=self._on_pig_killed,
        )
        self.level = Level(self.world.space, level_number)
        self.birds_left = self.level.number_of_birds
        self.current_bird = None
        self.state = STATE_PLAYING
        self.stars_earned = 0
        self._spawn_next_bird()
        logger.info(f"Loaded level {level_number}")

    def restart_level(self):
        self.score = 0
        self.load_level(self.level_number)

    def next_level(self):
        if self.level_number + 1 < TOTAL_LEVELS:
            self.load_level(self.level_number + 1)
        else:
            logger.info("Da het level! Quay lai level 0.")
            self.load_level(0)

    # ------------------------------------------------------------------
    # Callbacks va chạm -> điểm số
    # ------------------------------------------------------------------
    def _on_pig_killed(self, pig):
        self.score += 5000

    # ------------------------------------------------------------------
    # Chuyển trạng thái dùng chung cho cả phím tắt lẫn nút bấm chuột
    # ------------------------------------------------------------------
    def _go_to_menu(self):
        self.state = STATE_MENU

    # ------------------------------------------------------------------
    # Spawn chim
    # ------------------------------------------------------------------
    def _spawn_next_bird(self):
        anchor_pymunk = (settings.ANCHOR_X, settings.FRAME_H - settings.ANCHOR_Y)
        self.current_bird = Bird(self.world.space, anchor_pymunk)

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------
    def handle_events(self):
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event.key)

        self._handle_mouse_buttons(events)
        return events

    def _handle_keydown(self, key):
        if key in (pygame.K_q, pygame.K_ESCAPE):
            self.running = False
        elif key == pygame.K_SPACE and self.state == STATE_MENU:
            self.load_level(self.level_number)
        elif key == pygame.K_p and self.state in (STATE_PLAYING, STATE_PAUSED):
            self.state = STATE_PAUSED if self.state == STATE_PLAYING else STATE_PLAYING
        elif key == pygame.K_r and self.state in (STATE_PLAYING, STATE_PAUSED, STATE_WON, STATE_LOST):
            self.restart_level()
        elif key == pygame.K_n and self.state == STATE_WON:
            self.next_level()
        elif key == pygame.K_m and self.state in (STATE_PLAYING, STATE_PAUSED, STATE_WON, STATE_LOST):
            self._go_to_menu()
        elif key == pygame.K_w and self.world is not None:
            enabled = self.world.toggle_right_wall()
            logger.info(f"Right wall {'enabled' if enabled else 'disabled'}")
        elif key == pygame.K_s and self.world is not None:
            self.world.set_space_gravity()
            logger.info("Space mode (low gravity)")
        elif key == pygame.K_g and self.world is not None:
            self.world.set_earth_gravity()
            logger.info("Earth gravity restored")

    def _handle_mouse_buttons(self, events):
        """Xử lý click chuột vào các nút UI (Start, Restart, Thoat man, Next, Resume).
        Tách riêng khỏi slingshot.update() để không bị nhầm với thao tác kéo-ban."""
        if self.state == STATE_MENU:
            if self.menu.is_start_clicked(events):
                self.load_level(self.level_number)
            return

        # Các nút góc trên phải, hiện xuyên suốt khi đã có level (mọi state khác MENU)
        if self.world is not None:
            if self.hud.is_restart_corner_clicked(events):
                self.restart_level()
                return
            if self.hud.is_exit_corner_clicked(events):
                self._go_to_menu()
                return

        if self.state == STATE_PAUSED and self.hud.is_pause_resume_clicked(events):
            self.state = STATE_PLAYING
        elif self.state == STATE_WON and self.hud.is_win_next_clicked(events):
            self.next_level()
        elif self.state == STATE_LOST and self.hud.is_lose_restart_clicked(events):
            self.restart_level()

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def update(self, dt, events):
        # Đọc trạng thái camera/tay (hoặc chuột) mỗi frame, kể cả khi đang
        # PAUSED/WON/LOST, để khung camera bên phải không bị đứng hình.
        # Chỉ bỏ qua lúc ở MENU vì lúc đó chưa có Slingshot nào đang hoạt động
        # theo 1 level cụ thể (nhưng input_provider vẫn tồn tại nên vẫn đọc được).
        self.slingshot.update_input(events)

        if self.state != STATE_PLAYING:
            return

        self.world.step(dt)

        if self.current_bird and self.current_bird.state == DOCKED:
            velocity = self.slingshot.apply_pull(self.current_bird)
            if velocity is not None:
                self.current_bird.launch(velocity)

        if self.current_bird:
            self.current_bird.update(dt)
            if self.current_bird.state == SETTLED:
                self.current_bird.remove_from_space()
                self.current_bird = None
                self.birds_left -= 1

        if self.level.is_won():
            self.state = STATE_WON
            self.stars_earned = self.level.compute_stars(self.score)
            return

        if self.current_bird is None and self.birds_left > 0:
            self._spawn_next_bird()
        elif self.current_bird is None and self.birds_left <= 0:
            self.state = STATE_LOST

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------
    def render(self, dt):
        if self.state == STATE_MENU:
            self.menu.draw(self.game_surface)
        else:
            self._render_game()
            self.hud.draw_corner_buttons(self.game_surface)

        self.camera_overlay.render(
            self.camera_surface, dt=dt,
            frame=self._get_camera_frame(), hand_landmarks=self._get_hand_landmarks(),
        )

        if self.state == STATE_PAUSED:
            self.hud.draw_pause(self.game_surface)
        elif self.state == STATE_WON:
            self.hud.draw_win(self.game_surface, self.score, self.stars_earned)
        elif self.state == STATE_LOST:
            self.hud.draw_lose(self.game_surface)

        # Viền phân chia giữa 2 màn hình
        pygame.draw.line(
            self.window, (0, 0, 0),
            (settings.FRAME_W, 0), (settings.FRAME_W, settings.WINDOW_H), 3
        )

        pygame.display.flip()

    def _render_game(self):
        surf = self.game_surface
        surf.fill(settings.COLOR_BG_SKY)

        # Mặt đất
        ground_y_screen = settings.FRAME_H - settings.GROUND_HEIGHT
        pygame.draw.rect(
            surf, settings.COLOR_GROUND,
            (0, ground_y_screen, settings.FRAME_W, settings.GROUND_HEIGHT + 40)
        )
        pygame.draw.rect(surf, settings.COLOR_GROUND_TOP, (0, ground_y_screen, settings.FRAME_W, 6))

        if not self.world.right_wall_enabled:
            pass  # tường phải đã tắt - không vẽ gì thêm
        else:
            pygame.draw.rect(
                surf, settings.COLOR_WALL,
                (settings.FRAME_W - 6, 0, 6, settings.FRAME_H)
            )

        # Ná (2 cột chống)
        anchor_screen = (settings.ANCHOR_X, settings.ANCHOR_Y)
        pygame.draw.line(surf, settings.COLOR_SLINGSHOT,
                          (anchor_screen[0] - 14, anchor_screen[1] + 10),
                          (anchor_screen[0] - 14, anchor_screen[1] + 90), 8)
        pygame.draw.line(surf, settings.COLOR_SLINGSHOT,
                          (anchor_screen[0] + 14, anchor_screen[1] + 10),
                          (anchor_screen[0] + 14, anchor_screen[1] + 90), 8)

        # Dây ná + đường kéo (nếu đang pull)
        if self.slingshot.is_pulling():
            a, b = self.slingshot.get_pull_line()
            pygame.draw.line(surf, settings.COLOR_SLINGSHOT, (a[0] - 14, a[1] + 15), b, 4)
            pygame.draw.line(surf, settings.COLOR_SLINGSHOT, (a[0] + 14, a[1] + 15), b, 4)
            self._draw_trajectory_preview(surf, a, b)

        # Obstacles (gỗ)
        for obs in self.level.obstacles:
            if not obs.alive:
                continue
            corners = obs.get_corners_pygame(self.world.to_pygame)
            pygame.draw.polygon(surf, settings.COLOR_WOOD, corners)
            pygame.draw.polygon(surf, settings.COLOR_WOOD_OUTLINE, corners, 2)

        # Pigs
        for pig in self.level.pigs:
            if not pig.alive:
                continue
            x, y = self.world.to_pygame(pig.position)
            pygame.draw.circle(surf, settings.COLOR_PIG, (x, y), settings.PIG_RADIUS)
            pygame.draw.circle(surf, settings.COLOR_PIG_OUTLINE, (x, y), settings.PIG_RADIUS, 2)

        # Bird hiện tại
        if self.current_bird:
            x, y = self.world.to_pygame(self.current_bird.position)
            pygame.draw.circle(surf, settings.COLOR_BIRD, (x, y), settings.BIRD_RADIUS)
            pygame.draw.circle(surf, settings.COLOR_BIRD_OUTLINE, (x, y), settings.BIRD_RADIUS, 2)

        # 2 chấm ngón tay (cái + trỏ) - chỉ có khi đang điều khiển bằng TAY qua
        # webcam (HandInputProvider). Vẽ đè lên trên cùng để luôn thấy rõ.
        self._draw_finger_dots(surf)

        self.hud.draw_top_bar(surf, self.level_number, self.score, self.birds_left,
                               self.level.pigs_remaining())
        self.hud.draw_controls_hint(surf)

    def _draw_finger_dots(self, surf):
        finger_points = self._get_finger_points()
        if finger_points is None:
            return
        thumb_pt, index_pt = finger_points
        thumb_pt = (int(thumb_pt[0]), int(thumb_pt[1]))
        index_pt = (int(index_pt[0]), int(index_pt[1]))

        grabbing = self.slingshot.input_provider.is_grabbing()
        dot_color = (60, 220, 90) if grabbing else (255, 210, 40)  # xanh khi đang nắm, vàng khi chưa

        for pt in (thumb_pt, index_pt):
            pygame.draw.circle(surf, dot_color, pt, 10)
            pygame.draw.circle(surf, (0, 0, 0), pt, 10, 2)

    def _draw_trajectory_preview(self, surf, anchor_screen, pull_screen):
        """Vẽ vài điểm chấm dự đoán quỹ đạo bay dựa trên lực kéo hiện tại.
        Dùng chung công thức đạn đạo với slingshot.py qua src/game/physics.py
        (tránh 2 nơi tự tính riêng rồi lệch công thức khi sửa)."""
        pull_vec = (pull_screen[0] - anchor_screen[0], pull_screen[1] - anchor_screen[1])
        pull_distance = math.hypot(pull_vec[0], pull_vec[1])
        if not physics.is_pull_valid(pull_distance):
            return

        velocity_screen = physics.compute_launch_velocity_screen(pull_vec)
        gravity_screen = abs(self.world.space.gravity[1])  # luôn dương = rơi xuống trong screen space
        points = physics.predict_trajectory_screen(
            anchor_screen, velocity_screen, gravity_screen,
            bounds=(settings.FRAME_W, settings.FRAME_H),
        )
        for fx, fy in points:
            pygame.draw.circle(surf, settings.COLOR_TRAJECTORY, (int(fx), int(fy)), 3)

    def _get_camera_frame(self):
        provider = self.slingshot.input_provider
        if hasattr(provider, "get_camera_frame"):
            return provider.get_camera_frame()
        return None

    def _get_hand_landmarks(self):
        provider = self.slingshot.input_provider
        if hasattr(provider, "get_hand_landmarks"):
            return provider.get_hand_landmarks()
        return None

    def _get_finger_points(self):
        provider = self.slingshot.input_provider
        if hasattr(provider, "get_finger_points"):
            return provider.get_finger_points()
        return None

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self):
        while self.running:
            dt = self.clock.tick(settings.FPS) / 1000.0
            events = self.handle_events()
            self.update(dt, events)
            self.render(dt)

        provider = self.slingshot.input_provider
        if hasattr(provider, "close"):
            provider.close()

        pygame.quit()
        sys.exit()