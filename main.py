import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    from src.game import Game
except ImportError as e:
    print("Lỗi ImportError: Không thể import lớp Game từ src.game")
    print("Hãy đảm bảo rằng bạn đang chạy main.py từ thư mục gốc của dự án (PYGAME-ALGORITHM-MASTER),")
    print("và thư mục 'src' với tệp 'game.py' tồn tại đúng vị trí.")
    print(f"Chi tiết lỗi: {e}")
    sys.exit(1)


def main():
    """Hàm chính để khởi tạo và chạy game."""
    print("Khởi tạo Game instance...")
    game = Game()
    print("Bắt đầu chạy Game...")
    game.run()

if __name__ == "__main__":
    main()