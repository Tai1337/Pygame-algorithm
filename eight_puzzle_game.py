# eight_puzzle_game.py
import pygame
import random
import pygame_gui

from algorithms_puzzle import PUZZLE_ALGORITHMS_MAP, PUZZLE_ALGORITHMS_COSTS, PUZZLE_ALGORITHMS_INFO

# --- Constants for 8-Puzzle ---
GRID_SIZE = 3
TILE_SIZE_PUZZLE = 80
GAP_PUZZLE = 5
PUZZLE_BORDER = 10

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
BLUE = (100, 100, 255)
TEXT_COLOR = BLACK
PUZZLE_BG_COLOR = (50, 50, 50, 200)

class EightPuzzleGame:
            
    def __init__(self, screen_width, screen_height, ui_manager, player):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font = pygame.font.Font(None, 50)
        self.solved_board = [[1, 2, 3], [4, 5, 6], [7, 8, 0]]
        self.board = []
        self.empty_pos = None
        self.is_active = False

        # Thuộc tính cho UI và Player
        self.ui_manager = ui_manager
        self.player = player
        self.algo_buttons = [] # Danh sách các nút bấm thuật toán

        # Thuộc tính cho việc tự động giải puzzle
        self.auto_solve_moves = None # Danh sách các bước đi từ thuật toán
        self.auto_solve_delay = 0.5  # Độ trễ giữa các bước (giây) - Tăng lên để dễ quan sát
        self.auto_solve_timer = 0    # Bộ đếm cho độ trễ
        self.is_auto_solving = False # Cờ báo hiệu đang tự động giải

        # Lấy thông tin thuật toán từ file đã import
        self.PUZZLE_ALGORITHMS_MAP = PUZZLE_ALGORITHMS_MAP
        self.PUZZLE_ALGORITHMS_COSTS = PUZZLE_ALGORITHMS_COSTS
        
        self.puzzle_width = GRID_SIZE * TILE_SIZE_PUZZLE + (GRID_SIZE - 1) * GAP_PUZZLE + 2 * PUZZLE_BORDER
        self.puzzle_height = GRID_SIZE * TILE_SIZE_PUZZLE + (GRID_SIZE - 1) * GAP_PUZZLE + 2 * PUZZLE_BORDER
        self.puzzle_rect = pygame.Rect(
            (self.screen_width - self.puzzle_width) // 2,
            (self.screen_height - self.puzzle_height) // 2,
            self.puzzle_width,
            self.puzzle_height
        )
        self.message_font = pygame.font.Font(None, 36)
        self.win_message = ""
        self.win_message_timer = 0
        self.just_won = False
        self.win_processed_in_main = False

    def _kill_algo_buttons(self):
        for btn_data in self.algo_buttons:
            btn_data["button"].kill()
        self.algo_buttons = []

    def _create_algo_buttons(self):
        self._kill_algo_buttons() 

        num_algos = len(self.PUZZLE_ALGORITHMS_MAP)
        if num_algos == 0:
            return

        button_width = 220
        button_height = 40
        button_spacing = 10
        total_width_of_buttons = num_algos * button_width + (num_algos - 1) * button_spacing
        
        start_x = self.puzzle_rect.left + (self.puzzle_width - total_width_of_buttons) / 2
        start_y = self.puzzle_rect.bottom + 15

        current_x = start_x
        for algo_name, algo_func in self.PUZZLE_ALGORITHMS_MAP.items():
            cost = self.PUZZLE_ALGORITHMS_COSTS.get(algo_name, "N/A")
            button_text = f"{algo_name} ({cost} Tiền)"

            button_rect = pygame.Rect(
                current_x,
                start_y,
                button_width,
                button_height
            )
            button = pygame_gui.elements.UIButton(
                relative_rect=button_rect,
                text=button_text,
                manager=self.ui_manager,
                object_id=f"#puzzle_algo_button_{algo_name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('*','')}"
            )
            self.algo_buttons.append({
                "button": button,
                "name": algo_name,
                "func": algo_func,
                "cost": cost
            })
            current_x += button_width + button_spacing

    def _find_empty(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.board[r][c] == 0:
                    return r, c
        return None

    def _is_solvable(self, flat_board):
        inversions = 0
        temp_board = [i for i in flat_board if i != 0]
        for i in range(len(temp_board)):
            for j in range(i + 1, len(temp_board)):
                if temp_board[i] > temp_board[j]:
                    inversions += 1
        return inversions % 2 == 0

    def _generate_solvable_puzzle(self):
        numbers = list(range(GRID_SIZE * GRID_SIZE))
        while True:
            random.shuffle(numbers)
            if self._is_solvable(numbers):
                new_board = []
                for i in range(GRID_SIZE):
                    new_board.append(numbers[i*GRID_SIZE : (i+1)*GRID_SIZE])
                self.board = new_board
                self.empty_pos = self._find_empty()
                self.just_won = False 
                self.win_processed_in_main = False 
                if self.board != self.solved_board: # Đảm bảo puzzle không bắt đầu ở trạng thái đã giải
                    break
                


    def start_game(self):
        self._generate_solvable_puzzle()
        self.is_active = True
        self.win_message = ""
        self.win_message_timer = 0
        self.just_won = False
        self.win_processed_in_main = False
        self.is_auto_solving = False
        self.auto_solve_moves = None
        self.auto_solve_timer = 0
        if self.is_active: 
            self._create_algo_buttons()
        

    def get_tile_at_mouse_pos(self, mouse_x, mouse_y):
        if not self.puzzle_rect.collidepoint(mouse_x, mouse_y):
            return None
        local_x = mouse_x - self.puzzle_rect.left - PUZZLE_BORDER
        local_y = mouse_y - self.puzzle_rect.top - PUZZLE_BORDER
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                tile_x = c * (TILE_SIZE_PUZZLE + GAP_PUZZLE)
                tile_y = r * (TILE_SIZE_PUZZLE + GAP_PUZZLE)
                tile_rect = pygame.Rect(tile_x, tile_y, TILE_SIZE_PUZZLE, TILE_SIZE_PUZZLE)
                if tile_rect.collidepoint(local_x, local_y):
                    return r, c
        return None

    def move_tile(self, r, c):
        

        er, ec = self.empty_pos
        if (abs(r - er) == 1 and c == ec) or (abs(c - ec) == 1 and r == er): # Nước đi hợp lệ
            self.board[er][ec] = self.board[r][c]
            self.board[r][c] = 0
            self.empty_pos = (r, c)
            
                
            if self.check_win():
                self.win_message = "victory!"
                self.win_message_timer = 3 
                self.just_won = True      
                
        


    def check_win(self):
        return self.board == self.solved_board

    def handle_event(self, event):
        if not self.is_active:
            if self.algo_buttons: 
                self._kill_algo_buttons()
            return False

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if self.is_auto_solving or self.just_won: 
                return False 

            for btn_data in self.algo_buttons:
                if event.ui_element == btn_data["button"]:
                    algo_name = btn_data["name"]
                    algo_func = btn_data["func"]
                    cost = btn_data["cost"]

                    if isinstance(cost, int) and self.player.money >= cost:
                        self.player.spend_money(cost) 
                        print(f"[DEBUG HANDLE_EVENT] Nhấn nút: {algo_name}. Gọi hàm giải thuật toán...")
                        solution_path = algo_func(self.board)
                        print(f"[DEBUG HANDLE_EVENT] Kết quả từ thuật toán (solution_path): {solution_path}")

                        if solution_path is not None and isinstance(solution_path, list):
                            if not solution_path and self.board == self.solved_board: # Trường hợp puzzle đã giải
                                
                                self.win_message = "Puzzle đã được giải!"
                                self.win_message_timer = 2
                                # Có thể hoàn tiền nếu muốn, vì không dùng thuật toán
                                # self.player.add_money(cost)
                            elif not solution_path and self.board != self.solved_board: # Thuật toán trả về rỗng cho puzzle chưa giải?
                                
                                self.win_message = "Lỗi thuật toán!"
                                self.win_message_timer = 3
                                self.player.add_money(cost) # Hoàn tiền
                            else: # Có solution_path
                                self.auto_solve_moves = solution_path
                                self.is_auto_solving = True
                                
                                self.win_message = f"Loading ..."
                                self.win_message_timer = len(solution_path) * self.auto_solve_delay + 1.0
                                for b_data_inner in self.algo_buttons:
                                    b_data_inner["button"].disable()
                        else:
                            
                            self.win_message = "Thuật toán không tìm thấy lời giải!"
                            self.win_message_timer = 3
                            self.player.add_money(cost) 
                    elif isinstance(cost, int) and self.player.money < cost:
                        self.win_message = "Không đủ tiền!"
                        self.win_message_timer = 2
                    else: 
                        self.win_message = "Lỗi chi phí thuật toán!"
                        self.win_message_timer = 2
                    return False 

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_auto_solving: 
                
                return False

            if self.check_win() and self.win_message_timer > 0:
                self.is_active = False
                self._kill_algo_buttons() 
                return True

            if not self.just_won:
                clicked_tile_pos = self.get_tile_at_mouse_pos(*event.pos)
                if clicked_tile_pos:
                    self.move_tile(*clicked_tile_pos)
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.is_active = False
                self._kill_algo_buttons() 
                return True 
        return False
    
    def update(self, dt):
        if self.is_auto_solving and self.auto_solve_moves is not None: # Thêm check self.auto_solve_moves is not None
            # Thêm dòng print này ngay đầu để xem có vào block này không
            if not self.auto_solve_moves and not self.just_won: # Nếu list rỗng ngay từ đầu (ví dụ puzzle đã giải)
                 
                 self.is_auto_solving = False
                 # Không cần re-enable button ở đây vì nếu puzzle đã giải thì sẽ đóng sớm.
                 # Nếu thuật toán trả về rỗng một cách sai lầm thì handle_event đã xử lý.

            

            if not self.just_won: 
                self.auto_solve_timer -= dt
                

                if self.auto_solve_timer <= 0:
                     

                    if self.auto_solve_moves: 
                        move = self.auto_solve_moves.pop(0)
                        
                        self.move_tile(*move) 
                        self.auto_solve_timer = self.auto_solve_delay 
                        
                    else: 
                        
                        self.is_auto_solving = False
                        if not self.just_won: # Quan trọng: chỉ khi CHƯA THẮNG
                            self.win_message = "Tự động giải hoàn tất."
                            self.win_message_timer = 2
                            
                            for b_data in self.algo_buttons: 
                                if not b_data["button"].is_enabled: # Kiểm tra trước khi enable
                                    b_data["button"].enable()
            else: 
                
                self.is_auto_solving = False
                self.auto_solve_moves = None
        
        if self.win_message_timer > 0:
            self.win_message_timer -= dt
            if self.win_message_timer <= 0:
                self.win_message = "" 
                if self.check_win() and not self.is_auto_solving: 
                    self.is_active = False

        if not self.is_active and self.algo_buttons:
            
            self._kill_algo_buttons()

    def draw(self, surface):
        if not self.is_active:
            return
        puzzle_surface = pygame.Surface((self.puzzle_width, self.puzzle_height), pygame.SRCALPHA)
        puzzle_surface.fill(PUZZLE_BG_COLOR)
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                tile_value = self.board[r][c]
                tile_x = PUZZLE_BORDER + c * (TILE_SIZE_PUZZLE + GAP_PUZZLE)
                tile_y = PUZZLE_BORDER + r * (TILE_SIZE_PUZZLE + GAP_PUZZLE)
                rect = pygame.Rect(tile_x, tile_y, TILE_SIZE_PUZZLE, TILE_SIZE_PUZZLE)
                if tile_value != 0:
                    pygame.draw.rect(puzzle_surface, GREEN, rect)
                    pygame.draw.rect(puzzle_surface, BLUE, rect, 3)
                    text_surf = self.font.render(str(tile_value), True, TEXT_COLOR)
                    text_rect = text_surf.get_rect(center=rect.center)
                    puzzle_surface.blit(text_surf, text_rect)
                else:
                    pygame.draw.rect(puzzle_surface, BLACK, rect) # Vẽ ô trống
        
        if self.win_message_timer > 0 and self.win_message: 
            msg_surf = self.message_font.render(self.win_message, True, WHITE)
            msg_rect = msg_surf.get_rect(center=(self.puzzle_width // 2, self.puzzle_height - 30)) # Điều chỉnh vị trí thông báo nếu cần
            puzzle_surface.blit(msg_surf, msg_rect)
        
        surface.blit(puzzle_surface, self.puzzle_rect.topleft)