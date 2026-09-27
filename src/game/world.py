"""
src/game/world.py
Khởi tạo Pymunk Space, sàn đất, tường chắn & quy đổi tọa độ giữa Pymunk (y-up)
và Pygame (y-down).
"""
import pymunk

from config import settings


class GameWorld:
    def __init__(self):
        self.space = pymunk.Space()
        self.space.gravity = settings.PYMUNK_GRAVITY_EARTH
        self.space.sleep_time_threshold = 0.5

        self.right_wall_enabled = True
        self.is_space_mode = False

        self._ground_shape = None
        self._left_wall_shape = None
        self._right_wall_shape = None

        self._build_ground()
        self._build_walls()

    # ------------------------------------------------------------------
    # Xây dựng thế giới
    # ------------------------------------------------------------------
    def _build_ground(self):
        body = self.space.static_body
        ground_y = settings.GROUND_HEIGHT
        shape = pymunk.Segment(
            body, (-2000, ground_y), (settings.FRAME_W + 2000, ground_y),
            settings.GROUND_SEGMENT_RADIUS,
        )
        shape.friction = 1.0
        shape.elasticity = 0.1
        shape.collision_type = settings.COLLISION_TYPE_GROUND
        self.space.add(shape)
        self._ground_shape = shape

    def _build_walls(self):
        body = self.space.static_body
        top = settings.FRAME_H + 400  # tường cao hơn khung hình để chim không văng lên trời mãi
        ground_y = settings.GROUND_HEIGHT

        left = pymunk.Segment(body, (0, ground_y), (0, top), 5)
        left.friction = 0.5
        left.elasticity = 0.1
        self.space.add(left)
        self._left_wall_shape = left

        right = pymunk.Segment(
            body, (settings.FRAME_W, ground_y), (settings.FRAME_W, top), 5
        )
        right.friction = 0.5
        right.elasticity = 0.1
        self._right_wall_shape = right
        if self.right_wall_enabled:
            self.space.add(right)

    # ------------------------------------------------------------------
    # Điều khiển môi trường (theo phím tắt W / S / G)
    # ------------------------------------------------------------------
    def toggle_right_wall(self):
        self.right_wall_enabled = not self.right_wall_enabled
        if self.right_wall_enabled:
            if self._right_wall_shape not in self.space.shapes:
                self.space.add(self._right_wall_shape)
        else:
            if self._right_wall_shape in self.space.shapes:
                self.space.remove(self._right_wall_shape)
        return self.right_wall_enabled

    def set_space_gravity(self):
        self.space.gravity = settings.PYMUNK_GRAVITY_SPACE
        self.is_space_mode = True

    def set_earth_gravity(self):
        self.space.gravity = settings.PYMUNK_GRAVITY_EARTH
        self.is_space_mode = False

    # ------------------------------------------------------------------
    # Quy đổi tọa độ
    # ------------------------------------------------------------------
    @staticmethod
    def to_pygame(pos):
        """Pymunk (y-up, gốc dưới trái) -> Pygame (y-down, gốc trên trái)."""
        return int(pos[0]), int(settings.FRAME_H - pos[1])

    @staticmethod
    def to_pymunk(pos):
        """Pygame -> Pymunk."""
        return float(pos[0]), float(settings.FRAME_H - pos[1])

    def step(self, dt):
        # Sub-stepping nhỏ để mô phỏng ổn định hơn với vận tốc bắn lớn
        sub_steps = 4
        for _ in range(sub_steps):
            self.space.step(dt / sub_steps)

    def reset(self):
        """Xoá toàn bộ body/shape động (giữ ground & wall) để load lại level."""
        for body in list(self.space.bodies):
            if body.body_type == pymunk.Body.DYNAMIC:
                for shape in list(body.shapes):
                    self.space.remove(shape)
                self.space.remove(body)