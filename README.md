# 🐦 Angry Birds — Python · Pygame · Pymunk · MediaPipe

> Clone Angry Birds 2D viết bằng **Python**, kết hợp mô phỏng vật lý thực với **Pymunk**, đồ hoạ **Pygame** và điều khiển bằng **cử chỉ tay qua webcam** (MediaPipe + OpenCV) — tự động fallback về chuột nếu không có webcam.

---

## ✨ Tính năng

| Nhóm | Chi tiết |
|---|---|
| ⚙️ **Vật lý 2D** | Pymunk 6+ · trọng lực Trái Đất / Không gian · ma sát · đàn hồi · sub-stepping 4×/frame |
| 🎯 **Ná bắn** | Kéo–thả bằng chuột hoặc cử chỉ tay · giới hạn bán kính · dự đoán quỹ đạo thời gian thực |
| 🖐️ **Hand Tracking** | MediaPipe Tasks HandLandmarker · 21 landmark · khử rung Hysteresis · **tự động kích hoạt khi có webcam** |
| 💥 **Va chạm** | Xung lực ngưỡng riêng cho Chim↔Heo · Chim↔Gỗ · Heo↔Gỗ · Gỗ↔Gỗ |
| 🎮 **Gameplay** | 4 màn (0–3) · hệ thống điểm sao · 5 trạng thái game · HUD + Menu đầy đủ |
| 🪟 **Cửa sổ kép** | Game **1000×650** (trái) + Camera panel **700×650** (phải) = tổng **1700×650** |

---

## 📁 Cấu trúc dự án

```
Angry bird/
├── main.py                      # Entry-point: khởi tạo GameEngine → engine.run()
├── requirements.txt             # pygame · pymunk · numpy · opencv-python · mediapipe
├── hand_landmarker.task         # Model MediaPipe Hand Landmarker (~7.8 MB)
│
├── config/
│   ├── __init__.py
│   └── settings.py              # Mọi hằng số hệ thống (kích thước, vật lý, màu sắc, ngưỡng)
│
└── src/
    ├── __init__.py
    │
    ├── vision/                  # Module Computer Vision
    │   ├── __init__.py
    │   ├── hand_tracker.py      # Mở webcam + chạy HandLandmarker (VIDEO mode), trả về 21 landmark
    │   ├── coordinate_mapper.py # Tính điểm điều khiển, khoảng cách 2 ngón, vector bắn
    │   └── gesture_detector.py  # Máy trạng thái Nắm / Thả với khử rung Hysteresis
    │
    ├── game/                    # Logic game & động cơ vật lý
    │   ├── __init__.py
    │   ├── game_engine.py       # Game Loop 60 FPS · 5 trạng thái · auto-select input provider
    │   ├── world.py             # Pymunk Space · sàn đất · tường biên · chuyển đổi toạ độ Y
    │   ├── bird.py              # Thực thể Chim: DOCKED → FLYING → SETTLED
    │   ├── pig.py               # Thực thể Heo: máu · sát thương · kill()
    │   ├── obstacle.py          # Khối gỗ: khối lượng theo diện tích · get_corners_pygame()
    │   ├── level.py             # 4 màn chơi + helpers dựng cấu trúc phòng thủ
    │   ├── slingshot.py         # InputProvider (Mouse / Hand) · Slingshot · HandInputProvider
    │   ├── collisions.py        # Đăng ký handler va chạm Pymunk 6+ via space.on_collision
    │   └── physics.py           # Công thức dùng chung: đạn đạo · dự đoán quỹ đạo · ma sát lăn
    │
    ├── ui/                      # Giao diện người dùng
    │   ├── __init__.py
    │   ├── button.py            # Widget Button tái sử dụng (hover · click · bo góc)
    │   ├── hud.py               # HUD: điểm số · chim/heo · overlay Pause/Win/Lose
    │   ├── camera_overlay.py    # Panel camera 700×650: hiển thị frame webcam + vẽ khung xương tay
    │   └── menu.py              # Màn hình khởi động
    │
    └── utils/
        ├── __init__.py
        ├── logger.py            # get_logger() — logging có timestamp ra console
        └── vector2d.py          # Thư viện vector 2D: distance · normalize · clamp · magnitude
```

---

## ⚙️ Cấu hình chính (`config/settings.py`)

