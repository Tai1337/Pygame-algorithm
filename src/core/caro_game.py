# src/core/caro_game.py
import pygame
import random
import math
import sys 
import src.config as config

class CaroGame:
    def __init__(self, screen_width, screen_height, board_size=config.CARO_BOARD_SIZE, win_length=config.CARO_WIN_LENGTH):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.board_size = board_size
        self.win_length = win_length

        self.tile_size = config.CARO_TILE_SIZE
        self.board_pixel_width = self.board_size * self.tile_size
        self.board_pixel_height = self.board_size * self.tile_size

        self.board_rect = pygame.Rect(
            (self.screen_width - self.board_pixel_width) // 2,
            (self.screen_height - self.board_pixel_height) // 2 - 30,
            self.board_pixel_width,
            self.board_pixel_height
        )

        try:
            self.font = pygame.font.Font(None, config.CARO_FONT_SIZE)
            self.message_font = pygame.font.Font(None, config.CARO_MESSAGE_FONT_SIZE)
        except pygame.error as e:
            print(f"Lỗi khởi tạo font cho Caro: {e}. Sử dụng font hệ thống.")
            self.font = pygame.font.SysFont(None, config.CARO_FONT_SIZE)
            self.message_font = pygame.font.SysFont(None, config.CARO_MESSAGE_FONT_SIZE)

        self.board = []
        self.current_player = 1
        self.is_active = False 
        self.game_over = False
        self.winner = None
        self.winning_line = []

        self.ai_player_mark = 2
        self.human_player_mark = 1
        self.ai_difficulty = config.DEFAULT_CARO_AI
        
        self.message = ""
        self.message_timer = 0
        self.message_color = config.WHITE

        self.q_table = {}
        self.learning_rate = config.CARO_QL_LEARNING_RATE
        self.discount_factor = config.CARO_QL_DISCOUNT_FACTOR
        self.exploration_rate = config.CARO_QL_EXPLORATION_RATE
        self.last_ai_state_action = None

    def start_new_game(self, ai_difficulty='minimax'):
        self.board = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.current_player = self.human_player_mark # Người chơi luôn đi trước khi game mới bắt đầu
        # self.is_active = True # Sẽ được đặt thành True bởi main.py
        self.game_over = False
        self.winner = None
        self.winning_line = []
        self.ai_difficulty = ai_difficulty
        self.message = "Lượt của bạn (X)"
        self.message_color = config.WHITE
        self.message_timer = 0
        self.last_ai_state_action = None
        print(f"Caro game variables reset for AI: {self.ai_difficulty}. Game is NOT set to active by this function.")

    def get_board_state_tuple(self):
        return tuple(tuple(row) for row in self.board)

    def get_possible_moves(self, board_state=None):
        current_b = board_state if board_state is not None else self.board
        moves = []
        for r in range(self.board_size):
            for c in range(self.board_size):
                if current_b[r][c] == 0:
                    moves.append((r, c))
        return moves

    def make_move(self, row, col, player_mark, board_state=None):
        target_board = board_state if board_state is not None else self.board
        is_internal_move = board_state is None

        if 0 <= row < self.board_size and 0 <= col < self.board_size and target_board[row][col] == 0:
            target_board[row][col] = player_mark
            if is_internal_move: 
                # Chỉ check game status và chuyển lượt nếu đây là nước đi thật trên self.board
                self.check_game_status(player_mark, (row, col)) 
                if not self.game_over:
                    self.current_player = self.ai_player_mark if player_mark == self.human_player_mark else self.human_player_mark
                    self.message = "Lượt của AI (O)" if self.current_player == self.ai_player_mark else "Lượt của bạn (X)"
                    self.message_color = config.WHITE
            return True
        return False

    def _check_win_on_board_at_coord(self, board_to_check, mark, r_coord, c_coord):
        """
        Kiểm tra xem 'mark' tại (r_coord, c_coord) trên 'board_to_check' có tạo thành đường thắng không.
        Hàm này không thay đổi self.board.
        """
        if not (0 <= r_coord < self.board_size and 0 <= c_coord < self.board_size and board_to_check[r_coord][c_coord] == mark):
            return False # Ô không hợp lệ hoặc không chứa quân cờ cần kiểm tra

        orientations = [(0, 1), (1, 0), (1, 1), (1, -1)] # Ngang, Dọc, Chéo Xuống, Chéo Lên
        for dr, dc in orientations:
            count = 1 # Bắt đầu từ chính quân cờ đó
            # Kiểm tra theo một hướng
            for i in range(1, self.win_length):
                nr, nc = r_coord + i * dr, c_coord + i * dc
                if 0 <= nr < self.board_size and 0 <= nc < self.board_size and board_to_check[nr][nc] == mark:
                    count += 1
                else:
                    break
            # Kiểm tra theo hướng ngược lại
            for i in range(1, self.win_length):
                nr, nc = r_coord - i * dr, c_coord - i * dc
                if 0 <= nr < self.board_size and 0 <= nc < self.board_size and board_to_check[nr][nc] == mark:
                    count += 1
                else:
                    break
            
            if count >= self.win_length:
                return True # Tìm thấy đường thắng
        return False

    def check_win_at(self, mark, r, c): # Hàm này kiểm tra trên self.board
        """Kiểm tra xem việc đặt mark tại (r,c) trên self.board có tạo ra chiến thắng không.
           LƯU Ý: Hàm này giả định self.board[r][c] ĐÃ LÀ `mark`.
        """
        return self._check_win_on_board_at_coord(self.board, mark, r, c)


    def check_draw(self, board_state=None): # Thêm tham số board_state
        current_b = board_state if board_state is not None else self.board
        for r in range(self.board_size):
            for c in range(self.board_size):
                if current_b[r][c] == 0:
                    return False
        return True 

    def check_game_status(self, player_mark, last_move_coords):
        r, c = last_move_coords
        if self._check_win_on_board_at_coord(self.board, player_mark, r, c): # Sử dụng hàm kiểm tra trên self.board
            self.game_over = True
            self.winner = player_mark
            # Logic lấy winning_line cần được điều chỉnh nếu _check_win_on_board_at_coord không trả về line
            # Tạm thời bỏ qua việc vẽ winning_line nếu hàm trên chỉ trả về True/False
            self.winning_line = [] # Cần hàm riêng để tìm winning_line nếu muốn vẽ
            self.message = f"Player {player_mark} ('{'X' if player_mark == self.human_player_mark else 'O'}') thắng!"
            self.message_color = config.GREEN if player_mark == self.human_player_mark else config.RED
            self.message_timer = 5 
            return

        if self.check_draw(): # check_draw bây giờ có thể kiểm tra self.board mặc định
            self.game_over = True
            self.winner = 0 
            self.message = "Hòa!"
            self.message_color = config.YELLOW 
            self.message_timer = 5
            return
    
    def handle_event(self, event):
        if not self.is_active:
            return False

        if self.game_over and self.message_timer <= 0: 
             if event.type == pygame.MOUSEBUTTONDOWN or (event.type == pygame.KEYDOWN and event.key != pygame.K_ESCAPE):
                return True 

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.is_active = False 
                self.game_over = True 
                self.winner = None 
                self.message = "Đã thoát Caro."
                self.message_color = config.WHITE
                self.message_timer = 2 
                return True 

        if not self.game_over and self.current_player == self.human_player_mark:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_x, mouse_y = event.pos
                if self.board_rect.collidepoint(mouse_x, mouse_y):
                    clicked_col = (mouse_x - self.board_rect.left) // self.tile_size
                    clicked_row = (mouse_y - self.board_rect.top) // self.tile_size
                    
                    self.make_move(clicked_row, clicked_col, self.human_player_mark)
                        
        return False

    def update(self, dt):
        if not self.is_active:
            return

        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer < 0: self.message_timer = 0 # Đảm bảo không âm

            if self.message_timer == 0:
                if not self.game_over: 
                    self.message = "Lượt của AI (O)" if self.current_player == self.ai_player_mark else "Lượt của bạn (X)"
                    self.message_color = config.WHITE
                # else: giữ nguyên thông báo thắng/thua/hòa

        if not self.game_over and self.current_player == self.ai_player_mark:
            self.ai_take_turn()

    # --- AI Logic ---
    def ai_take_turn(self):
        if self.game_over: return

        print(f"AI ({self.ai_difficulty}) is thinking...")
        pygame.event.pump() # Xử lý các sự kiện Pygame để tránh treo khi AI tính toán lâu

        move = None 
        if self.ai_difficulty == 'random':
            move = self.ai_random_move()
        elif self.ai_difficulty == 'greedy':
            move = self.ai_greedy_move()
        elif self.ai_difficulty == 'minimax':
            move = self.ai_minimax_move(depth=config.CARO_MINIMAX_DEPTH)
        elif self.ai_difficulty == 'q_learning':
            move = self.ai_q_learning_move()
        elif self.ai_difficulty == 'hill_climbing':
            move = self.ai_hill_climbing_move()
        elif self.ai_difficulty == 'beam_search':
            move = self.ai_beam_search_move(beam_width=config.CARO_BEAM_WIDTH, depth=config.CARO_BEAM_DEPTH)
        else: 
            move = self.ai_random_move()

        if move:
            if self.ai_difficulty == 'q_learning':
                self.last_ai_state_action = (self.get_board_state_tuple(), move)

            self.make_move(move[0], move[1], self.ai_player_mark)
            
            if self.ai_difficulty == 'q_learning' and self.last_ai_state_action:
                reward = 0
                if self.game_over:
                    if self.winner == self.ai_player_mark: reward = config.CARO_REWARD_WIN
                    elif self.winner == self.human_player_mark: reward = config.CARO_REWARD_LOSS
                    else: reward = config.CARO_REWARD_DRAW
                self.update_q_value(self.last_ai_state_action[0], self.last_ai_state_action[1], reward, self.get_board_state_tuple(), self.game_over)
                self.last_ai_state_action = None
        elif not self.get_possible_moves() and not self.game_over : 
            self.game_over = True
            self.winner = 0 
            self.message = "Hòa! (AI không còn nước đi)"
            self.message_color = config.YELLOW
            self.message_timer = 5
    
    def ai_random_move(self):
        possible_moves = self.get_possible_moves()
        return random.choice(possible_moves) if possible_moves else None

    def _get_winning_line_for_draw(self, board, mark, r_start, c_start):
        """
        Hàm này được dùng bởi _check_win_on_board_at_coord_for_draw để trả về đường thắng
        nếu có, dùng cho việc vẽ.
        """
        orientations = [(0, 1), (1, 0), (1, 1), (1, -1)] 
        for dr, dc in orientations:
            line = [(r_start, c_start)]
            # Hướng 1
            for i in range(1, self.win_length):
                r, c = r_start + i * dr, c_start + i * dc
                if 0 <= r < self.board_size and 0 <= c < self.board_size and board[r][c] == mark:
                    line.append((r,c))
                else:
                    break
            # Hướng 2 (ngược lại)
            for i in range(1, self.win_length):
                r, c = r_start - i * dr, c_start - i * dc
                if 0 <= r < self.board_size and 0 <= c < self.board_size and board[r][c] == mark:
                    line.insert(0, (r,c)) # Chèn vào đầu để giữ thứ tự
                else:
                    break
            
            # Bây giờ `line` chứa tất cả các quân cờ liên tiếp theo hướng này
            # Chúng ta cần tìm một chuỗi con có độ dài `self.win_length`
            if len(line) >= self.win_length:
                for i in range(len(line) - self.win_length + 1):
                    sub_line = line[i:i+self.win_length]
                    if len(sub_line) == self.win_length: # Double check
                        return sub_line # Trả về đường thắng đầu tiên tìm thấy
        return []


    def evaluate_board_heuristic(self, board_state, player_to_evaluate_for, is_maximizing_call):
        # player_to_evaluate_for là quân cờ của người chơi mà lượt đi hiện tại của Minimax đang xét
        # is_maximizing_call cho biết liệu đây có phải là lượt của AI (True) hay người (False) trong cây Minimax
        
        ai_score = self._calculate_player_potential_score(board_state, self.ai_player_mark, self.human_player_mark)
        human_score = self._calculate_player_potential_score(board_state, self.human_player_mark, self.ai_player_mark)

        # Điểm số cuối cùng là hiệu số, dương nếu AI lợi thế, âm nếu người chơi lợi thế
        final_score = ai_score - human_score * 1.5 # Ưu tiên chặn đối thủ mạnh hơn một chút
        return final_score


    def _calculate_player_potential_score(self, board, mark, opponent_mark):
        score = 0
        # Trọng số cho các chuỗi có độ dài khác nhau và số đầu mở
        # (length, open_ends): weight
        weights = {
            (self.win_length, 0): config.CARO_REWARD_WIN * 10, # Thắng tuyệt đối (thực tế nên được xử lý ở terminal state)
            (self.win_length - 1, 2): 5000,  # 4 mở 2 đầu (gần như thắng)
            (self.win_length - 1, 1): 1000,  # 4 mở 1 đầu
            (self.win_length - 2, 2): 500,   # 3 mở 2 đầu
            (self.win_length - 2, 1): 100,   # 3 mở 1 đầu
            (self.win_length - 3, 2): 50,    # 2 mở 2 đầu
            (self.win_length - 3, 1): 10,    # 2 mở 1 đầu
            # Có thể thêm trọng số cho các chuỗi bị chặn 1 đầu (open_ends = 0) nếu muốn
        }

        orientations = [(0, 1), (1, 0), (1, 1), (1, -1)]
        checked_lines = set() # Để tránh đếm một đường nhiều lần từ các ô khác nhau trên đường đó

        for r in range(self.board_size):
            for c in range(self.board_size):
                if board[r][c] == mark: # Chỉ bắt đầu phân tích từ một quân cờ của người chơi hiện tại
                    for dr, dc in orientations:
                        # Kiểm tra xuôi
                        current_marks_in_line = 0
                        line_coords = []
                        open_ends = 0
                        
                        # Ô phía trước (đầu 1)
                        prev_r, prev_c = r - dr, c - dc
                        if not (0 <= prev_r < self.board_size and 0 <= prev_c < self.board_size) or \
                           board[prev_r][prev_c] == opponent_mark:
                            pass # Bị chặn hoặc ra ngoài biên
                        elif board[prev_r][prev_c] == 0:
                            open_ends += 1

                        # Đếm chuỗi
                        for i in range(self.win_length): # Kiểm tra tối đa win_length
                            nr, nc = r + i * dr, c + i * dc
                            if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                                if board[nr][nc] == mark:
                                    current_marks_in_line += 1
                                    line_coords.append((nr,nc))
                                elif board[nr][nc] == opponent_mark: # Bị chặn
                                    current_marks_in_line = -1 # Đánh dấu là bị chặn hoàn toàn
                                    break
                                else: # Gặp ô trống
                                    break 
                            else: # Ra ngoài biên
                                break
                        
                        if current_marks_in_line > 0:
                            # Kiểm tra ô phía sau (đầu 2)
                            next_r, next_c = r + current_marks_in_line * dr, c + current_marks_in_line * dc
                            if not (0 <= next_r < self.board_size and 0 <= next_c < self.board_size) or \
                               board[next_r][next_c] == opponent_mark:
                                pass # Bị chặn hoặc ra ngoài biên
                            elif board[next_r][next_c] == 0:
                                open_ends +=1

                            # Chỉ tính điểm nếu có ít nhất 1 đầu mở, hoặc là đường thắng
                            if open_ends > 0 or current_marks_in_line == self.win_length:
                                # Sắp xếp line_coords để tạo key duy nhất cho set
                                sorted_line_key = tuple(sorted(line_coords))
                                if sorted_line_key not in checked_lines and len(sorted_line_key) == current_marks_in_line :
                                    if current_marks_in_line == self.win_length : # Đây là đường thắng
                                         score += weights.get((current_marks_in_line, True), 0) # True vì nó là đường thắng
                                    else:
                                        score += weights.get((current_marks_in_line, open_ends >=1 ), 0) * (open_ends +1) # open_ends >=1 -> True
                                    checked_lines.add(sorted_line_key)
        return score


    def _check_win_on_board_at_coord(self, board_to_check, mark, r_coord, c_coord):
        # (Giữ nguyên như phiên bản trước bạn đã có)
        if not (0 <= r_coord < self.board_size and 0 <= c_coord < self.board_size and board_to_check[r_coord][c_coord] == mark):
            return False 
        orientations = [(0, 1), (1, 0), (1, 1), (1, -1)] 
        for dr, dc in orientations:
            count = 1 
            for i in range(1, self.win_length):
                nr, nc = r_coord + i * dr, c_coord + i * dc
                if 0 <= nr < self.board_size and 0 <= nc < self.board_size and board_to_check[nr][nc] == mark:
                    count += 1
                else:
                    break
            for i in range(1, self.win_length):
                nr, nc = r_coord - i * dr, c_coord - i * dc
                if 0 <= nr < self.board_size and 0 <= nc < self.board_size and board_to_check[nr][nc] == mark:
                    count += 1
                else:
                    break
            if count >= self.win_length:
                return True
        return False
    
    def ai_minimax_move(self, depth=config.CARO_MINIMAX_DEPTH):
        # AI là người chơi MAXIMIZING (muốn điểm cao nhất)
        _, move = self._minimax_alpha_beta(self.board, depth, -sys.maxsize, sys.maxsize, True, self.ai_player_mark, self.human_player_mark)
        if move is None: 
            print("DEBUG: Minimax không trả về nước đi cụ thể, chọn ngẫu nhiên.")
            return self.ai_random_move()
        return move

    def _minimax_alpha_beta(self, current_board_state, depth, alpha, beta, is_maximizing_player, ai_mark, human_mark):
        # 1. Kiểm tra trạng thái kết thúc của current_board_state
        # Kiểm tra AI thắng
        for r in range(self.board_size):
            for c in range(self.board_size):
                if current_board_state[r][c] == ai_mark:
                    if self._check_win_on_board_at_coord(current_board_state, ai_mark, r, c):
                        return config.CARO_REWARD_WIN + depth * 10, None # Thưởng cho thắng nhanh hơn
        
        # Kiểm tra Người chơi thắng
        for r in range(self.board_size):
            for c in range(self.board_size):
                if current_board_state[r][c] == human_mark:
                     if self._check_win_on_board_at_coord(current_board_state, human_mark, r, c):
                        return config.CARO_REWARD_LOSS - depth * 10, None # Phạt cho thua nhanh hơn

        possible_moves = self.get_possible_moves(current_board_state)
        if not possible_moves: # Hòa
            return config.CARO_REWARD_DRAW, None
        
        if depth == 0: # Hết độ sâu
            # Đánh giá từ góc nhìn của AI (player_to_evaluate_for = ai_mark)
            return self.evaluate_board_heuristic(current_board_state, ai_mark, True), None

        best_move_for_this_call = possible_moves[0] # Khởi tạo best_move để tránh lỗi nếu không tìm thấy nước đi nào tốt hơn
        # random.shuffle(possible_moves) # Bỏ shuffle để có thể debug dễ hơn, thêm lại sau nếu muốn random hóa

        if is_maximizing_player: # Lượt của AI (MAX)
            max_eval = -sys.maxsize
            for r_move, c_move in possible_moves:
                board_copy = [row[:] for row in current_board_state]
                board_copy[r_move][c_move] = ai_mark 
                
                eval_score, _ = self._minimax_alpha_beta(board_copy, depth - 1, alpha, beta, False, ai_mark, human_mark) 
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move_for_this_call = (r_move, c_move)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break 
            return max_eval, best_move_for_this_call
        else: # Lượt của Người chơi (MIN)
            min_eval = sys.maxsize
            for r_move, c_move in possible_moves:
                board_copy = [row[:] for row in current_board_state]
                board_copy[r_move][c_move] = human_mark
                
                eval_score, _ = self._minimax_alpha_beta(board_copy, depth - 1, alpha, beta, True, ai_mark, human_mark)
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move_for_this_call = (r_move, c_move)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break 
            return min_eval, best_move_for_this_call

    # ... (Các hàm ai_greedy_move, ai_q_learning_move, ai_hill_climbing_move, ai_beam_search_move giữ nguyên) ...
    # ... (Hàm draw giữ nguyên) ...
    # --- (Sao chép các hàm AI và draw còn lại từ phiên bản trước của bạn vào đây) ---
    
    # Các hàm AI khác (greedy, q_learning, hill_climbing, beam_search) giữ nguyên từ phiên bản bạn cung cấp trước đó
    # Hàm draw() cũng giữ nguyên
    
    def ai_greedy_move(self): # Giữ lại từ code bạn cung cấp
        possible_moves = self.get_possible_moves()
        if not possible_moves: return None
        best_move = None
        best_score = -float('inf')

        for r_move, c_move in possible_moves:
            temp_board = [row[:] for row in self.board]
            temp_board[r_move][c_move] = self.ai_player_mark
            score = self.evaluate_board_heuristic(temp_board, self.ai_player_mark, True)
            score += random.uniform(-0.1, 0.1)
            if score > best_score:
                best_score = score
                best_move = (r_move, c_move)
        return best_move if best_move is not None else (random.choice(possible_moves) if possible_moves else None)

    def get_q_value(self, state_tuple, action_tuple): # Giữ lại từ code bạn cung cấp
        return self.q_table.get((state_tuple, action_tuple), 0.0) 

    def update_q_value(self, state_tuple, action_tuple, reward, next_state_tuple, is_terminal): # Giữ lại
        old_q_value = self.get_q_value(state_tuple, action_tuple)
        if is_terminal:
            target = reward
        else:
            next_possible_moves = self.get_possible_moves(list(list(row) for row in next_state_tuple))
            max_future_q = 0.0
            if next_possible_moves:
                 max_future_q = max([self.get_q_value(next_state_tuple, next_action) for next_action in next_possible_moves], default=0.0) # Thêm default
            target = reward + self.discount_factor * max_future_q
        new_q_value = old_q_value + self.learning_rate * (target - old_q_value)
        self.q_table[(state_tuple, action_tuple)] = new_q_value

    def ai_q_learning_move(self): # Giữ lại
        possible_moves = self.get_possible_moves()
        if not possible_moves: return None
        if random.uniform(0, 1) < self.exploration_rate:
            return random.choice(possible_moves) 
        else: 
            current_state_tuple = self.get_board_state_tuple()
            q_values = {move: self.get_q_value(current_state_tuple, move) for move in possible_moves}
            max_q = -float('inf')
            if not q_values: return random.choice(possible_moves) if possible_moves else None # Xử lý trường hợp q_values rỗng

            # Sửa lỗi có thể xảy ra nếu possible_moves rỗng sau khi q_values được tạo (ít khả năng)
            if not possible_moves: return None 
            
            is_all_same = True
            first_val = q_values[possible_moves[0]]
            for move in possible_moves:
                if q_values[move] != first_val:
                    is_all_same = False
                    break
            if is_all_same:
                 return random.choice(possible_moves)

            best_moves = []
            for move, q_val in q_values.items():
                if q_val > max_q:
                    max_q = q_val
                    best_moves = [move]
                elif q_val == max_q:
                    best_moves.append(move)
            return random.choice(best_moves) if best_moves else random.choice(possible_moves)

    def ai_hill_climbing_move(self, variant='steepest_ascent'): # Giữ lại
        possible_moves = self.get_possible_moves()
        if not possible_moves: return None
        current_board_score = self.evaluate_board_heuristic(self.board, self.ai_player_mark, True)
        best_move = None
        best_neighbor_score = current_board_score 
        
        for r_m, c_m in possible_moves: # Tránh trùng tên biến cục bộ với vòng lặp ngoài
            temp_board_win = [row[:] for row in self.board]
            temp_board_win[r_m][c_m] = self.ai_player_mark
            if self._check_win_on_board_at_coord(temp_board_win, self.ai_player_mark, r_m, c_m): # Sử dụng hàm check win mới
                return (r_m, c_m) 
        
        random.shuffle(possible_moves) 
        for r_move, c_move in possible_moves:
            temp_board = [row[:] for row in self.board]
            temp_board[r_move][c_move] = self.ai_player_mark
            neighbor_score = self.evaluate_board_heuristic(temp_board, self.ai_player_mark, True)
            if variant == 'simple':
                if neighbor_score > current_board_score:
                    return (r_move, c_move) 
            elif variant == 'steepest_ascent':
                if neighbor_score > best_neighbor_score: 
                    best_neighbor_score = neighbor_score
                    best_move = (r_move, c_move)
        if variant == 'steepest_ascent' and best_move is not None: 
            return best_move
        return random.choice(possible_moves) if possible_moves else None

    def ai_beam_search_move(self, beam_width=config.CARO_BEAM_WIDTH, depth=config.CARO_BEAM_DEPTH): # Giữ lại
        possible_first_moves = self.get_possible_moves()
        if not possible_first_moves: return None
        current_beam = [] 
        for r_move, c_move in possible_first_moves:
            temp_board = [row[:] for row in self.board]
            temp_board[r_move][c_move] = self.ai_player_mark
            if self._check_win_on_board_at_coord(temp_board, self.ai_player_mark, r_move,c_move): #Sử dụng hàm check win mới
                return (r_move,c_move) 
            score = self.evaluate_board_heuristic(temp_board, self.ai_player_mark, True)
            current_beam.append((score, [(r_move, c_move)])) 
        current_beam.sort(key=lambda x: x[0], reverse=True) 
        current_beam = current_beam[:beam_width]

        for d_ply in range(1, depth * 2): 
            next_beam_candidates = []
            is_ai_turn_in_simulation = (d_ply % 2 == 0) 
            current_sim_player_mark = self.human_player_mark if not is_ai_turn_in_simulation else self.ai_player_mark
            
            for _, move_sequence_so_far in current_beam:
                board_after_sequence = [row[:] for row in self.board]
                player_for_seq_step = self.ai_player_mark 
                for r_s, c_s in move_sequence_so_far:
                    if 0 <= r_s < self.board_size and 0 <= c_s < self.board_size and board_after_sequence[r_s][c_s] == 0:
                        board_after_sequence[r_s][c_s] = player_for_seq_step
                    player_for_seq_step = self.human_player_mark if player_for_seq_step == self.ai_player_mark else self.ai_player_mark
                
                possible_next_sim_moves = self.get_possible_moves(board_after_sequence)
                if not possible_next_sim_moves:
                    score = self.evaluate_board_heuristic(board_after_sequence, self.ai_player_mark, True)
                    next_beam_candidates.append((score, move_sequence_so_far))
                    continue

                for next_r, next_c in possible_next_sim_moves:
                    board_after_next_sim_move = [row[:] for row in board_after_sequence]
                    board_after_next_sim_move[next_r][next_c] = current_sim_player_mark
                    new_sequence = move_sequence_so_far + [(next_r, next_c)]
                    
                    if self._check_win_on_board_at_coord(board_after_next_sim_move, current_sim_player_mark, next_r, next_c): #Sử dụng hàm check win mới
                        if current_sim_player_mark == self.ai_player_mark: 
                            score = config.CARO_REWARD_WIN + depth 
                        else: 
                            score = config.CARO_REWARD_LOSS - depth
                    else: 
                        score = self.evaluate_board_heuristic(board_after_next_sim_move, self.ai_player_mark, True)
                    next_beam_candidates.append((score, new_sequence))

            if not next_beam_candidates: break 
            next_beam_candidates.sort(key=lambda x: x[0], reverse=True) 
            current_beam = next_beam_candidates[:beam_width]

        if current_beam:
            best_sequence_overall = current_beam[0][1] 
            return best_sequence_overall[0] 
        return random.choice(possible_first_moves) if possible_first_moves else None

    def draw(self, surface): # Giữ lại từ code bạn cung cấp
        if not self.is_active:
            return
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill(config.CARO_OVERLAY_COLOR)
        surface.blit(overlay, (0, 0))
        pygame.draw.rect(surface, config.CARO_BOARD_BG_COLOR, self.board_rect)
        for r in range(self.board_size):
            for c in range(self.board_size):
                rect = pygame.Rect(
                    self.board_rect.left + c * self.tile_size,
                    self.board_rect.top + r * self.tile_size,
                    self.tile_size, self.tile_size
                )
                pygame.draw.rect(surface, config.CARO_GRID_LINE_COLOR, rect, 1)
                mark = self.board[r][c]
                center_x = rect.centerx
                center_y = rect.centery
                radius = self.tile_size // 2 - 5 
                if mark == self.human_player_mark: 
                    pygame.draw.line(surface, config.CARO_X_COLOR, 
                                     (center_x - radius, center_y - radius), 
                                     (center_x + radius, center_y + radius), config.CARO_MARK_THICKNESS)
                    pygame.draw.line(surface, config.CARO_X_COLOR, 
                                     (center_x + radius, center_y - radius), 
                                     (center_x - radius, center_y + radius), config.CARO_MARK_THICKNESS)
                elif mark == self.ai_player_mark: 
                    pygame.draw.circle(surface, config.CARO_O_COLOR, rect.center, radius, config.CARO_MARK_THICKNESS)
        if self.game_over and self.winner is not None and self.winner != 0 and self.winning_line:
            if len(self.winning_line) >= 2: # Đảm bảo có ít nhất 2 điểm
                # Chuyển đổi tọa độ ô sang tọa độ pixel cho điểm đầu và cuối của đường thắng
                start_board_r, start_board_c = self.winning_line[0]
                end_board_r, end_board_c = self.winning_line[-1]
                
                start_pixel_x = self.board_rect.left + start_board_c * self.tile_size + self.tile_size // 2
                start_pixel_y = self.board_rect.top + start_board_r * self.tile_size + self.tile_size // 2
                end_pixel_x = self.board_rect.left + end_board_c * self.tile_size + self.tile_size // 2
                end_pixel_y = self.board_rect.top + end_board_r * self.tile_size + self.tile_size // 2
                
                pygame.draw.line(surface, config.CARO_WIN_LINE_COLOR, 
                                 (start_pixel_x, start_pixel_y), 
                                 (end_pixel_x, end_pixel_y), config.CARO_WIN_LINE_THICKNESS)
        if self.message: 
            msg_color_to_use = self.message_color if self.game_over else config.WHITE
            msg_surface = self.message_font.render(self.message, True, msg_color_to_use)
            msg_rect = msg_surface.get_rect(center=(self.screen_width // 2, self.board_rect.top - 30))
            surface.blit(msg_surface, msg_rect)