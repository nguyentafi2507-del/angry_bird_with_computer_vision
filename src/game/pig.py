"""
src/game/pig.py
Đối tượng Heo & quản lý trạng thái va chạm / máu.
"""
import pymunk

from config import settings


class Pig:
    def __init__(self, pos, space):
        self.space = space
        self.alive = True
        self.health = settings.PIG_MAX_HEALTH

        mass = settings.PIG_MASS
        radius = settings.PIG_RADIUS
        moment = pymunk.moment_for_circle(mass, 0, radius)

        self.body = pymunk.Body(mass, moment)
        self.body.position = pos

        self.shape = pymunk.Circle(self.body, radius)
        self.shape.friction = settings.PIG_FRICTION
        self.shape.elasticity = settings.PIG_ELASTICITY
        self.shape.collision_type = settings.COLLISION_TYPE_PIG
        self.shape.pig_ref = self

        self.space.add(self.body, self.shape)

    @property
    def position(self):
        return self.body.position

    def take_hit(self, damage=1):
        self.health -= damage
        if self.health <= 0:
            self.kill()

    def kill(self):
        if not self.alive:
            return
        self.alive = False
        if self.shape in self.space.shapes:
            self.space.remove(self.shape)
        if self.body in self.space.bodies:
            self.space.remove(self.body)