| Nhóm | Hằng số | Giá trị |
|---|---|---|
| **Cửa sổ** | `FRAME_W × FRAME_H` | `1000 × 650` |
| **Camera panel** | `CAMERA_PANEL_W × CAMERA_PANEL_H` | `700 × 650` |
| **FPS** | `FPS` | `60` |
| **Ná** | `ANCHOR_X, ANCHOR_Y` | `200, 444` |
| **Kéo** | `MAX_PULL_DISTANCE` | `120 px` |
| **Tốc độ bắn** | `MAX_LAUNCH_SPEED` | `900 px/s` |
| **Cử chỉ Nắm** | `GRAB_ENTER_THRESHOLD` | `< 42 px` |
| **Cử chỉ Thả** | `GRAB_EXIT_THRESHOLD` | `> 60 px` |
| **Trọng lực** | `PYMUNK_GRAVITY_EARTH` | `(0, −700)` |
| **Không gian** | `PYMUNK_GRAVITY_SPACE` | `(0, −10)` |

---

## 🔬 Giải thích module quan trọng

### `src/game/slingshot.py` — InputProvider Pattern

Game tự động chọn nguồn điều khiển khi khởi động (`game_engine._create_input_provider()`):

```
Có webcam + model MediaPipe  →  HandInputProvider  (điều khiển bằng tay)
Không có webcam / lỗi        →  MouseInputProvider  (tự động fallback về chuột)
```

Ba lớp cùng implement interface `InputProvider`:

| Lớp | Mô tả |
|---|---|
| `InputProvider` | Interface trừu tượng: `get_control_point()`, `is_grabbing()`, `just_released()` |
| `MouseInputProvider` | Giữ chuột trái trong bán kính anchor để nắm, thả để bắn |
| `HandInputProvider` | Chụm ngón cái + trỏ để nắm, xòe ra để bắn; expose `get_camera_frame()`, `get_hand_landmarks()`, `get_finger_points()` cho camera panel |

---

### `src/game/physics.py` — Công thức dùng chung

Tập trung mọi công thức vật lý tránh duplicate giữa `slingshot.py` và `game_engine.py`:

| Hàm | Mô tả |
|---|---|
| `compute_pull()` | Giới hạn vector kéo theo `MAX_PULL_DISTANCE` |
| `compute_launch_velocity_screen()` | Vector kéo → vận tốc bắn (hệ màn hình y-down) |
| `screen_velocity_to_pymunk()` | Đổi sang hệ Pymunk (y-up): đảo dấu `vy` |
| `predict_trajectory_screen()` | Sinh danh sách điểm quỹ đạo parabol (vẽ đường chấm) |
| `is_touching_ground()` | Kiểm tra vật tròn chạm đất (tính đúng `GROUND_SEGMENT_RADIUS`) |
| `rolling_friction_decay()` | Ma sát lăn thủ công cho chim trên đất |

---

### `src/vision/` — Computer Vision Pipeline

```
webcam frame
    └─► HandTracker.read()           # OpenCV cap + MediaPipe VIDEO mode
            └─► 21 landmarks (chuẩn hoá 0..1)
                    ├─► coordinate_mapper.compute_control_point()   # điểm giữ dây ná
                    ├─► coordinate_mapper.pinch_distance_px()       # khoảng cách 2 ngón
                    └─► GestureDetector.update(distance)            # Nắm / Thả (Hysteresis)
```

Kết quả được `HandInputProvider.update()` gọi mỗi frame và đưa vào `Slingshot`.

---

### `src/game/level.py` — Màn chơi & cấu trúc phòng thủ

| Màn | Mô tả | Heo |
|---|---|---|
| **Level 0** | Nhập môn — heo lộ thiên, không gỗ | 1 |
| **Level 1** | 1 hàng cột gỗ mở (`open_flat`) | 1 |
| **Level 2** | Hộp kín (`closed_flat`) bảo vệ heo | 2 |
| **Level 3** | Tháp dọc + tháp ngang (`vertical_pile` + `horizontal_pile`) | 3 |

4 helper tái sử dụng để dựng cấu trúc gỗ:

