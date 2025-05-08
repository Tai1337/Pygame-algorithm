# pathfinder.py

import pygame
import heapq
from math import sqrt
import pygame_gui
from pygame_gui.elements import UIButton, UILabel
# from pygame_gui.core import ObjectID # Không cần thiết nếu không dùng ObjectID trực tiếp

from pathfinding_algorithms import ALGORITHM_MAP, ALGORITHM_INFO, ALGORITHM_COSTS, DEFAULT_PATHFINDING_ALGORITHM_NAME, DEFAULT_PATHFINDING_COST

# Không cần định nghĩa màu ở đây nữa, chúng được quản lý bởi theme.json

class PathFinder:
    def __init__(self, floor_block_data, tile_size, ui_manager, player):
        self.tile_size = tile_size
        self.grid = self._create_grid(floor_block_data)
        self.rows = len(self.grid)
        self.cols = len(self.grid[0]) if self.rows > 0 else 0
        self.ui_manager = ui_manager
        self.player = player # player được truyền vào và lưu trữ
        self.input_active = False
        self.actions = []
        self.error_message = ""
        # self.font không cần thiết nếu dùng theme của pygame_gui

        self.algorithms = list(ALGORITHM_MAP.keys())
        # self.theme không cần lấy và lưu trữ nếu không set programmatically nữa

        # UI elements
        self.algorithm_buttons = []
        self.info_label = None
        self.cancel_button = None
        self.error_label = None
        self.title_label = None

    def _create_grid(self, floor_block_data):
        grid = []
        for r_idx, row_data_val in enumerate(floor_block_data):
            grid_row = []
            for c_idx, value_val in enumerate(row_data_val):
                val_str = value_val.strip()
                is_blocked = val_str != '-1' and val_str != ''
                grid_row.append(1 if is_blocked else 0)
            grid.append(grid_row)
        return grid

    def _is_valid_position(self, row, col):
        return 0 <= row < self.rows and 0 <= col < self.cols and self.grid[row][col] == 0

    def _path_to_actions(self, path):
        actions = []
        if not path or len(path) < 2:
            return []
        for i in range(len(path) - 1):
            current = path[i]
            next_pos = path[i+1]
            dr, dc = next_pos[0] - current[0], next_pos[1] - current[1]
            if dr == -1: actions.append('W')
            elif dr == 1: actions.append('S')
            elif dc == -1: actions.append('A')
            elif dc == 1: actions.append('D')
        return actions

    def pixel_to_grid(self, x, y):
        row, col = y // self.tile_size, x // self.tile_size
        return row, col

    def enable_input(self):
        self.input_active = True
        if self.error_label: self.error_label.set_text("")

        self.title_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(200, 50, 400, 40),
            text="Chọn Gói Cước Taxi (Thuật Toán)",
            manager=self.ui_manager,
            object_id="#pathfinder_title_label" # Khớp với theme.json
        )
        # Không cần set màu và rebuild ở đây nữa

        button_width = 280
        button_height = 50
        button_spacing = 15
        start_y = 120

        for i, algo_name in enumerate(self.algorithms):
            cost = ALGORITHM_COSTS.get(algo_name, "N/A")
            button_text = f"{algo_name} (Giá: {cost})"
            # Sử dụng object_id chung "button" từ theme, hoặc ID cụ thể nếu có trong theme
            button = UIButton(
                relative_rect=pygame.Rect(
                    (800 - button_width) // 2,
                    start_y + i * (button_height + button_spacing),
                    button_width,
                    button_height
                ),
                text=button_text,
                manager=self.ui_manager,
                object_id=f"#algo_button_{i}" # Có thể định nghĩa từng ID này trong theme
                                             # hoặc để nó kế thừa từ "button" chung
            )
            self.algorithm_buttons.append(button)

        self.cancel_button = UIButton(
            relative_rect=pygame.Rect(
                (800 - button_width) // 2,
                start_y + len(self.algorithms) * (button_height + button_spacing),
                button_width,
                button_height
            ),
            text="Hủy",
            manager=self.ui_manager,
            object_id="#pathfinder_cancel_button" # Hoặc dùng style "button" chung
        )

        info_label_y = start_y + (len(self.algorithms) + 1) * (button_height + button_spacing) + 10
        self.info_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(100, info_label_y, 600, 60),
            text="Di chuột qua gói cước để xem thông tin.",
            manager=self.ui_manager,
            object_id="#pathfinder_info_label" # Khớp với theme.json
        )

        error_label_y = info_label_y + 70
        self.error_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(100, error_label_y, 600, 40),
            text="",
            manager=self.ui_manager,
            object_id="#pathfinder_error_label" # Khớp với theme.json
        )

    def disable_input(self):
        self.input_active = False
        for button in self.algorithm_buttons: button.kill()
        self.algorithm_buttons = []
        if self.title_label: self.title_label.kill(); self.title_label = None
        if self.info_label: self.info_label.kill(); self.info_label = None
        if self.cancel_button: self.cancel_button.kill(); self.cancel_button = None
        if self.error_label: self.error_label.kill(); self.error_label = None

    def handle_input(self, event, point_manager): # player đã là self.player
        if not self.input_active:
            return

        # ui_manager.process_events(event) đã được gọi ở main

        if event.type == pygame.MOUSEMOTION:
            for i, button in enumerate(self.algorithm_buttons):
                if button.check_hover(event.pos, event.type == pygame.MOUSEMOTION) and self.info_label:
                    algo_name = self.algorithms[i]
                    cost = ALGORITHM_COSTS.get(algo_name, "N/A")
                    info_text = ALGORITHM_INFO.get(algo_name, "Không có thông tin.") + f" | Giá: {cost}"
                    self.info_label.set_text(info_text) # Text thay đổi, màu giữ nguyên từ theme

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.cancel_button:
                self.disable_input()
                return

            for i, button in enumerate(self.algorithm_buttons):
                if event.ui_element == button:
                    algo_name = self.algorithms[i]
                    algorithm_func = ALGORITHM_MAP.get(algo_name)
                    cost = ALGORITHM_COSTS.get(algo_name, 0)

                    if not algorithm_func:
                        msg = f"Lỗi: Không tìm thấy hàm cho thuật toán {algo_name}"
                        if self.error_label: self.error_label.set_text(msg)
                        print(f"Debug: {msg}")
                        return

                    if not point_manager.is_visible or not point_manager.current_point_center:
                        msg = "Không có điểm đích để tìm đường."
                        if self.error_label: self.error_label.set_text(msg)
                        return

                    if not self.player.spend_money(cost):
                        msg = f"Không đủ tiền! Cần: {cost}, Bạn có: {self.player.money}"
                        if self.error_label: self.error_label.set_text(msg)
                        return

                    start_pos_pixels = self.player.rect.center
                    goal_pos_pixels = point_manager.current_point_center
                    start_row, start_col = self.pixel_to_grid(*start_pos_pixels)
                    goal_row, goal_col = self.pixel_to_grid(*goal_pos_pixels)

                    if not self._is_valid_position(start_row, start_col) or \
                       not self._is_valid_position(goal_row, goal_col):
                        msg = "Vị trí bắt đầu hoặc kết thúc không hợp lệ."
                        if self.error_label: self.error_label.set_text(msg)
                        self.player.add_money(cost) # Hoàn tiền
                        return

                    path_nodes = algorithm_func(self.grid, (start_row, start_col), (goal_row, goal_col))

                    if path_nodes:
                        self.actions = self._path_to_actions(path_nodes)
                        self.player.set_actions(self.actions)
                        self.disable_input()
                    else:
                        msg = f"{algo_name} không tìm thấy đường đi."
                        if self.error_label: self.error_label.set_text(msg)
                        # Tùy chọn hoàn tiền ở đây nếu muốn
                        # self.player.add_money(cost)
                    return

    def find_path_to_point(self, player_pos_pixels, point_center_pixels):
        if point_center_pixels is None:
            print("Debug: (find_path_to_point) Không có điểm đích.")
            return [], False

        cost = DEFAULT_PATHFINDING_COST
        algo_name = DEFAULT_PATHFINDING_ALGORITHM_NAME
        algorithm_func = ALGORITHM_MAP.get(algo_name)

        if not algorithm_func:
            print(f"Lỗi: (find_path_to_point) Không tìm thấy hàm cho thuật toán mặc định {algo_name}")
            return [], False

        if not self.player.spend_money(cost):
            print(f"Debug: (find_path_to_point) Không đủ tiền cho {algo_name}. Cần: {cost}, Có: {self.player.money}")
            return [], False

        start_row, start_col = self.pixel_to_grid(*player_pos_pixels)
        goal_row, goal_col = self.pixel_to_grid(*point_center_pixels)

        if not self._is_valid_position(start_row, start_col) or \
           not self._is_valid_position(goal_row, goal_col):
            print(f"Debug: (find_path_to_point) Vị trí không hợp lệ.")
            self.player.add_money(cost) # Hoàn tiền
            return [], False

        path_nodes = algorithm_func(self.grid, (start_row, start_col), (goal_row, goal_col))

        if path_nodes:
            actions = self._path_to_actions(path_nodes)
            return actions, True
        else:
            print(f"Debug: (find_path_to_point) {algo_name} không tìm thấy đường đi.")
            # self.player.add_money(cost) # Tùy chọn hoàn tiền
            return [], False

    def draw(self, surface):
        # UIManager sẽ vẽ các element này khi self.input_active là True
        pass

    def update(self, delta_time):
        # UIManager sẽ cập nhật các element này
        pass