# Game Giao Hàng & Mini-games (PYGAME-ALGORITHM-MASTER)

Một trò chơi phiêu lưu 2D được xây dựng bằng Pygame (Python), kết hợp yếu tố giao hàng trong một thế giới bản đồ rộng lớn, nơi người chơi phải hoàn thành các nhiệm vụ và thử thách bản thân qua nhiều mini-game đa dạng. Mỗi mini-game được thiết kế để áp dụng hoặc minh họa các thuật toán khác nhau.


## Tính năng

### Game chính:
* **Thế giới mở:** Di chuyển tự do trên bản đồ lớn được thiết kế từ file CSV.
* **Nhiệm vụ giao hàng:** Thu thập các "điểm" (items/points) trên bản đồ.
* **Hệ thống kinh tế:** Người chơi có tiền, có thể kiếm thêm hoặc bị trừ khi tương tác với các yếu tố trong game (ví dụ: giải AI cho puzzle, phạt khi thua mini-game).
* **Thời gian giới hạn:** Hoàn thành mục tiêu trước khi hết giờ.
* **Camera:** Theo dõi người chơi, tạo cảm giác khám phá.
* **Pathfinding "Taxi":** Người chơi có thể sử dụng thuật toán tìm đường (A\*, Beam Search, Backtracking) để di chuyển tự động đến một điểm đã chọn (có tính phí).
* **Giao diện người dùng:** Sử dụng `pygame_gui` để hiển thị thông tin (thời gian, tiền, vật phẩm) và các cửa sổ tương tác.

### Mini-games tích hợp:
* **8-Puzzle:** Giải đố trí tuệ sắp xếp các ô số. Có tùy chọn cho AI giải tự động (UCS) với một khoản phí.
* **Rắn Săn Mồi (Snake Game):** Điều khiển rắn ăn mồi, tránh tường và thân mình. Có thể bị phạt tiền khi va chạm.
* **Chuột và Phô Mát (Mouse & Cheese Maze):** AI (Q-Learning) điều khiển chuột tìm đường trong mê cung để ăn phô mai. Người chơi có thể "huấn luyện" AI bằng cách trả phí.
* **Cờ Caro (Caro Game):** Đánh cờ caro với AI (sử dụng Minimax hoặc các thuật toán khác).
* **Cửa sổ chọn Mini-game:** Cho phép người chơi chọn mini-game muốn thử thách khi đến các điểm đặc biệt.

## Công nghệ sử dụng
* **Ngôn ngữ:** Python 3.x
* **Thư viện chính:** Pygame
* **Giao diện người dùng:** Pygame GUI
* **Khác:** `numpy` (có thể được sử dụng trong một số thuật toán AI), `csv` (đọc dữ liệu bản đồ).

## Cài đặt

1.  **Clone repository:**
    ```bash
    git clone https://github.com/Tai1337/Pygame-algorithm.git


2.  **Tạo môi trường ảo (khuyến khích):**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Cài đặt các thư viện cần thiết:**
 
    pygame
    pygame_gui
    numpy 
    

## Cách chạy trò chơi

Sau khi cài đặt, chạy file `main.py` từ thư mục gốc của dự án:
```bash
python main.py
