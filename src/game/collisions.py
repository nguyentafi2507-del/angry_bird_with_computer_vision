"""
src/game/collisions.py
Quản lý va chạm bằng space.on_collision (cú pháp Pymunk 6.0+, thay cho
add_collision_handler đã bị loại bỏ).

Quy tắc va chạm hiện tại (theo yêu cầu gameplay):
    - Gỗ (Wood) KHÔNG bao giờ bị phá/xoá khi va chạm - chỉ bị đẩy/ngã theo vật lý
      thông thường của Pymunk. Vì vậy ta KHÔNG đăng ký handler nào cho
      Bird<->Wood hay Wood<->Wood để "destroy" gỗ; vật lý mặc định của Pymunk
      tự lo việc va chạm/đẩy, không cần custom logic.
    - Heo (Pig) chết ngay khi bị CHẠM vào (không cần đủ lực/impulse), bởi
      chim (Bird) hoặc bởi gỗ (Wood) đè/đẩy vào. Dùng callback "begin" (kích
      hoạt ngay khi 2 shape chạm nhau) thay cho "post_solve" + kiểm tra impulse.
"""
from config import settings
from src.utils.logger import get_logger

logger = get_logger()


def setup_collision_handlers(space, on_pig_killed=None):
    """Đăng ký collision handler cho space hiện tại.

    on_pig_killed(pig): callback tuỳ chọn để GameEngine cập nhật điểm số khi
    có heo chết.
    """

    def _kill_pig_in_shapes(shapes, cause):
        for shape in shapes:
            pig = getattr(shape, "pig_ref", None)
            if pig is not None and pig.alive:
                pig.kill()
                logger.info(f"Pig killed by touch ({cause})")
                if on_pig_killed:
                    on_pig_killed(pig)

    # --------------------------------------------------------------
    # Bird <-> Pig: chạm là chết, không cần đủ lực
    # --------------------------------------------------------------
    def bird_pig_begin(arbiter, space, data):
        _kill_pig_in_shapes(arbiter.shapes, "bird")
        return True  # vẫn cho vật lý xử lý va chạm bình thường (chim không xuyên qua heo)

    space.on_collision(
        settings.COLLISION_TYPE_BIRD,
        settings.COLLISION_TYPE_PIG,
        begin=bird_pig_begin,
    )

    # --------------------------------------------------------------
    # Pig <-> Wood: gỗ đè/đẩy vào heo cũng khiến heo chết ngay khi chạm
    # --------------------------------------------------------------
    def pig_wood_begin(arbiter, space, data):
        _kill_pig_in_shapes(arbiter.shapes, "wood")
        return True

    space.on_collision(
        settings.COLLISION_TYPE_PIG,
        settings.COLLISION_TYPE_WOOD,
        begin=pig_wood_begin,
    )

    # Bird <-> Wood và Wood <-> Wood: không đăng ký handler nào cả.
    # Pymunk sẽ tự tính toán va chạm/đẩy bình thường như mọi rigid body khác.