"""
src/vision/coordinate_mapper.py
Tính toán điểm điều khiển, khoảng cách kéo, góc & vector vận tốc từ 21 điểm
landmark thô của MediaPipe.

Chỉ số landmark bàn tay theo chuẩn MediaPipe Hand (0-20):
    4  = đầu ngón CÁI (THUMB_TIP)
    8  = đầu ngón TRỎ (INDEX_FINGER_TIP)
(xem đầy đủ 21 điểm tại tài liệu MediaPipe Hand Landmarker)
"""
import math

THUMB_TIP = 4
INDEX_TIP = 8


def _to_pixel(landmark, frame_w, frame_h):
    return landmark.x * frame_w, landmark.y * frame_h


def compute_control_point(hand_landmarks, frame_w, frame_h):
    """Điểm điều khiển = trung điểm giữa đầu ngón cái và đầu ngón trỏ,
    quy đổi từ toạ độ chuẩn hoá (0..1) sang toạ độ pixel của khung game
    (frame_w x frame_h, mặc định = settings.FRAME_W/FRAME_H).
    Trả về (x, y) hoặc None nếu thiếu landmark.
    """
    if hand_landmarks is None or len(hand_landmarks) <= INDEX_TIP:
        return None

    tx, ty = _to_pixel(hand_landmarks[THUMB_TIP], frame_w, frame_h)
    ix, iy = _to_pixel(hand_landmarks[INDEX_TIP], frame_w, frame_h)
    return ((tx + ix) / 2.0, (ty + iy) / 2.0)


def pinch_distance_px(hand_landmarks, frame_w, frame_h):
    """Khoảng cách (px) giữa đầu ngón cái và đầu ngón trỏ - dùng để so với
    GRAB_ENTER_THRESHOLD / GRAB_EXIT_THRESHOLD trong gesture_detector.py.
    Trả về None nếu thiếu landmark (không thấy tay).
    """
    if hand_landmarks is None or len(hand_landmarks) <= INDEX_TIP:
        return None

    tx, ty = _to_pixel(hand_landmarks[THUMB_TIP], frame_w, frame_h)
    ix, iy = _to_pixel(hand_landmarks[INDEX_TIP], frame_w, frame_h)
    return math.hypot(ix - tx, iy - ty)


def get_finger_tips(hand_landmarks, frame_w, frame_h):
    """Trả về ((thumb_x, thumb_y), (index_x, index_y)) theo pixel - dùng để
    vẽ 2 chấm ngón tay trực tiếp lên màn hình GAME (không chỉ panel camera),
    giúp người chơi thấy rõ vị trí đang điều khiển ná.
    Trả về None nếu thiếu landmark (không thấy tay).
    """
    if hand_landmarks is None or len(hand_landmarks) <= INDEX_TIP:
        return None

    thumb = _to_pixel(hand_landmarks[THUMB_TIP], frame_w, frame_h)
    index = _to_pixel(hand_landmarks[INDEX_TIP], frame_w, frame_h)
    return thumb, index


def get_all_points_px(hand_landmarks, frame_w, frame_h):
    """Trả về danh sách 21 điểm (x, y) theo pixel - dùng để vẽ khung xương
    bàn tay lên camera panel (debug/overlay). Trả về [] nếu không có tay."""
    if hand_landmarks is None:
        return []
    return [_to_pixel(lm, frame_w, frame_h) for lm in hand_landmarks]