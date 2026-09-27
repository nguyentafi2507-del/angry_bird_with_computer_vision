# CAMERA
CAM_INDEX = 0
MIRROR_CAMERA = True  # lật gương webcam để thao tác tay tự nhiên hơn (giống soi gương)

# COMPUTER VISION - MediaPipe HandLandmarker
HAND_MODEL_PATH = "hand_landmarker.task"
MAX_NUM_HANDS = 1
MIN_DETECTION_CONFIDENCE = 0.5
MIN_TRACKING_CONFIDENCE = 0.5

# KHUNG HÌNH GAME
FRAME_W = 1000
FRAME_H = 650

# PANEL CAMERA
CAMERA_PANEL_W = 700
CAMERA_PANEL_H = FRAME_H

# Tổng kích thước cửa sổ = game viewport + camera panel (chia 2 màn hình)
WINDOW_W = FRAME_W + CAMERA_PANEL_W
WINDOW_H = FRAME_H

FPS = 60

# SLINGSHOT / NÁ
ANCHOR_X = 200
ANCHOR_Y = 444

MAX_PULL_DISTANCE = 120       # px - khoảng cách kéo tối đa để đạt 100% lực bắn
MAX_LAUNCH_SPEED = 900.0      # px/s - vận tốc phóng tối đa
MIN_LAUNCH_PULL = 20          # px - khoảng cách kéo tối thiểu để tính là 1 lượt bắn

GRAB_ENTER_THRESHOLD = 42      # px - khoảng cách 2 ngón phải NHỎ HƠN mức này mới bắt đầu "nắm"
GRAB_EXIT_THRESHOLD = 60       # px - khoảng cách 2 ngón phải LỚN HƠN mức này mới xác nhận "thả"

# VẬT LÝ (Pymunk)
PYMUNK_GRAVITY_EARTH = (0.0, -700.0)
PYMUNK_GRAVITY_SPACE = (0.0, -10.0)

BIRD_RADIUS = 15
BIRD_MASS = 5
BIRD_FRICTION = 0.6
BIRD_ELASTICITY = 0.4

PIG_RADIUS = 18
PIG_MASS = 4
PIG_FRICTION = 0.7
PIG_ELASTICITY = 0.3
PIG_MAX_HEALTH = 1  # số lần va chạm đủ mạnh để chết

WOOD_FRICTION = 0.8
WOOD_ELASTICITY = 0.2
WOOD_DENSITY = 0.006  # mass = density * area


# Ma sát lăn thủ công khi chim chạm đất
GROUND_ROLL_FRICTION = 2.0

# Bán kính "độ dày" của segment sàn đất/tường trong Pymunk
GROUND_SEGMENT_RADIUS = 5

GROUND_HEIGHT = 20
COLLISION_TYPE_BIRD = 1
COLLISION_TYPE_PIG = 2
COLLISION_TYPE_WOOD = 3
COLLISION_TYPE_GROUND = 4

# LEVEL
DEFAULT_LEVEL_NUMBER = 0

# Số chim (đạn) mặc định cho MỖI màn chơi. Đổi số này để áp dụng đồng loạt cho
DEFAULT_NUMBER_OF_BIRDS = 2

# MÀU SẮC
COLOR_BG_SKY = (135, 206, 235)
COLOR_GROUND = (94, 63, 31)
COLOR_GROUND_TOP = (76, 153, 51)
COLOR_BIRD = (200, 30, 30)
COLOR_BIRD_OUTLINE = (120, 10, 10)
COLOR_PIG = (110, 200, 90)
COLOR_PIG_OUTLINE = (60, 120, 50)
COLOR_WOOD = (150, 105, 60)
COLOR_WOOD_OUTLINE = (90, 60, 30)
COLOR_SLINGSHOT = (80, 50, 20)
COLOR_TRAJECTORY = (255, 255, 255)
COLOR_HUD_TEXT = (20, 20, 20)
COLOR_PANEL_BG = (25, 25, 25)
COLOR_PANEL_TEXT = (200, 200, 200)
COLOR_WALL = (60, 60, 60)

FONT_NAME = None  # dùng font hệ thống mặc định của pygame