# src/utils/file_handler.py
import csv
import os
import pygame # Cần thiết nếu bạn xử lý lỗi pygame.quit() ở đây
import sys   # Cần thiết nếu bạn xử lý lỗi sys.exit() ở đây

# Hàm đọc dữ liệu CSV
def load_csv(filepath):
    data = []
    if not os.path.exists(filepath):
        print(f"Lỗi: Không tìm thấy file CSV '{filepath}'")
        # Cân nhắc việc raise Exception thay vì quit/exit trực tiếp từ hàm tiện ích
        # để cho phép hàm gọi xử lý lỗi một cách linh hoạt hơn.
        # Ví dụ: raise FileNotFoundError(f"Không tìm thấy file CSV '{filepath}'")
        pygame.quit()
        sys.exit()
    try:
        with open(filepath, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row_data in reader:
                data.append(list(row_data))
    except Exception as e:
        print(f"Lỗi khi đọc file CSV '{filepath}': {e}")
        pygame.quit()
        sys.exit()
    return data