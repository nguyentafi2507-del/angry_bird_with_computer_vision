"""
src/game/level.py
Định nghĩa các màn chơi và các hàm dựng cấu trúc phòng thủ (gỗ) tái sử dụng được:
open_flat, closed_flat, horizontal_pile, vertical_pile.

Ghi chú: README gốc mô tả 12 level (0-11). Ở bản khởi tạo này mình dựng sẵn
4 level (0-3) làm nền, đúng chuẩn cấu trúc để bạn/mình bổ sung tiếp 8 level
còn lại theo đúng hướng dẫn trong "Hướng Dẫn Thêm Màn Chơi Mới" của README.
"""
from src.game.pig import Pig
from src.game.obstacle import Obstacle
from config import settings


class Level:
    # Toàn bộ toạ độ x trong các hàm build_N bên dưới được THIẾT KẾ CHO khung
    # game rộng 1200px. Nếu FRAME_W thay đổi (ví dụ khi chia lại tỉ lệ
    # game/camera), mọi vị trí sẽ tự dịch theo (qua self.sx()) để heo/gỗ vẫn
    # nằm đúng khoảng cách tương đối so với tường phải, không bị lọt ra ngoài
    # khung hình hay lẫn vào tường.
    DESIGN_WIDTH = 1200

    def __init__(self, space, level_number):
        self.space = space
        self.level_number = level_number
        self._shift = settings.FRAME_W - self.DESIGN_WIDTH

        self.pigs = []
        self.obstacles = []
        self.number_of_birds = settings.DEFAULT_NUMBER_OF_BIRDS  # mặc định theo settings.py

        self.one_star = 10000
        self.two_star = 20000
        self.three_star = 30000

        build_fn = getattr(self, f"build_{level_number}", None)
        if build_fn is None:
            raise ValueError(f"Level {level_number} chưa được định nghĩa.")
        build_fn()

    def sx(self, x):
        """Dịch toạ độ x theo độ chênh lệch giữa FRAME_W thực tế và
        DESIGN_WIDTH (1200) mà các level bên dưới được thiết kế theo."""
        return x + self._shift

    # ------------------------------------------------------------------
    # Helper: các cấu trúc phòng thủ tái sử dụng
    # ------------------------------------------------------------------
    def open_flat(self, x, y, count, spacing=70, width=20, height=100):
        """Các cột gỗ đứng riêng lẻ, không có nóc (dễ đổ)."""
        for i in range(count):
            pos = (x + i * spacing, y + height / 2)
            self.obstacles.append(Obstacle(self.space, pos, width, height))

    def closed_flat(self, x, y, count, spacing=70, width=20, height=100, roof_height=20):
        """Giống open_flat nhưng có 1 dầm ngang làm nóc phía trên."""
        for i in range(count):
            pos = (x + i * spacing, y + height / 2)
            self.obstacles.append(Obstacle(self.space, pos, width, height))
        roof_width = spacing * (count - 1) + width + 10
        roof_pos = (x + spacing * (count - 1) / 2, y + height + roof_height / 2)
        self.obstacles.append(Obstacle(self.space, roof_pos, roof_width, roof_height))

    def horizontal_pile(self, x, y, count, width=90, height=20, gap=4):
        """Xếp các dầm gỗ nằm ngang chồng lên nhau (tháp ngang)."""
        for i in range(count):
            pos = (x, y + i * (height + gap) + height / 2)
            self.obstacles.append(Obstacle(self.space, pos, width, height))

    def vertical_pile(self, x, y, count, width=20, height=100, gap=4):
        """Xếp các cột gỗ đứng cạnh nhau tạo thành tường dày."""
        for i in range(count):
            pos = (x + i * (width + gap), y + height / 2)
            self.obstacles.append(Obstacle(self.space, pos, width, height))

    # ------------------------------------------------------------------
    # LEVEL 0: màn nhập môn - 1 heo trần, không gỗ
    # ------------------------------------------------------------------
    def build_0(self):
        self.pigs.append(Pig((self.sx(700), 60), self.space))
        self.one_star = 5000
        self.two_star = 9000
        self.three_star = 13000

    # ------------------------------------------------------------------
    # LEVEL 1: heo đứng sau 1 hàng cột gỗ mở (open_flat)
    # ------------------------------------------------------------------
    def build_1(self):
        self.open_flat(self.sx(650), 20, 2, spacing=80)
        self.pigs.append(Pig((self.sx(820), 60), self.space))
        self.one_star = 8000
        self.two_star = 14000
        self.three_star = 20000

    # ------------------------------------------------------------------
    # LEVEL 2: hộp kín (closed_flat) bảo vệ 2 heo
    # ------------------------------------------------------------------
    def build_2(self):
        self.closed_flat(self.sx(700), 20, 3, spacing=90)
        self.pigs.append(Pig((self.sx(790), 70), self.space))
        self.pigs.append(Pig((self.sx(880), 70), self.space))
        self.one_star = 12000
        self.two_star = 20000
        self.three_star = 28000

    # ------------------------------------------------------------------
    # LEVEL 3: tháp dọc (vertical_pile) + tháp ngang (horizontal_pile) + 3 heo
    # ------------------------------------------------------------------
    def build_3(self):
        self.vertical_pile(self.sx(750), 20, 4)
        self.horizontal_pile(self.sx(950), 20, 3)
        self.pigs.append(Pig((self.sx(790), 130), self.space))
        self.pigs.append(Pig((self.sx(950), 130), self.space))
        self.pigs.append(Pig((self.sx(1050), 60), self.space))
        self.one_star = 18000
        self.two_star = 28000
        self.three_star = 40000

    # ------------------------------------------------------------------
    # Trạng thái level
    # ------------------------------------------------------------------
    def pigs_remaining(self):
        return sum(1 for p in self.pigs if p.alive)

    def is_won(self):
        return self.pigs_remaining() == 0

    def compute_stars(self, score):
        """Tính số sao (0-3) đạt được dựa trên điểm số và 3 ngưỡng
        one_star/two_star/three_star đã định nghĩa ở mỗi build_N()."""
        if score >= self.three_star:
            return 3
        if score >= self.two_star:
            return 2
        if score >= self.one_star:
            return 1
        return 0

    def cleanup(self):
        for pig in self.pigs:
            if pig.alive:
                pig.kill()
        for obs in self.obstacles:
            if obs.alive:
                obs.destroy()


TOTAL_LEVELS = 4  # cập nhật số này khi thêm build_4, build_5, ...