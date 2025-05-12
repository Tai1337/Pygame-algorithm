# src/minigames/eight_puzzle_game.py
import pygame
import random
import heapq
import src.config as config
import pygame_gui
from .base_minigame import BaseMiniGame

class EightPuzzleGame(BaseMiniGame):
    # ... (__init__, start_game, và các phương thức khác giữ nguyên như phiên bản ở Turn 28) ...
    # (Đảm bảo các phương thức _board_to_tuple, _solve_puzzle_with_ucs, attempt_ai_solve, etc. đã có)

    def __init__(self, screen_width, screen_height, ui_manager):
        super().__init__(screen_width, screen_height, ui_manager)
        
        try:
            self.tile_font = pygame.font.Font(None, 50)
            self.message_font = pygame.font.Font(None, 36) 
        except pygame.error as e:
            self.tile_font = pygame.font.SysFont(None, 50)
            self.message_font = pygame.font.SysFont(None, 36)

        self.solved_board = [[1, 2, 3], [4, 5, 6], [7, 8, 0]]
        self.board = [] 
        self.empty_pos = None
        self.puzzle_width = config.PUZZLE_GRID_SIZE * config.PUZZLE_TILE_SIZE + \
                            (config.PUZZLE_GRID_SIZE - 1) * config.PUZZLE_GAP + \
                            2 * config.PUZZLE_BORDER
        self.puzzle_height = config.PUZZLE_GRID_SIZE * config.PUZZLE_TILE_SIZE + \
                             (config.PUZZLE_GRID_SIZE - 1) * config.PUZZLE_GAP + \
                             2 * config.PUZZLE_BORDER
        self.puzzle_rect = pygame.Rect(
            (self.screen_width - self.puzzle_width) // 2,
            (self.screen_height - self.puzzle_height - config.SOLVE_AI_BUTTON_HEIGHT - config.SOLVE_AI_BUTTON_MARGIN_TOP - 20) // 2,
            self.puzzle_width,
            self.puzzle_height
        )
        self.display_message = "" 
        self.display_message_timer = 0    
        self.solved_by_ai = False
        self.solve_ai_button = None
        self.is_ai_solving_step_by_step = False
        self.ai_solution_path_states = [] 
        self.ai_solution_current_step_index = 0
        self.ai_step_timer = 0.0
        self._goal_pos_map_cache = {}
        goal_tuple_for_cache = self._board_to_tuple(self.solved_board)
        for r_goal in range(config.PUZZLE_GRID_SIZE):
            for c_goal in range(config.PUZZLE_GRID_SIZE):
                tile_value_in_goal = goal_tuple_for_cache[r_goal][c_goal]
                if tile_value_in_goal != 0:
                    self._goal_pos_map_cache[tile_value_in_goal] = (r_goal, c_goal)

    def start_game(self):
        super().start_game() 
        self._generate_solvable_puzzle()
        self.display_message = ""
        self.display_message_timer = 0
        self.solved_by_ai = False
        self.is_ai_solving_step_by_step = False
        self.ai_solution_path_states = []
        self.ai_solution_current_step_index = 0
        self.ai_step_timer = 0.0
        self.cleanup_ui() 
        self._create_ai_button()

    def _create_ai_button(self):
        if self.solve_ai_button and self.solve_ai_button.alive(): 
            self.solve_ai_button.enable()
            self.solve_ai_button.show()
            return
        button_rect_x = self.puzzle_rect.centerx - config.SOLVE_AI_BUTTON_WIDTH // 2
        button_rect_y = self.puzzle_rect.bottom + config.SOLVE_AI_BUTTON_MARGIN_TOP
        self.solve_ai_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(button_rect_x, button_rect_y, config.SOLVE_AI_BUTTON_WIDTH, config.SOLVE_AI_BUTTON_HEIGHT),
            text=config.SOLVE_AI_BUTTON_TEXT.format(cost=config.PUZZLE_SOLVE_COST),
            manager=self.ui_manager,
            object_id="#solve_ai_puzzle_button"
        )

    def cleanup_ui(self):
        super().cleanup_ui()
        if self.solve_ai_button:
            if self.solve_ai_button.alive():
                 self.solve_ai_button.kill()
            self.solve_ai_button = None

    def _find_empty(self):
        for r in range(config.PUZZLE_GRID_SIZE):
            for c in range(config.PUZZLE_GRID_SIZE):
                if self.board[r][c] == 0:
                    self.empty_pos = (r,c) 
                    return r, c
        return None 

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
                self._find_empty() 
                if self.board != self.solved_board:
                    break
        self.solved_by_ai = False
        self.is_ai_solving_step_by_step = False
    
    def get_tile_at_mouse_pos(self, mouse_x, mouse_y):
        # ... (giữ nguyên)
        if not self.puzzle_rect.collidepoint(mouse_x, mouse_y): return None
        local_x = mouse_x - self.puzzle_rect.left - config.PUZZLE_BORDER
        local_y = mouse_y - self.puzzle_rect.top - config.PUZZLE_BORDER
        for r in range(config.PUZZLE_GRID_SIZE):
            for c in range(config.PUZZLE_GRID_SIZE):
                tile_x_start = c * (config.PUZZLE_TILE_SIZE + config.PUZZLE_GAP)
                tile_y_start = r * (config.PUZZLE_TILE_SIZE + config.PUZZLE_GAP)
                tile_clickable_rect = pygame.Rect(tile_x_start, tile_y_start, config.PUZZLE_TILE_SIZE, config.PUZZLE_TILE_SIZE)
                if tile_clickable_rect.collidepoint(local_x, local_y): return r, c
        return None

    def move_tile(self, r, c):
        # ... (giữ nguyên, nhưng thông báo thắng sẽ là "Bạn đã thắng!")
        if not self.is_active or self.won or self.solved_by_ai or self.is_ai_solving_step_by_step: return
        er, ec = self.empty_pos
        if (abs(r - er) == 1 and c == ec) or (abs(c - ec) == 1 and r == er):
            self.board[er][ec] = self.board[r][c]
            self.board[r][c] = 0
            self._find_empty()
            if self.check_win():
                self.display_message = "Bạn đã thắng!" # Thông báo người chơi tự thắng
                self.display_message_timer = 3
                self.won = True 
                self.is_active = False 
                if self.solve_ai_button and self.solve_ai_button.alive(): self.solve_ai_button.disable()

    def check_win(self):
        return self.board == self.solved_board

    def _board_to_tuple(self, board_list): # Giữ nguyên
        return tuple(tuple(row) for row in board_list)

    def _tuple_to_board(self, board_tuple): # Giữ nguyên
        return [list(row) for row in board_tuple]

    def _find_empty_in_tuple(self, board_tuple): # Giữ nguyên
        for r_idx, row_val in enumerate(board_tuple):
            for c_idx, tile_val in enumerate(row_val):
                if tile_val == 0: return r_idx, c_idx
        return None
    
    def _solve_puzzle_with_ucs(self): # Giữ nguyên logic UCS
        start_board_tuple = self._board_to_tuple(self.board)
        goal_board_tuple = self._board_to_tuple(self.solved_board)
        if start_board_tuple == goal_board_tuple: return [start_board_tuple]
        open_set = [(0, start_board_tuple)] 
        heapq.heapify(open_set)
        came_from = {start_board_tuple: None}
        visited_states = {start_board_tuple}
        max_nodes_to_explore = config.PUZZLE_AI_UCS_MAX_EXPLORE_NODES 
        nodes_explored_count = 0
        while open_set:
            nodes_explored_count += 1
            if nodes_explored_count > max_nodes_to_explore:
                print(f"UCS reached exploration limit of {max_nodes_to_explore} nodes.")
                return None
            g, current_board_tuple = heapq.heappop(open_set)
            if current_board_tuple == goal_board_tuple:
                path_of_states = []
                temp_state = current_board_tuple
                while temp_state is not None:
                    path_of_states.append(temp_state)
                    temp_state = came_from.get(temp_state)
                path_of_states.reverse()
                return path_of_states
            empty_r, empty_c = self._find_empty_in_tuple(current_board_tuple)
            if empty_r is None: continue
            for dr_empty, dc_empty in [(0, 1), (0, -1), (1, 0), (-1, 0)]: 
                tile_to_move_r, tile_to_move_c = empty_r - dr_empty, empty_c - dc_empty
                if 0 <= tile_to_move_r < config.PUZZLE_GRID_SIZE and \
                   0 <= tile_to_move_c < config.PUZZLE_GRID_SIZE:
                    new_board_list = self._tuple_to_board(current_board_tuple)
                    new_board_list[empty_r][empty_c] = new_board_list[tile_to_move_r][tile_to_move_c]
                    new_board_list[tile_to_move_r][tile_to_move_c] = 0
                    neighbor_board_tuple = self._board_to_tuple(new_board_list)
                    if neighbor_board_tuple not in visited_states:
                        visited_states.add(neighbor_board_tuple)
                        came_from[neighbor_board_tuple] = current_board_tuple
                        heapq.heappush(open_set, (g + 1, neighbor_board_tuple))
        print("UCS could not find a solution.")
        return None
    
    def attempt_ai_solve(self):
        if self.won or self.solved_by_ai or self.is_ai_solving_step_by_step: return

        print("Attempting AI solve with UCS...")
        solution_states = self._solve_puzzle_with_ucs() 
        if solution_states and len(solution_states) > 0:
            self.ai_solution_path_states = solution_states
            self.ai_solution_current_step_index = 0
            self.ai_step_timer = 0.0
            self.is_ai_solving_step_by_step = True
            self.solved_by_ai = True 
            self.display_message = "AI đang giải..." # Thông báo ban đầu
            self.display_message_timer = float('inf') 
            if self.solve_ai_button and self.solve_ai_button.alive(): self.solve_ai_button.disable()
        else:
            self.display_message = "AI không tìm ra cách giải!"
            self.display_message_timer = 3
            self.solved_by_ai = False 
            if self.solve_ai_button and self.solve_ai_button.alive(): self.solve_ai_button.enable()

    def handle_event(self, event):
        # ... (logic handle_event như ở Turn 28, đảm bảo nó trả về True khi game kết thúc) ...
        # Và gọi self.cleanup_ui() trước khi return True từ các trường hợp đóng game
        if super().handle_event(event): 
            self.cleanup_ui()
            return True 
        if not self.is_active:
            if self.won and self.display_message_timer > 0 and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.cleanup_ui()
                return True
            return True 
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if self.solve_ai_button and self.solve_ai_button.alive() and event.ui_element == self.solve_ai_button:
                if not self.won and not self.solved_by_ai and not self.is_ai_solving_step_by_step:
                    return config.PUZZLE_EVENT_AI_SOLVE_REQUEST
                return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_ai_solving_step_by_step: return False 
            if self.won and self.display_message_timer > 0:
                self.cleanup_ui()
                return True
            if not self.won and not self.solved_by_ai:
                clicked_tile_pos = self.get_tile_at_mouse_pos(*event.pos)
                if clicked_tile_pos:
                    self.move_tile(*clicked_tile_pos)
                    if self.won:
                        self.cleanup_ui()
                        return True
        return False


    def update(self, dt):
        if not self.is_active:
            if self.won and self.display_message_timer > 0:
                self.display_message_timer -= dt
                if self.display_message_timer <= 0:
                    self.display_message = ""
                    return True 
                return False 
            return True 

        if self.is_ai_solving_step_by_step:
            self.ai_step_timer += dt
            if self.ai_step_timer >= config.AI_PUZZLE_SOLVE_STEP_DURATION:
                self.ai_step_timer -= config.AI_PUZZLE_SOLVE_STEP_DURATION
                if self.ai_solution_current_step_index < len(self.ai_solution_path_states):
                    current_board_tuple = self.ai_solution_path_states[self.ai_solution_current_step_index]
                    self.board = self._tuple_to_board(current_board_tuple)
                    self._find_empty()
                    self.ai_solution_current_step_index += 1
                if self.ai_solution_current_step_index >= len(self.ai_solution_path_states):
                    self.is_ai_solving_step_by_step = False
                    self.won = True 
                    self.is_active = False 
                    # THAY ĐỔI THÔNG BÁO
                    self.display_message = config.AI_SOLVED_DEDUCTION_MESSAGE.format(cost=config.PUZZLE_SOLVE_COST)
                    self.display_message_timer = 4 # Hiện thông báo này lâu hơn một chút
                    print("AI finished. Message: ", self.display_message)
                    return True # Báo hiệu game kết thúc
            return False 
        
        if self.display_message_timer > 0 and self.display_message_timer != float('inf'):
            self.display_message_timer -= dt
            if self.display_message_timer <= 0:
                self.display_message = ""
        
        if self.solve_ai_button and self.solve_ai_button.alive(): # Kiểm tra nút còn tồn tại
            if self.won or self.solved_by_ai or self.is_ai_solving_step_by_step:
                if self.solve_ai_button.is_enabled: self.solve_ai_button.disable()
            else:
                if not self.solve_ai_button.is_enabled: self.solve_ai_button.enable()
        
        return False

    def draw(self, surface, main_game_time_remaining):
        super().draw(surface, main_game_time_remaining)
        
        puzzle_render_surface = pygame.Surface((self.puzzle_width, self.puzzle_height), pygame.SRCALPHA)
        puzzle_render_surface.fill((0,0,0,0))

        for r in range(config.PUZZLE_GRID_SIZE):
            for c in range(config.PUZZLE_GRID_SIZE):
                tile_value = self.board[r][c]
                tile_x = config.PUZZLE_BORDER + c * (config.PUZZLE_TILE_SIZE + config.PUZZLE_GAP)
                tile_y = config.PUZZLE_BORDER + r * (config.PUZZLE_TILE_SIZE + config.PUZZLE_GAP)
                rect = pygame.Rect(tile_x, tile_y, config.PUZZLE_TILE_SIZE, config.PUZZLE_TILE_SIZE)
                if tile_value != 0:
                    pygame.draw.rect(puzzle_render_surface, config.GREEN, rect)
                    pygame.draw.rect(puzzle_render_surface, config.BLUE, rect, 3)
                    text_surf = self.tile_font.render(str(tile_value), True, config.TEXT_COLOR)
                    text_rect = text_surf.get_rect(center=rect.center)
                    puzzle_render_surface.blit(text_surf, text_rect)
                else:
                    pygame.draw.rect(puzzle_render_surface, config.BLACK, rect)
        
        # Hiển thị display_message (thắng bởi người chơi, AI đang giải, AI giải xong, lỗi AI)
        if self.display_message_timer > 0 and self.display_message:
            msg_surf = self.message_font.render(self.display_message, True, config.WHITE)
            # Đặt thông báo này ở trên cùng của puzzle_render_surface, dưới timer của game chính (nếu có)
            # Vị trí timer của game chính được vẽ bởi BaseMiniGame.draw_main_game_timer
            # Giả sử timer game chính cao khoảng 30-40px từ mép trên của vùng minigame (do lớp cha vẽ)
            # Chúng ta sẽ đặt thông báo này ngay dưới đó, hoặc ở một vị trí cố định khác.
            # Ví dụ: đặt ở phía trên của puzzle_rect, bên trong khu vực lớp phủ mờ.
            
            # Tính toán vị trí cho thông báo của 8-puzzle, nằm bên trong puzzle_rect
            # nhưng phía trên các ô số, và dưới timer của game chính (vẽ bởi BaseMiniGame)
            msg_y_offset = config.PUZZLE_BORDER + self.font.get_height() + 15 # Khoảng cách từ trên cùng của puzzle_surface
            if hasattr(super(), 'timer_font') and super().timer_font: # Nếu lớp cha có timer_font
                 msg_y_offset = config.PUZZLE_BORDER + super().timer_font.get_height() + 20 # Dưới timer của game chính

            msg_rect = msg_surf.get_rect(center=(self.puzzle_width // 2, msg_y_offset))
            puzzle_render_surface.blit(msg_surf, msg_rect)

        surface.blit(puzzle_render_surface, self.puzzle_rect.topleft)