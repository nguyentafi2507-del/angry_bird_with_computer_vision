"""
src/utils/vector2d.py
Các hàm tiện ích tính toán vector 2D dùng chung (khoảng cách, góc, giới hạn độ lớn).
"""
import math


def distance(p1, p2):
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def sub(p1, p2):
    """p1 - p2"""
    return (p1[0] - p2[0], p1[1] - p2[1])


def magnitude(v):
    return math.hypot(v[0], v[1])


def normalize(v):
    m = magnitude(v)
    if m == 0:
        return (0.0, 0.0)
    return (v[0] / m, v[1] / m)


def clamp_magnitude(v, max_len):
    m = magnitude(v)
    if m <= max_len or m == 0:
        return v
    scale = max_len / m
    return (v[0] * scale, v[1] * scale)


def angle_between(p1, p2):
    """Góc (radian) của vector từ p1 tới p2."""
    return math.atan2(p2[1] - p1[1], p2[0] - p1[0])