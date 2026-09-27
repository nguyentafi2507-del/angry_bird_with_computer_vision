"""
src/game/bird.py
Đối tượng Chim & vòng đời trạng thái (DOCKED, FLYING, SETTLED).
"""
import pymunk

from config import settings
from src.game import physics

DOCKED = "DOCKED"      # đang chờ trên ná, chưa bắn
FLYING = "FLYING"      # đang bay
SETTLED = "SETTLED"    # đã đáp / dừng lại (dùng để load chim tiếp theo)


class Bird:
    def __init__(self, space, anchor_pos):
        self.space = space
        self.anchor_pos = anchor_pos
        self.state = DOCKED
        self._settle_timer = 0.0

        mass = settings.BIRD_MASS
        radius = settings.BIRD_RADIUS
        moment = pymunk.moment_for_circle(mass, 0, radius)

        self.body = pymunk.Body(mass, moment)
        self.body.position = anchor_pos
        self.body.body_type = pymunk.Body.KINEMATIC  # trên ná: kéo bằng tay, không rơi tự do

        self.shape = pymunk.Circle(self.body, radius)
        self.shape.friction = settings.BIRD_FRICTION
        self.shape.elasticity = settings.BIRD_ELASTICITY
        self.shape.collision_type = settings.COLLISION_TYPE_BIRD
        self.shape.bird_ref = self  # tham chiếu ngược để dùng trong collisions.py

        self.space.add(self.body, self.shape)

    @property
    def position(self):
        return self.body.position

    def dock_at(self, pos):
        """Đặt chim tại vị trí kéo (khi đang bị 'nắm')."""
        if self.state == DOCKED:
            self.body.position = pos

    def launch(self, velocity):
        """Chuyển từ KINEMATIC -> DYNAMIC và bắn đi với vận tốc velocity."""
        if self.state != DOCKED:
            return
        pos = self.body.position
        self.body.body_type = pymunk.Body.DYNAMIC
        moment = pymunk.moment_for_circle(settings.BIRD_MASS, 0, settings.BIRD_RADIUS)
        self.body.mass = settings.BIRD_MASS
        self.body.moment = moment
        self.body.position = pos
        self.body.velocity = velocity
        self.state = FLYING

    def return_to_dock(self):
        """Nếu người chơi thả tay mà kéo quá ít (< MIN_LAUNCH_PULL) -> không bắn, về lại ná."""
        self.body.position = self.anchor_pos

    def update(self, dt):
        if self.state == FLYING:
            self._apply_ground_rolling_friction(dt)

            v = self.body.velocity
            speed = (v.x ** 2 + v.y ** 2) ** 0.5
            if speed < 8 and self.body.position.y < settings.FRAME_H:
                self._settle_timer += dt
                if self._settle_timer > 1.2:
                    self.state = SETTLED
            else:
                self._settle_timer = 0.0
            # Chim bay ra khỏi khung hình quá xa -> coi như settled để load chim mới
            if self.body.position.x > settings.FRAME_W + 150 or self.body.position.x < -150:
                self.state = SETTLED

    def _apply_ground_rolling_friction(self, dt):
        """Chim là hình tròn nên ma sát va chạm của Pymunk gần như không cản
        được chuyển động LĂN thuần (không trượt). Vì vậy khi chim vừa chạm đất,
        ta chủ động giảm dần vận tốc ngang + vận tốc góc mỗi frame để mô phỏng
        ma sát lăn thực tế: chim lăn thêm một đoạn ngắn rồi dừng hẳn, thay vì
        lăn mãi không dừng."""
        touching_ground = physics.is_touching_ground(self.body.position.y, settings.BIRD_RADIUS)
        if not touching_ground:
            return

        decay = physics.rolling_friction_decay(dt)
        v = self.body.velocity
        self.body.velocity = (v.x * decay, v.y)
        self.body.angular_velocity *= decay

    def remove_from_space(self):
        if self.shape in self.space.shapes:
            self.space.remove(self.shape)
        if self.body in self.space.bodies:
            self.space.remove(self.body)