```python
open_flat(x, y, count)        # cột đứng riêng lẻ, không nóc
closed_flat(x, y, count)      # cột đứng + dầm ngang làm nóc
horizontal_pile(x, y, count)  # dầm ngang chồng lên nhau (tháp ngang)
vertical_pile(x, y, count)    # cột đứng sát nhau (tháp dọc / tường)
```

---

## 🚀 Cài đặt & Chạy

### Yêu cầu
- Python **3.10** hoặc **3.11**
- Webcam (tuỳ chọn — game vẫn chạy bình thường bằng chuột nếu không có)

### 1. Clone & tạo môi trường ảo

```bash
git clone https://github.com/<your-username>/angry-birds-cv.git
cd angry-birds-cv

python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

### 2. Cài đặt thư viện

```bash
pip install -r requirements.txt
```

> File `hand_landmarker.task` (~7.8 MB) đã có sẵn trong repo.
> Đặt đúng thư mục gốc dự án hoặc chỉnh đường dẫn `HAND_MODEL_PATH` trong `config/settings.py`.

### 3. Chạy

```bash
python main.py
```

Khi khởi động, game tự động thử mở webcam:
- ✅ **Có webcam + model** → điều khiển bằng tay, khung camera hiển thị live feed
- ⚠️ **Không có webcam** → tự fallback về chuột, in log thông báo, game vẫn chạy bình thường

---

## 🎮 Điều khiển

### Chuột (mặc định khi không có webcam)

| Thao tác | Hành động |
|---|---|
| Giữ chuột trái gần ná | Nắm dây |
| Kéo ra xa | Canh góc và lực (đường chấm trắng dự đoán quỹ đạo) |
| Thả chuột | Bắn chim |

### Tay qua webcam

| Cử chỉ | Hành động |
|---|---|
| Chụm ngón cái + trỏ (< 42 px) | Nắm dây — chấm **xanh** xuất hiện trên màn game |
| Di chuyển tay ra sau | Kéo căng dây ná |
| Xoè ngón (> 60 px) | Thả — phóng chim; chấm chuyển **vàng** |

### Phím tắt

| Phím | Chức năng |
|---|---|
| `SPACE` | Bắt đầu game từ Menu |
| `P` | Tạm dừng / Tiếp tục |
| `R` | Chơi lại màn hiện tại |
| `N` | Màn tiếp theo (chỉ sau khi thắng) |
| `M` | Quay về Menu chính |
| `W` | Bật / Tắt tường biên phải |
| `S` | Chế độ **Không gian** (trọng lực thấp `(0, −10)`) |
| `G` | Trở về **Trọng lực Trái Đất** `(0, −700)` |
| `Q` / `ESC` | Thoát game |

---

## 🏗️ Thêm màn chơi mới

1. Mở `src/game/level.py`, thêm hàm `build_4(self)`:

```python
def build_4(self):
    self.number_of_birds = 4
    self.closed_flat(self.sx(750), 20, 3, spacing=80)
    self.horizontal_pile(self.sx(950), 20, 4)
    self.pigs.append(Pig((self.sx(830), 80), self.space))
    self.pigs.append(Pig((self.sx(950), 150), self.space))
    self.one_star   = 15000
    self.two_star   = 25000
    self.three_star = 35000
```

2. Cập nhật dòng cuối file:

```python
TOTAL_LEVELS = 5  # tăng thêm 1
```

> **Lưu ý:** Dùng `self.sx(x)` thay vì toạ độ x tuyệt đối — hàm này tự điều chỉnh
> theo `FRAME_W` hiện tại để gỗ/heo không bị lệch khi thay đổi kích thước khung game.

---

## 📦 Phụ thuộc

| Thư viện | Phiên bản tối thiểu | Mục đích |
|---|---|---|
| `pygame` | ≥ 2.5.0 | Cửa sổ, render, sự kiện, âm thanh |
| `pymunk` | ≥ 6.6.0 | Động cơ vật lý 2D (Chipmunk wrapper) |
| `numpy` | ≥ 1.24.0 | Xử lý mảng số |
| `opencv-python` | ≥ 4.9.0 | Đọc webcam, xử lý ảnh |
| `mediapipe` | ≥ 0.10.0 | Hand Landmarker Tasks API |

---

## 📄 Giấy phép

Phát hành theo giấy phép **MIT**. Xem file [LICENSE](LICENSE) để biết thêm chi tiết.
