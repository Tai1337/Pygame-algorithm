
import csv
import os
import pygame 
import sys   


def load_csv(filepath):
    data = []
    if not os.path.exists(filepath):
        print(f"Lỗi: Không tìm thấy file CSV '{filepath}'")
        
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