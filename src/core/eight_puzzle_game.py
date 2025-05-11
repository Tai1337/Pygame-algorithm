# src/core/eight_puzzle_game.py
import pygame
import random
import heapq
import src.config as config
import pygame_gui

class EightPuzzleGame:
    def __init__(self, ui_manager):
        self.screen_width = config.SCREEN_WIDTH
        self.screen_height = config.SCREEN_HEIGHT
        self.ui_manager = ui_manager

        # ... (khởi tạo font như cũ) ...
        try:
            self.font = pygame.font.Font(None, 50)
            self.message_font = pygame.font.Font(None, 36)
        except pygame.error as e:
            print(f"Lỗi khởi tạo font cho 8-Puzzle: {e}")
            self.font = pygame.font.SysFont(None, 50)
            self.message_font = pygame.font.SysFont(None, 36)

        self.solved_board = [[1, 2, 3], [4, 5, 6], [7, 8, 0]]
        self.board = []
        self.empty_pos = None
        self.is_active = False

        # ... (khởi tạo puzzle_width, puzzle_height, puzzle_rect như cũ) ...
        self.puzzle_width = config.PUZZLE_GRID_SIZE * config.PUZZLE_TILE_SIZE + \
                            (config.PUZZLE_GRID_SIZE - 1) * config.PUZZLE_GAP + \
                            2 * config.PUZZLE_BORDER
        self.puzzle_height = config.PUZZLE_GRID_SIZE * config.PUZZLE_TILE_SIZE + \
                             (config.PUZZLE_GRID_SIZE - 1) * config.PUZZLE_GAP + \
                             2 * config.PUZZLE_BORDER
        
        self.puzzle_rect = pygame.Rect(
            (self.screen_width - self.puzzle_width) // 2,
            (self.screen_height - self.puzzle_height - config.SOLVE_AI_BUTTON_HEIGHT - config.SOLVE_AI_BUTTON_MARGIN_TOP) // 2,
            self.puzzle_width,
            self.puzzle_height
        )
        
        self.win_message = ""
        self.win_message_timer = 0
        self.just_won = False
        self.win_processed_in_main = False
        self.solved_by_ai = False
        self.solve_ai_button = None

        # Thuộc tính cho việc giải từng bước của AI
        self.is_ai_solving_step_by_step = False
        self.ai_solution_path_states = [] # Danh sách các trạng thái board (tuples)
        self.ai_solution_current_step_index = 0
        self.ai_step_timer = 0.0


    def _find_empty(self): # Cần cập nhật self.empty_pos mỗi khi self.board thay đổi
        for r in range(config.PUZZLE_GRID_SIZE):
            for c in range(config.PUZZLE_GRID_SIZE):
                if self.board[r][c] == 0:
                    self.empty_pos = (r,c) # Cập nhật trực tiếp
                    return r, c
        return None # Should not happen

    # ... (_is_solvable, _generate_solvable_puzzle như cũ) ...
    def _is_solvable(self, flat_board_no_zero):
        inversions = 0
        for i in range(len(flat_board_no_zero)):
            for j in range(i + 1, len(flat_board_no_zero)):
                if flat_board_no_zero[i] > flat_board_no_zero[j]:
                    inversions += 1
        return inversions % 2 == 0

    def _generate_solvable_puzzle(self):
        numbers = list(range(1, config.PUZZLE_GRID_SIZE * config.PUZZLE_GRID_SIZE))
        while True:
            random.shuffle(numbers)
            if self._is_solvable(numbers):
                flat_board_with_zero = numbers + [0]
                new_board = []
                for i in range(config.PUZZLE_GRID_SIZE):
                    row = flat_board_with_zero[i * config.PUZZLE_GRID_SIZE : (i + 1) * config.PUZZLE_GRID_SIZE]
                    new_board.append(row)
                self.board = new_board
                self._find_empty() # Cập nhật empty_pos
                if self.board != self.solved_board:
                    break
        self.just_won = False
        self.win_processed_in_main = False
        self.solved_by_ai = False
        self.is_ai_solving_step_by_step = False # Reset
        print("8-Puzzle board generated.")


    def start_game(self):
        self._generate_solvable_puzzle()
        self.win_message = ""
        self.win_message_timer = 0
        self.just_won = False
        self.win_processed_in_main = False
        self.solved_by_ai = False
        self.is_ai_solving_step_by_step = False
        self.ai_solution_path_states = []
        self.ai_solution_current_step_index = 0
        self.ai_step_timer = 0.0

        if self.solve_ai_button:
            self.solve_ai_button.kill()
        
        button_rect_x = self.puzzle_rect.centerx - config.SOLVE_AI_BUTTON_WIDTH // 2
        button_rect_y = self.puzzle_rect.bottom + config.SOLVE_AI_BUTTON_MARGIN_TOP
        
        self.solve_ai_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(button_rect_x, button_rect_y, config.SOLVE_AI_BUTTON_WIDTH, config.SOLVE_AI_BUTTON_HEIGHT),
            text=config.SOLVE_AI_BUTTON_TEXT.replace("50", str(config.PUZZLE_SOLVE_COST)),
            manager=self.ui_manager,
            object_id="#solve_ai_puzzle_button"
        )
        self.solve_ai_button.enable()
        self.solve_ai_button.show()
        print("8-Puzzle game variables reset. AI Solve button created.")

    def cleanup_ui(self):
        if self.solve_ai_button:
            self.solve_ai_button.kill()
            self.solve_ai_button = None
        print("8-Puzzle UI cleaned up.")

    # ... (get_tile_at_mouse_pos như cũ) ...
    def get_tile_at_mouse_pos(self, mouse_x, mouse_y):
        if not self.puzzle_rect.collidepoint(mouse_x, mouse_y):
            return None
        local_x = mouse_x - self.puzzle_rect.left - config.PUZZLE_BORDER
        local_y = mouse_y - self.puzzle_rect.top - config.PUZZLE_BORDER
        for r in range(config.PUZZLE_GRID_SIZE):
            for c in range(config.PUZZLE_GRID_SIZE):
                tile_x_start = c * (config.PUZZLE_TILE_SIZE + config.PUZZLE_GAP)
                tile_y_start = r * (config.PUZZLE_TILE_SIZE + config.PUZZLE_GAP)
                tile_clickable_rect = pygame.Rect(tile_x_start, tile_y_start, config.PUZZLE_TILE_SIZE, config.PUZZLE_TILE_SIZE)
                if tile_clickable_rect.collidepoint(local_x, local_y):
                    return r, c
        return None

    def move_tile(self, r, c):
        # Chặn di chuyển nếu AI đang giải hoặc đã giải, hoặc game đã thắng
        if not self.is_active or self.just_won or self.solved_by_ai or self.is_ai_solving_step_by_step:
            return

        er, ec = self.empty_pos
        if (abs(r - er) == 1 and c == ec) or (abs(c - ec) == 1 and r == er):
            self.board[er][ec] = self.board[r][c]
            self.board[r][c] = 0
            self._find_empty() # Cập nhật empty_pos
            if self.check_win():
                self.win_message = "Chiến Thắng 8-Puzzle!"
                self.win_message_timer = 3
                self.just_won = True
                if self.solve_ai_button: self.solve_ai_button.disable()
                print("8-Puzzle solved by player!")

    def check_win(self):
        return self.board == self.solved_board

    # --- A* Algorithm for 8-Puzzle (Trả về danh sách các trạng thái board) ---
    def _board_to_tuple(self, board_list):
        return tuple(tuple(row) for row in board_list)

    def _tuple_to_board(self, board_tuple):
        return [list(row) for row in board_tuple]

    def _find_empty_in_tuple(self, board_tuple): # Tìm ô trống trong tuple (không thay đổi self.empty_pos)
        for r_idx, row_val in enumerate(board_tuple):
            for c_idx, tile_val in enumerate(row_val):
                if tile_val == 0:
                    return r_idx, c_idx
        return None

    # ... (_calculate_heuristic như cũ) ...
    def _calculate_heuristic(self, board_tuple, goal_tuple): # Manhattan distance
        dist = 0
        goal_pos_map = {} 
        if not hasattr(self, '_goal_pos_map_cache'): 
            self._goal_pos_map_cache = {}
            for r_goal in range(config.PUZZLE_GRID_SIZE):
                for c_goal in range(config.PUZZLE_GRID_SIZE):
                    self._goal_pos_map_cache[goal_tuple[r_goal][c_goal]] = (r_goal, c_goal)
        
        for r1 in range(config.PUZZLE_GRID_SIZE):
            for c1 in range(config.PUZZLE_GRID_SIZE):
                tile_val = board_tuple[r1][c1]
                if tile_val != 0:
                    r2, c2 = self._goal_pos_map_cache[tile_val]
                    dist += abs(r1 - r2) + abs(c1 - c2)
        return dist


    def _solve_puzzle_with_a_star(self):
        start_board_tuple = self._board_to_tuple(self.board)
        goal_board_tuple = self._board_to_tuple(self.solved_board)

        if start_board_tuple == goal_board_tuple:
            return [start_board_tuple] # Trả về list chứa trạng thái hiện tại nếu đã giải

        # (f_score, g_score, board_state_tuple)
        open_set = [(self._calculate_heuristic(start_board_tuple, goal_board_tuple), 0, start_board_tuple)]
        heapq.heapify(open_set)

        came_from = {start_board_tuple: None} # predecessor_state
        g_scores = {start_board_tuple: 0}

        max_nodes_to_explore = 50000 # Giới hạn explore
        nodes_explored = 0

        while open_set:
            nodes_explored += 1
            if nodes_explored > max_nodes_to_explore:
                print("A* reached exploration limit for step-by-step.")
                return None

            _, g, current_board_tuple, = heapq.heappop(open_set)

            if current_board_tuple == goal_board_tuple:
                path_of_states = []
                temp_state = current_board_tuple
                while temp_state is not None:
                    path_of_states.append(temp_state)
                    temp_state = came_from.get(temp_state)
                path_of_states.reverse()
                return path_of_states

            empty_r, empty_c = self._find_empty_in_tuple(current_board_tuple)

            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]: # Hướng ô trống di chuyển
                tile_to_move_r, tile_to_move_c = empty_r - dr, empty_c - dc

                if 0 <= tile_to_move_r < config.PUZZLE_GRID_SIZE and \
                   0 <= tile_to_move_c < config.PUZZLE_GRID_SIZE:
                    
                    new_board_list = self._tuple_to_board(current_board_tuple)
                    new_board_list[empty_r][empty_c] = new_board_list[tile_to_move_r][tile_to_move_c]
                    new_board_list[tile_to_move_r][tile_to_move_c] = 0
                    neighbor_board_tuple = self._board_to_tuple(new_board_list)

                    new_g_score = g + 1
                    
                    if new_g_score < g_scores.get(neighbor_board_tuple, float('inf')):
                        came_from[neighbor_board_tuple] = current_board_tuple
                        g_scores[neighbor_board_tuple] = new_g_score
                        h_score = self._calculate_heuristic(neighbor_board_tuple, goal_board_tuple)
                        new_f_score = new_g_score + h_score
                        heapq.heappush(open_set, (new_f_score, new_g_score, neighbor_board_tuple))
        
        print("A* (step-by-step) could not find a solution.")
        return None
    
    def attempt_ai_solve(self):
        if self.just_won or self.solved_by_ai or self.is_ai_solving_step_by_step:
            return

        print("Attempting AI solve (step-by-step)...")
        solution_states = self._solve_puzzle_with_a_star()

        if solution_states and len(solution_states) > 0:
            self.ai_solution_path_states = solution_states
            self.ai_solution_current_step_index = 0
            self.ai_step_timer = 0.0
            self.is_ai_solving_step_by_step = True
            self.solved_by_ai = True # Đánh dấu AI đang giải (hoặc đã giải)
            self.win_message = "AI đang giải..."
            self.win_message_timer = float('inf') # Hiển thị cho đến khi giải xong

            if self.solve_ai_button:
                self.solve_ai_button.disable()
            print(f"AI found a solution with {len(self.ai_solution_path_states)} states. Starting animation.")
        else:
            self.win_message = "AI không tìm ra cách giải!"
            self.win_message_timer = 2
            self.solved_by_ai = False # Reset nếu không tìm được path
            print("AI failed to find a solution for step-by-step.")


    def handle_event(self, event):
        if not self.is_active:
            return False

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if self.solve_ai_button and event.ui_element == self.solve_ai_button:
                # Chỉ cho phép nếu chưa thắng, AI chưa giải, và AI không đang giải từng bước
                if not self.just_won and not self.solved_by_ai and not self.is_ai_solving_step_by_step:
                    return config.PUZZLE_EVENT_AI_SOLVE_REQUEST
                return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Nếu AI đang giải từng bước, không cho click vào bảng
            if self.is_ai_solving_step_by_step:
                return False 
            
            if self.just_won and self.win_message_timer > 0: # Click để đóng sau khi thắng
                return True
            
            # Chỉ cho phép click nếu AI không giải và game chưa thắng
            if not self.just_won and not self.solved_by_ai:
                clicked_tile_pos = self.get_tile_at_mouse_pos(*event.pos)
                if clicked_tile_pos:
                    self.move_tile(*clicked_tile_pos)
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.is_ai_solving_step_by_step:
                    self.is_ai_solving_step_by_step = False # Dừng AI giải
                    self.solved_by_ai = False # Coi như AI chưa giải
                    self.win_message = "Đã dừng AI giải."
                    self.win_message_timer = 2
                    # Không set just_won, main.py sẽ xử lý là không hoàn thành
                else: # Nếu không phải AI đang giải, thì thoát bình thường
                    self.just_won = False 
                    self.solved_by_ai = False
                return True # Báo hiệu puzzle nên đóng
        return False

    def update(self, dt):
        if not self.is_active:
            return

        if self.is_ai_solving_step_by_step:
            self.ai_step_timer += dt
            if self.ai_step_timer >= config.AI_PUZZLE_SOLVE_STEP_DURATION:
                self.ai_step_timer -= config.AI_PUZZLE_SOLVE_STEP_DURATION # Giữ lại phần dư
                
                if self.ai_solution_current_step_index < len(self.ai_solution_path_states):
                    current_board_tuple = self.ai_solution_path_states[self.ai_solution_current_step_index]
                    self.board = self._tuple_to_board(current_board_tuple)
                    self._find_empty() # Cập nhật vị trí ô trống cho việc vẽ
                    self.ai_solution_current_step_index += 1
                
                if self.ai_solution_current_step_index >= len(self.ai_solution_path_states):
                    # AI đã hoàn thành tất cả các bước
                    self.is_ai_solving_step_by_step = False
                    self.just_won = True # Bây giờ mới coi là thắng
                    self.win_message = "AI đã giải xong!"
                    self.win_message_timer = 3 # Thời gian hiển thị thông báo thắng
                    print("AI finished step-by-step solution.")
        else: # Không phải AI đang giải từng bước
            if self.win_message_timer > 0 and self.win_message_timer != float('inf'):
                self.win_message_timer -= dt
                if self.win_message_timer <= 0:
                    self.win_message = ""
        
        if self.solve_ai_button:
            if self.just_won or self.solved_by_ai or self.is_ai_solving_step_by_step:
                if self.solve_ai_button.is_enabled:
                    self.solve_ai_button.disable()
            else:
                if not self.solve_ai_button.is_enabled:
                    self.solve_ai_button.enable()

    # ... (draw method như cũ) ...
    def draw(self, surface):
        if not self.is_active:
            return
            
        puzzle_surface = pygame.Surface((self.puzzle_width, self.puzzle_height), pygame.SRCALPHA)
        puzzle_surface.fill(config.PUZZLE_BG_COLOR)

        for r in range(config.PUZZLE_GRID_SIZE):
            for c in range(config.PUZZLE_GRID_SIZE):
                tile_value = self.board[r][c]
                tile_x_in_puzzle_surf = config.PUZZLE_BORDER + c * (config.PUZZLE_TILE_SIZE + config.PUZZLE_GAP)
                tile_y_in_puzzle_surf = config.PUZZLE_BORDER + r * (config.PUZZLE_TILE_SIZE + config.PUZZLE_GAP)
                rect = pygame.Rect(tile_x_in_puzzle_surf, tile_y_in_puzzle_surf, config.PUZZLE_TILE_SIZE, config.PUZZLE_TILE_SIZE)

                if tile_value != 0:
                    pygame.draw.rect(puzzle_surface, config.GREEN, rect)
                    pygame.draw.rect(puzzle_surface, config.BLUE, rect, 3)
                    text_surf = self.font.render(str(tile_value), True, config.TEXT_COLOR)
                    text_rect = text_surf.get_rect(center=rect.center)
                    puzzle_surface.blit(text_surf, text_rect)
                else:
                    pygame.draw.rect(puzzle_surface, config.BLACK, rect)
        
        if self.win_message_timer > 0 and self.win_message:
            msg_surf = self.message_font.render(self.win_message, True, config.WHITE)
            msg_rect = msg_surf.get_rect(center=(self.puzzle_width // 2, 30)) 
            puzzle_surface.blit(msg_surf, msg_rect)

        surface.blit(puzzle_surface, self.puzzle_rect.topleft)