"""
src/game/physics.py
Các công thức vật lý DÙNG CHUNG, tránh tình trạng 2 nơi trong code tự viết
lại cùng 1 công thức rồi lệch nhau khi sửa (bài học thực tế: bug
GROUND_SEGMENT_RADIUS trước đây, sửa ngưỡng chạm đất ở bird.py mà quên
đồng bộ với world.py).

Có 2 nhóm hàm:
    1. Đạn đạo (pull -> velocity -> quỹ đạo dự đoán): dùng chung giữa
       slingshot.py (bắn thật) và game_engine.py (vẽ đường chấm dự đoán).
    2. Ma sát lăn khi vật thể tròn (chim) nằm/lăn trên đất: dùng bởi bird.py.

Quy ước toạ độ: mọi hàm đạn đạo trong file này làm việc theo hệ MÀN HÌNH
(y hướng xuống, giống pygame/chuột/tay) - vì đó là hệ tự nhiên của thao tác
"kéo". Chỉ quy đổi sang hệ PYMUNK (y hướng lên) ở bước cuối cùng bằng
screen_velocity_to_pymunk(), ngay trước khi gọi bird.launch().
"""
from config import settings
from src.utils import vector2d as v2


# ======================================================================
# 1. Đạn đạo: pull -> velocity -> quỹ đạo dự đoán
# ======================================================================
def compute_pull(pull_vector_screen, max_pull_distance=None):
    """Giới hạn độ dài vector kéo theo MAX_PULL_DISTANCE.
    Trả về (pull_vector_da_gioi_han, pull_distance)."""
    max_pull_distance = settings.MAX_PULL_DISTANCE if max_pull_distance is None else max_pull_distance
    clamped = v2.clamp_magnitude(pull_vector_screen, max_pull_distance)
    distance = v2.magnitude(clamped)
    return clamped, distance


def is_pull_valid(pull_distance, min_pull_distance=None):
    """Kéo phải đủ xa (>= MIN_LAUNCH_PULL) mới tính là 1 lượt bắn hợp lệ."""
    min_pull_distance = settings.MIN_LAUNCH_PULL if min_pull_distance is None else min_pull_distance
    return pull_distance >= min_pull_distance


def compute_launch_velocity_screen(pull_vector_screen, max_pull_distance=None, max_launch_speed=None):
    """Từ vector kéo (anchor -> điểm kéo, hệ MÀN HÌNH y-down), tính vận tốc
    phóng (vx, vy) CŨNG theo hệ MÀN HÌNH. Hướng bay luôn NGƯỢC hướng kéo,
    độ lớn tỉ lệ thuận với khoảng cách kéo (tối đa ở MAX_PULL_DISTANCE).
    Trả về (0, 0) nếu vector kéo bằng 0."""
    max_pull_distance = settings.MAX_PULL_DISTANCE if max_pull_distance is None else max_pull_distance
    max_launch_speed = settings.MAX_LAUNCH_SPEED if max_launch_speed is None else max_launch_speed

    pull_distance = v2.magnitude(pull_vector_screen)
    if pull_distance == 0:
        return (0.0, 0.0)

    power_ratio = min(pull_distance / max_pull_distance, 1.0)
    speed = power_ratio * max_launch_speed
    direction = v2.normalize((-pull_vector_screen[0], -pull_vector_screen[1]))
    return (direction[0] * speed, direction[1] * speed)


def screen_velocity_to_pymunk(vx_screen, vy_screen):
    """Quy đổi vận tốc từ hệ MÀN HÌNH (y-down) sang hệ PYMUNK (y-up)."""
    return (vx_screen, -vy_screen)


def predict_trajectory_screen(anchor_screen, velocity_screen, gravity_magnitude,
                               max_points=18, step_dt=0.06, bounds=None):
    """Sinh danh sách điểm (x, y) dự đoán quỹ đạo bay - hệ MÀN HÌNH (y-down),
    theo công thức đạn đạo parabol chuẩn: y(t) = y0 + vy*t + 0.5*g*t^2.

    gravity_magnitude PHẢI là số dương (độ lớn trọng lực) - vì trong hệ màn
    hình "rơi xuống" luôn là +y, bất kể trọng lực trong Pymunk đang mang
    dấu âm theo quy ước y-up của nó.
    bounds: (width, height) tuỳ chọn - điểm ngoài khung hình sẽ bị bỏ qua.
    """
    px, py = anchor_screen
    vx, vy = velocity_screen
    points = []
    t = 0.0
    for _ in range(max_points):
        t += step_dt
        fx = px + vx * t
        fy = py + vy * t + 0.5 * gravity_magnitude * t * t
        if bounds is None or (0 <= fx <= bounds[0] and 0 <= fy <= bounds[1]):
            points.append((fx, fy))
    return points


# ======================================================================
# 2. Ma sát lăn khi vật thể tròn nằm/lăn trên đất
# ======================================================================
def is_touching_ground(y_position_pymunk, object_radius, epsilon=4):
    """Kiểm tra 1 vật thể HÌNH TRÒN (bán kính object_radius) có đang
    chạm/nghỉ trên mặt đất hay không (toạ độ Pymunk, y-up).

    Tính đúng cả độ dày của segment sàn đất (settings.GROUND_SEGMENT_RADIUS)
    - nếu quên cộng số này, ngưỡng sẽ luôn thấp hơn độ cao nghỉ thực tế và
    ma sát lăn sẽ gần như không bao giờ kích hoạt (bug đã từng xảy ra)."""
    resting_height = settings.GROUND_HEIGHT + settings.GROUND_SEGMENT_RADIUS + object_radius
    return y_position_pymunk <= resting_height + epsilon


def rolling_friction_decay(dt, friction=None):
    """Hệ số nhân vào vận tốc mỗi frame để mô phỏng ma sát lăn cho vật thể
    hình tròn (ma sát va chạm thông thường của Pymunk không cản được lăn
    thuần không trượt). Trả về giá trị trong [0, 1] - càng gần 0 thì càng
    dừng nhanh."""
    friction = settings.GROUND_ROLL_FRICTION if friction is None else friction
    return max(0.0, 1.0 - friction * dt)