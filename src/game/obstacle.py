"""
src/game/obstacle.py
Đối tượng Khối gỗ (cột/dầm) với cơ chế render fallback (chưa có sprite ảnh).
"""
import pymunk

from config import settings


class Obstacle:
    """Khối gỗ hình chữ nhật, có thể xoay (dầm nằm ngang) hoặc đứng (cột)."""

    def __init__(self, space, pos, width, height, angle=0.0):
        self.space = space
        self.alive = True
        self.width = width
        self.height = height

        area = width * height
        mass = max(area * settings.WOOD_DENSITY, 0.5)
        moment = pymunk.moment_for_box(mass, (width, height))

        self.body = pymunk.Body(mass, moment)
        self.body.position = pos
        self.body.angle = angle

        self.shape = pymunk.Poly.create_box(self.body, (width, height))
        self.shape.friction = settings.WOOD_FRICTION
        self.shape.elasticity = settings.WOOD_ELASTICITY
        self.shape.collision_type = settings.COLLISION_TYPE_WOOD
        self.shape.obstacle_ref = self

        self.space.add(self.body, self.shape)

    @property
    def position(self):
        return self.body.position

    def destroy(self):
        if not self.alive:
            return
        self.alive = False
        if self.shape in self.space.shapes:
            self.space.remove(self.shape)
        if self.body in self.space.bodies:
            self.space.remove(self.body)

    def get_corners_pygame(self, to_pygame_func):
        """Trả về 4 điểm góc (đã xoay) trong hệ toạ độ Pygame để vẽ polygon."""
        local_corners = [
            (-self.width / 2, -self.height / 2),
            (self.width / 2, -self.height / 2),
            (self.width / 2, self.height / 2),
            (-self.width / 2, self.height / 2),
        ]
        world_corners = [self.body.local_to_world(c) for c in local_corners]
        return [to_pygame_func(c) for c in world_corners]