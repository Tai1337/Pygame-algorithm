# src/pathfinding/pathfinder.py

import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UILabel
import src.config as config

from .pathfinding_algorithms import ALGORITHM_MAP, ALGORITHM_INFO
# QLearningAgent đã được xóa import

class PathFinder:
    def __init__(self, floor_block_data, ui_manager, player, point_manager):
        self.tile_size = config.TILE_SIZE
        self.grid = self._create_grid(floor_block_data)
        self.rows = len(self.grid)
        self.cols = len(self.grid[0]) if self.rows > 0 else 0
        
        self.ui_manager = ui_manager
        self.player = player
        self.point_manager = point_manager
        
        self.screen_width = config.SCREEN_WIDTH
        self.screen_height = config.SCREEN_HEIGHT
        
        self.input_active = False
        
        self.algorithms = list(ALGORITHM_MAP.keys())
        self.algorithm_details = {} 

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

    def _path_to_actions(self, path_nodes):
        actions = []
        if not path_nodes or len(path_nodes) < 2:
            return []
        for i in range(len(path_nodes) - 1):
            current_node = path_nodes[i]
            next_node = path_nodes[i+1]
            dr, dc = next_node[0] - current_node[0], next_node[1] - current_node[1]
            if dr == -1: actions.append('W')
            elif dr == 1: actions.append('S')
            elif dc == -1: actions.append('A')
            elif dc == 1: actions.append('D')
        return actions

    def pixel_to_grid(self, x, y):
        row = y // self.tile_size
        col = x // self.tile_size
        return int(row), int(col)

    # THAY ĐỔI HÀM TÍNH GIÁ
    def calculate_taxi_fare(self, path_length, visited_count):
        if path_length <= 0: # Không tìm thấy đường
            return float('inf')
        
        num_moves = path_length - 1
        if num_moves < 0: # Trường hợp path_length = 0 (không nên xảy ra nếu kiểm tra path_length <=0 ở trên)
            num_moves = 0

        # Công thức tính giá mới
        price = config.TAXI_BASE_FARE + \
                (visited_count * config.TAXI_COST_PER_VISITED_NODE) + \
                (num_moves * config.TAXI_COST_PER_MOVE)
        
        # Áp dụng giá cước tối thiểu nếu tìm thấy đường
        if path_length > 0 : # path_length = 1 nghĩa là đã ở đích, vẫn tính phí
             price = max(price, config.TAXI_MIN_FARE_IF_PATH_FOUND)
             
        return int(round(price)) # Làm tròn đến số nguyên gần nhất

    def enable_input(self):
        # ... (Phần đầu hàm giữ nguyên) ...
        if self.input_active: return
        if not self.point_manager.is_visible or not self.point_manager.current_point_center:
            print("PathFinder: Không có điểm đến, không thể mở UI chọn thuật toán.")
            return

        self.input_active = True
        if self.error_label: self.error_label.set_text("") 
        self.algorithm_details.clear()

        self.title_label = UILabel(
            relative_rect=pygame.Rect((self.screen_width - 400) // 2, 50, 400, 40),
            text="Chọn Gói Cước Taxi", # Có thể đổi tiêu đề nếu muốn
            manager=self.ui_manager, object_id="#pathfinder_title_label"
        )
        button_width = 420 
        button_height = 50
        button_spacing = 10 
        start_y = self.title_label.relative_rect.bottom + 20
        start_pos_pixels = self.player.rect.center
        goal_pos_pixels = self.point_manager.current_point_center

        if not goal_pos_pixels: 
            # ... (Xử lý lỗi không có điểm đến, tạo nút Đóng)
            if self.error_label: self.error_label.set_text("Lỗi: Không xác định được điểm đến.")
            self.title_label.set_text("Lỗi: Không có điểm đến cho Taxi")
            cancel_button_rect = pygame.Rect((self.screen_width - button_width) // 2, start_y, button_width, button_height)
            self.cancel_button = UIButton(relative_rect=cancel_button_rect, text="Đóng", manager=self.ui_manager, object_id="#pathfinder_cancel_button")
            return

        start_row, start_col = self.pixel_to_grid(*start_pos_pixels)
        goal_row, goal_col = self.pixel_to_grid(*goal_pos_pixels)

        if not self._is_valid_position(start_row, start_col) or \
           not self._is_valid_position(goal_row, goal_col):
            # ... (Xử lý lỗi vị trí không hợp lệ, tạo nút Đóng)
            msg = "Vị trí bắt đầu hoặc kết thúc không hợp lệ cho Taxi."
            self.title_label.set_text("Lỗi Vị Trí Taxi")
            if self.error_label: self.error_label.set_text(msg)
            else: print(f"PathFinder UI Error: {msg}")
            cancel_button_rect = pygame.Rect((self.screen_width - button_width) // 2, start_y, button_width, button_height)
            self.cancel_button = UIButton(relative_rect=cancel_button_rect, text="Đóng", manager=self.ui_manager, object_id="#pathfinder_cancel_button")
            return


        for i, algo_name in enumerate(self.algorithms):
            algorithm_func = ALGORITHM_MAP.get(algo_name)
            path_nodes, visited_count = [], 0
            display_text_suffix = "Đang xử lý..."
            is_button_enabled = False
            exception_that_occurred_name = None
            current_algo_details = {'price': float('inf'), 'length': 0, 'visited': 0, 'path_nodes': []}

            if callable(algorithm_func):
                try:
                    if algo_name == "Backtracking": 
                         path_nodes, visited_count = algorithm_func(self.grid, (start_row, start_col), (goal_row, goal_col), 
                                                                    max_depth_factor=config.BACKTRACKING_MAX_DEPTH_FACTOR,
                                                                    max_calls_factor=config.BACKTRACKING_MAX_CALLS_FACTOR)
                    elif algo_name == "BEAM_SEARCH":
                         path_nodes, visited_count = algorithm_func(self.grid, (start_row, start_col), (goal_row, goal_col), 
                                                                    beam_width=config.BEAM_SEARCH_WIDTH_DEFAULT)
                    else: 
                        path_nodes, visited_count = algorithm_func(self.grid, (start_row, start_col), (goal_row, goal_col))
                    
                    if display_text_suffix == "Đang xử lý...":
                        if not path_nodes:
                            display_text_suffix = f"Không tìm thấy đường (Duyệt: {visited_count} ô)"
                except Exception as e_details: 
                    print(f"Lỗi khi chạy thử thuật toán {algo_name}: {e_details}")
                    exception_that_occurred_name = type(e_details).__name__ 
                    display_text_suffix = f"Lỗi: {exception_that_occurred_name}"
                
                current_algo_details['visited'] = visited_count
                if path_nodes: 
                    path_length = len(path_nodes)
                    current_algo_details['length'] = path_length
                    current_algo_details['path_nodes'] = path_nodes 
                    
                    # SỬ DỤNG HÀM TÍNH GIÁ MỚI
                    taxi_price = self.calculate_taxi_fare(path_length, visited_count)
                    current_algo_details['price'] = taxi_price
                    
                    num_moves = path_length - 1 if path_length > 0 else 0
                    display_text_suffix = f"Giá: {taxi_price} (Dài: {num_moves}, Duyệt: {visited_count} ô)"
                    is_button_enabled = True
                # else: display_text_suffix đã được set
            else: 
                display_text_suffix = "Lỗi cấu hình hàm"
            
            self.algorithm_details[algo_name] = current_algo_details
            button_text = f"{algo_name} | {display_text_suffix}"
            button_rect = pygame.Rect((self.screen_width - button_width) // 2, start_y + i * (button_height + button_spacing), button_width, button_height)
            button = UIButton(relative_rect=button_rect, text=button_text, manager=self.ui_manager, object_id=f"#algo_button_{i}")
            if not is_button_enabled:
                button.disable()
            self.algorithm_buttons.append(button)

        # ... (Phần tạo nút Hủy và các Label giữ nguyên) ...
        cancel_button_y = start_y + len(self.algorithms) * (button_height + button_spacing)
        cancel_button_rect = pygame.Rect((self.screen_width - button_width) // 2, cancel_button_y, button_width, button_height)
        self.cancel_button = UIButton(relative_rect=cancel_button_rect, text="Hủy", manager=self.ui_manager, object_id="#pathfinder_cancel_button")

        info_label_y = cancel_button_rect.bottom + 15
        self.info_label = UILabel(
            relative_rect=pygame.Rect((self.screen_width - 600)//2, info_label_y, 600, 60),
            text="Di chuột qua gói cước để xem thông tin chi tiết.", manager=self.ui_manager, object_id="#pathfinder_info_label"
        )
        error_label_y = self.info_label.relative_rect.bottom + 5
        self.error_label = UILabel(
            relative_rect=pygame.Rect((self.screen_width - 600)//2, error_label_y, 600, 40),
            text="", manager=self.ui_manager, object_id="#pathfinder_error_label"
        )


    def disable_input(self):
        # ... (Giữ nguyên) ...
        self.input_active = False
        for button in self.algorithm_buttons: button.kill()
        self.algorithm_buttons = []
        if self.title_label: self.title_label.kill(); self.title_label = None
        if self.info_label: self.info_label.kill(); self.info_label = None
        if self.cancel_button: self.cancel_button.kill(); self.cancel_button = None
        if self.error_label: self.error_label.kill(); self.error_label = None

    def handle_input(self, event, point_manager_param_unused_in_signature_but_self_used):
        # ... (Giữ nguyên logic, vì nó đọc thông tin từ self.algorithm_details đã được tính toán đúng) ...
        if not self.input_active: return

        if event.type == pygame.MOUSEMOTION:
            if self.info_label:
                new_info_text = "Di chuột qua gói cước để xem thông tin chi tiết."
                hovered_a_button = False
                for i, button in enumerate(self.algorithm_buttons):
                    if button.check_hover(event.pos, event.type == pygame.MOUSEMOTION) :
                        hovered_a_button = True
                        algo_name = self.algorithms[i]
                        details = self.algorithm_details.get(algo_name)
                        base_info = ALGORITHM_INFO.get(algo_name, "Không có thông tin.")
                        if details:
                            price = details['price']
                            length = details['length']
                            visited = details['visited']
                            num_moves = length - 1 if length > 0 else 0
                            if price != float('inf') and length > 0 :
                                new_info_text = f"{base_info} | Giá: {price} (Dài: {num_moves}, Duyệt: {visited} ô)"
                            # Xử lý trường hợp không tìm thấy đường hoặc lỗi từ text của button
                            elif '|' in button.text:
                                status_from_button = button.text.split('|', 1)[1].strip()
                                new_info_text = f"{base_info} | {status_from_button}"
                            else: # Fallback
                                new_info_text = f"{base_info} | Không tìm thấy đường (Đã duyệt: {visited} ô)"

                        else: new_info_text = base_info
                        break 
                self.info_label.set_text(new_info_text)


        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if self.cancel_button and event.ui_element == self.cancel_button:
                self.disable_input()
                return
            for i, button in enumerate(self.algorithm_buttons):
                if event.ui_element == button:
                    algo_name = self.algorithms[i]
                    details = self.algorithm_details.get(algo_name)
                    if not details or details['price'] == float('inf') or not details['path_nodes']:
                        msg = f"Không thể chọn: {algo_name} (không có đường hoặc lỗi)."
                        if self.error_label: self.error_label.set_text(msg)
                        return
                    cost = details['price']
                    path_nodes_to_use = details['path_nodes'] 
                    if not self.point_manager.is_visible or not self.point_manager.current_point_center:
                        if self.error_label: self.error_label.set_text("Lỗi: Điểm đến đã thay đổi hoặc không còn.")
                        return
                    if not self.player.spend_money(cost):
                        if self.error_label: self.error_label.set_text(f"Không đủ tiền! Cần: {cost}, Bạn có: {self.player.money}")
                        return
                    actions = self._path_to_actions(path_nodes_to_use)
                    self.player.set_actions(actions, path_nodes_to_use) 
                    self.disable_input()
                    return

    def find_path_to_point(self, player_pos_pixels, point_center_pixels):
        algo_name_default = config.DEFAULT_PATHFINDING_ALGORITHM_NAME
        algorithm_func_default = ALGORITHM_MAP.get(algo_name_default)

        if not algorithm_func_default or not point_center_pixels:
             print(f"Lỗi (P-key): Không tìm thấy hàm cho {algo_name_default} hoặc không có điểm đến.")
             return [], None, False 

        start_row_def, start_col_def = self.pixel_to_grid(*player_pos_pixels)
        goal_row_def, goal_col_def = self.pixel_to_grid(*point_center_pixels)

        if not self._is_valid_position(start_row_def, start_col_def) or \
           not self._is_valid_position(goal_row_def, goal_col_def):
            print(f"Debug (P-key): Vị trí không hợp lệ cho {algo_name_default}.")
            return [], None, False
        
        path_nodes_default, visited_count_default = [], 0 
        try:
            if algo_name_default == "Backtracking": 
                path_nodes_default, visited_count_default = algorithm_func_default(
                    self.grid, (start_row_def, start_col_def), (goal_row_def, goal_col_def),
                    max_depth_factor=config.BACKTRACKING_MAX_DEPTH_FACTOR, 
                    max_calls_factor=config.BACKTRACKING_MAX_CALLS_FACTOR
                )
            elif algo_name_default == "BEAM_SEARCH":
                 path_nodes_default, visited_count_default = algorithm_func_default(
                    self.grid, (start_row_def, start_col_def), (goal_row_def, goal_col_def),
                    beam_width=config.BEAM_SEARCH_WIDTH_DEFAULT
                )
            else:
                path_nodes_default, visited_count_default = algorithm_func_default(
                    self.grid, (start_row_def, start_col_def), (goal_row_def, goal_col_def)
                )
        except Exception as e:
            print(f"Lỗi khi chạy {algo_name_default} (P-key): {e}")
            return [], None, False
            
        if not path_nodes_default:
            return [], None, False

        # SỬ DỤNG HÀM TÍNH GIÁ MỚI
        path_length_default = len(path_nodes_default)
        cost_default_taxi = self.calculate_taxi_fare(path_length_default, visited_count_default)
        
        if cost_default_taxi == float('inf'):
            return [], None, False

        if not self.player.spend_money(cost_default_taxi):
            print(f"Debug (P-key): Không đủ tiền cho {algo_name_default}. Cần: {cost_default_taxi}, Có: {self.player.money}")
            return [], None, False
        
        actions = self._path_to_actions(path_nodes_default)
        return actions, path_nodes_default, True

    def draw(self, surface):
        pass

    def update(self, delta_time):
        pass