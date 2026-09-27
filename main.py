"""
main.py
Điểm khởi chạy chính của trò chơi Angry Birds (giai đoạn: điều khiển bằng chuột,
chưa tích hợp Computer Vision). Chạy: python main.py
"""
from src.game.game_engine import GameEngine


def main():
    engine = GameEngine()
    engine.run()


if __name__ == "__main__":
    main()