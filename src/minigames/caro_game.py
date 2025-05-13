import pygame
import random
import math 
import sys 
import src.config as config
from .base_minigame import BaseMiniGame 

class CaroGame(BaseMiniGame):
    def __init__(self, screen_width, screen_height, ui_manager, 
                 board_size=config.CARO_BOARD_SIZE, 
                 win_length=config.CARO_WIN_LENGTH):
        super().__init__(screen_width, screen_height, ui_manager) 
        
        self.board_size = board_size
        self.win_length = win_length
        self.tile_size = config.CARO_TILE_SIZE

        self.board_pixel_width = self.board_size * self.tile_size
        self.board_pixel_height = self.board_size * self.tile_size

        self.board_rect = pygame.Rect(
            (self.screen_width - self.board_pixel_width) // 2,
            (self.screen_height - self.board_pixel_height) // 2 + 20,
            self.board_pixel_width,
            self.board_pixel_height
        )

        try:
            self.mark_font = pygame.font.Font(config.DEFAULT_FONT_PATH, config.CARO_FONT_SIZE) 
        except pygame.error as e:
            print(f"Lỗi khởi tạo font cho Caro: {e}. Sử dụng font hệ thống.")
            self.mark_font = pygame.font.SysFont(None, config.CARO_FONT_SIZE)

        self.board = [] 
        self.current_player_mark = 1 
        self.winner_mark = None 
        self.winning_line_coords = [] 

        self.ai_player_mark = 2
        self.human_player_mark = 1
        self.ai_difficulty = config.DEFAULT_CARO_AI
        
        self.display_message = ""      
        self.display_message_timer = 0 
        self.display_message_color = config.WHITE

        self.q_table_caro = {} 
        self.learning_rate = config.CARO_QL_LEARNING_RATE
        self.discount_factor = config.CARO_QL_DISCOUNT_FACTOR
        self.exploration_rate = config.CARO_QL_EXPLORATION_RATE 
        self.last_ai_state_action_caro = None

    def start_game(self): 
        super().start_game() 
        self.board = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.current_player_mark = self.human_player_mark 
        self.winner_mark = None
        self.winning_line_coords = []
        self.display_message = "Lượt của bạn (X)"
        self.display_message_color = config.WHITE
        self.display_message_timer = 0 
        self.last_ai_state_action_caro = None
        print(f"Caro game started. AI: {self.ai_difficulty}. Player is X.")

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


    def make_move(self, row, col, player_mark, board_state_to_modify=None):
        target_board = board_state_to_modify if board_state_to_modify is not None else self.board
        is_actual_move_on_game_board = (board_state_to_modify is None)

        if 0 <= row < self.board_size and 0 <= col < self.board_size and target_board[row][col] == 0:
            target_board[row][col] = player_mark
            
            if is_actual_move_on_game_board: 
                self._check_game_status(player_mark, (row, col)) 
                if not self.is_active: 
                    pass 
                else: 
                    self.current_player_mark = self.ai_player_mark if player_mark == self.human_player_mark else self.human_player_mark
                    self.display_message = "Lượt của AI (O)" if self.current_player_mark == self.ai_player_mark else "Lượt của bạn (X)"
                    self.display_message_color = config.WHITE
            return True
        return False


    def _check_win_on_board_at_coord(self, board_to_check, mark, r_coord, c_coord):
        if not (0 <= r_coord < self.board_size and 0 <= c_coord < self.board_size and board_to_check[r_coord][c_coord] == mark):
            return [] 
        orientations = [(0, 1), (1, 0), (1, 1), (1, -1)] 
        for dr, dc in orientations:
            line = [(r_coord, c_coord)]
            for i in range(1, self.win_length):
                nr, nc = r_coord + i * dr, c_coord + i * dc
                if 0 <= nr < self.board_size and 0 <= nc < self.board_size and board_to_check[nr][nc] == mark:
                    line.append((nr,nc))
                else: break
            for i in range(1, self.win_length):
                nr, nc = r_coord - i * dr, c_coord - i * dc
                if 0 <= nr < self.board_size and 0 <= nc < self.board_size and board_to_check[nr][nc] == mark:
                    line.insert(0, (nr,nc)) 
                else: break
            
            if len(line) >= self.win_length:
                for i in range(len(line) - self.win_length + 1):
                    sub_line = line[i:i+self.win_length]
                    if len(sub_line) == self.win_length:
                        return sub_line 
        return []


    def _check_game_status(self, player_mark, last_move_coords): 
        r, c = last_move_coords
        winning_actual_line = self._check_win_on_board_at_coord(self.board, player_mark, r, c)

        if winning_actual_line:
            self.is_active = False 
            self.won = (player_mark == self.human_player_mark) 
            self.winner_mark = player_mark
            self.winning_line_coords = winning_actual_line 
            self.display_message = f"{'Bạn (X)' if player_mark == self.human_player_mark else 'AI (O)'} thắng!"
            self.display_message_color = config.GREEN if player_mark == self.human_player_mark else config.RED
            self.display_message_timer = 5 
            return

        if self.check_draw(): 
            self.is_active = False 
            self.won = False       
            self.winner_mark = 0   
            self.display_message = "Hòa!"
            self.display_message_color = config.YELLOW
            self.display_message_timer = 5
            return

    def check_draw(self, board_state=None):
        current_b = board_state if board_state is not None else self.board
        for r in range(self.board_size):
            for c in range(self.board_size):
                if current_b[r][c] == 0:
                    return False
        return True


    def handle_event(self, event):
        if super().handle_event(event): 
            return True 

        if not self.is_active: 
            if self.display_message_timer <=0 and (self.winner_mark is not None) and \
               (event.type == pygame.MOUSEBUTTONDOWN or (event.type == pygame.KEYDOWN and event.key != pygame.K_ESCAPE)):
                return True 
            return False 

        if self.current_player_mark == self.human_player_mark:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_x, mouse_y = event.pos
                if self.board_rect.collidepoint(mouse_x, mouse_y):
                    clicked_col = (mouse_x - self.board_rect.left) // self.tile_size
                    clicked_row = (mouse_y - self.board_rect.top) // self.tile_size
                    
                    if self.make_move(clicked_row, clicked_col, self.human_player_mark):
                        if not self.is_active: 
                            return True 
        return False 

    def update(self, dt):
        if not self.is_active: 
            if self.display_message_timer > 0:
                self.display_message_timer -= dt
                if self.display_message_timer <= 0:
                    self.display_message_timer = 0
            return not self.is_active 

        if self.display_message_timer > 0:
            self.display_message_timer -= dt
            if self.display_message_timer < 0: 
                self.display_message_timer = 0
                if self.winner_mark is None: 
                     self.display_message = "Lượt của AI (O)" if self.current_player_mark == self.ai_player_mark else "Lượt của bạn (X)"
                     self.display_message_color = config.WHITE
        
        if self.current_player_mark == self.ai_player_mark and self.is_active:
            self.ai_take_turn()
            if not self.is_active: 
                return True 

        return False 

    def ai_take_turn(self):
        if not self.is_active : return 
        print(f"AI ({self.ai_difficulty}) is thinking...")
        pygame.event.pump() 

        move = None 
        if self.ai_difficulty == 'random': move = self.ai_random_move()
        elif self.ai_difficulty == 'greedy': move = self.ai_greedy_move()
        elif self.ai_difficulty == 'minimax': move = self.ai_minimax_move(depth=config.CARO_MINIMAX_DEPTH)
        else: move = self.ai_random_move()

        if move:
            self.make_move(move[0], move[1], self.ai_player_mark)
        elif not self.get_possible_moves(): 
            print("AI không còn nước đi, xử lý hòa.")
            self.is_active = False
            self.won = False
            self.winner_mark = 0 
            self.display_message = "Hòa! (AI hết nước)"
            self.display_message_color = config.YELLOW
            self.display_message_timer = 5
    
    def ai_random_move(self):
        possible_moves = self.get_possible_moves()
        return random.choice(possible_moves) if possible_moves else None

    def evaluate_board_heuristic(self, board_state, player_to_evaluate_for, is_maximizing_call):
        ai_score = self._calculate_player_potential_score(board_state, self.ai_player_mark, self.human_player_mark)
        human_score = self._calculate_player_potential_score(board_state, self.human_player_mark, self.ai_player_mark)
        final_score = ai_score - human_score * 1.5 
        return final_score

    def _calculate_player_potential_score(self, board, mark, opponent_mark):
        score = 0
        weights = {
            (self.win_length, True): config.CARO_REWARD_WIN * 100, 
            (self.win_length - 1, True): 5000,  
            (self.win_length - 1, False): 1000, 
            (self.win_length - 2, True): 500,   
            (self.win_length - 2, False): 100,  
            (self.win_length - 3, True): 50,    
            (self.win_length - 3, False): 10,   
        } 
        orientations = [(0, 1), (1, 0), (1, 1), (1, -1)]
        checked_lines = set()
        for r in range(self.board_size):
            for c in range(self.board_size):
                if board[r][c] == mark:
                    for dr, dc in orientations:
                        line_coords = []
                        current_marks_in_line = 0
                        for i in range(self.win_length):
                            nr, nc = r + i * dr, c + i * dc
                            if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                                if board[nr][nc] == mark: 
                                    current_marks_in_line += 1
                                    line_coords.append((nr,nc))
                                elif board[nr][nc] == opponent_mark: current_marks_in_line = -self.win_length*2 ; break 
                                else: break 
                            else: break 
                        
                        if current_marks_in_line < 0 : continue 

                        open_ends_count = 0
                        prev_r, prev_c = r - dr, c - dc
                        if 0 <= prev_r < self.board_size and 0 <= prev_c < self.board_size and board[prev_r][prev_c] == 0:
                            open_ends_count +=1
                        elif not (0 <= prev_r < self.board_size and 0 <= prev_c < self.board_size): 
                            open_ends_count +=1 
                        
                        last_r_in_seq, last_c_in_seq = r + (current_marks_in_line-1)*dr, c + (current_marks_in_line-1)*dc
                        next_r, next_c = last_r_in_seq + dr, last_c_in_seq + dc
                        if 0 <= next_r < self.board_size and 0 <= next_c < self.board_size and board[next_r][next_c] == 0:
                            open_ends_count +=1
                        elif not (0 <= next_r < self.board_size and 0 <= next_c < self.board_size):
                            open_ends_count +=1

                        if current_marks_in_line > 0 :
                            sorted_line_key = tuple(sorted(line_coords))
                            if sorted_line_key not in checked_lines :
                                if current_marks_in_line == self.win_length: 
                                    score += weights.get((current_marks_in_line, True), 100000) 
                                else:
                                    if open_ends_count == 2: 
                                        score += weights.get((current_marks_in_line, True),0) * 2 
                                    elif open_ends_count == 1: 
                                        score += weights.get((current_marks_in_line, True),0)
                                checked_lines.add(sorted_line_key)
        return score


    def ai_minimax_move(self, depth=config.CARO_MINIMAX_DEPTH):
        _, move = self._minimax_alpha_beta(self.board, depth, -sys.maxsize, sys.maxsize, True, self.ai_player_mark, self.human_player_mark)
        if move is None: 
            return self.ai_random_move()
        return move

    def _minimax_alpha_beta(self, current_board_state, depth, alpha, beta, is_maximizing_player, ai_mark, human_mark):
        possible_moves_check = self.get_possible_moves(current_board_state)
        is_draw_check = not possible_moves_check 
        
        def get_move_priority(move):
            return abs(move[0] - self.board_size // 2) + abs(move[1] - self.board_size // 2)

        if possible_moves_check:
            possible_moves_check.sort(key=get_move_priority)


        if is_maximizing_player:
            for r_test, c_test in possible_moves_check:
                if self._check_win_on_board_at_coord(current_board_state, ai_mark, r_test, c_test): 
                    temp_board_ai_win = [row[:] for row in current_board_state]
                    temp_board_ai_win[r_test][c_test] = ai_mark
                    if self._check_win_on_board_at_coord(temp_board_ai_win, ai_mark, r_test, c_test):
                        return config.CARO_REWARD_WIN + depth * 100, (r_test,c_test) 

        if not is_maximizing_player: 
            for r_test, c_test in possible_moves_check:
                temp_board_human_win = [row[:] for row in current_board_state]
                temp_board_human_win[r_test][c_test] = human_mark
                if self._check_win_on_board_at_coord(temp_board_human_win, human_mark, r_test, c_test):
                     return config.CARO_REWARD_LOSS - depth * 100, (r_test,c_test) 


        if depth == 0 or is_draw_check :
            if is_draw_check and not (any(self._check_win_on_board_at_coord(current_board_state, m, r,c) for m in [ai_mark, human_mark] for r in range(self.board_size) for c in range(self.board_size) if current_board_state[r][c]==m )):
                return config.CARO_REWARD_DRAW, None
            return self.evaluate_board_heuristic(current_board_state, ai_mark, True), None 

        best_move_for_this_call = possible_moves_check[0] if possible_moves_check else None

        if is_maximizing_player:
            max_eval = -float('inf')
            for r_move, c_move in possible_moves_check:
                board_copy = [row[:] for row in current_board_state]
                board_copy[r_move][c_move] = ai_mark
                eval_score, _ = self._minimax_alpha_beta(board_copy, depth - 1, alpha, beta, False, ai_mark, human_mark)
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move_for_this_call = (r_move, c_move)
                alpha = max(alpha, eval_score)
                if beta <= alpha: break
            return max_eval, best_move_for_this_call
        else:
            min_eval = float('inf')
            for r_move, c_move in possible_moves_check:
                board_copy = [row[:] for row in current_board_state]
                board_copy[r_move][c_move] = human_mark
                eval_score, _ = self._minimax_alpha_beta(board_copy, depth - 1, alpha, beta, True, ai_mark, human_mark)
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move_for_this_call = (r_move, c_move)
                beta = min(beta, eval_score)
                if beta <= alpha: break
            return min_eval, best_move_for_this_call
    
    def ai_greedy_move(self): 
        possible_moves = self.get_possible_moves()
        if not possible_moves: return None
        best_move = None
        best_score = -float('inf')
        for r_move, c_move in possible_moves:
            temp_board = [row[:] for row in self.board]
            temp_board[r_move][c_move] = self.ai_player_mark
            if self._check_win_on_board_at_coord(temp_board, self.ai_player_mark,r_move,c_move ): return (r_move, c_move)
            temp_board_block = [row[:] for row in self.board]
            temp_board_block[r_move][c_move] = self.human_player_mark 
            
            score = self.evaluate_board_heuristic(temp_board, self.ai_player_mark, True) 
            score += random.uniform(-0.1, 0.1) 
            if score > best_score:
                best_score = score
                best_move = (r_move, c_move)
        
        for r_block, c_block in possible_moves:
            temp_board_human_win = [row[:] for row in self.board]
            temp_board_human_win[r_block][c_block] = self.human_player_mark
            if self._check_win_on_board_at_coord(temp_board_human_win, self.human_player_mark,r_block,c_block):
                return (r_block, c_block) 

        return best_move if best_move is not None else (random.choice(possible_moves) if possible_moves else None)


    def get_q_value(self, state_tuple, action_tuple): 
        return self.q_table_caro.get((state_tuple, action_tuple), 0.0)

    def update_q_value(self, state_tuple, action_tuple, reward, next_state_tuple, is_terminal): 
        old_q_value = self.get_q_value(state_tuple, action_tuple)
        if is_terminal:
            target = reward
        else:
            next_possible_moves = self.get_possible_moves(list(list(row) for row in next_state_tuple))
            max_future_q = 0.0
            if next_possible_moves:
                max_future_q = max([self.get_q_value(next_state_tuple, next_action) for next_action in next_possible_moves], default=0.0)
            target = reward + self.discount_factor * max_future_q
        new_q_value = old_q_value + self.learning_rate * (target - old_q_value)
        self.q_table_caro[(state_tuple, action_tuple)] = new_q_value
        
    def ai_q_learning_move(self):
        possible_moves = self.get_possible_moves()
        if not possible_moves: return None
        if random.uniform(0, 1) < self.exploration_rate:
            return random.choice(possible_moves) 
        else: 
            current_state_tuple = self.get_board_state_tuple()
            q_values = {move: self.get_q_value(current_state_tuple, move) for move in possible_moves}
            if not q_values: return random.choice(possible_moves) if possible_moves else None
            max_q = -float('inf')
            is_all_same = True
            first_val = q_values[possible_moves[0]] if possible_moves else 0 
            for move in possible_moves:
                if q_values[move] != first_val:
                    is_all_same = False; break
            if is_all_same: return random.choice(possible_moves)

            best_moves = []
            for move, q_val in q_values.items():
                if q_val > max_q:
                    max_q = q_val
                    best_moves = [move]
                elif q_val == max_q:
                    best_moves.append(move)
            return random.choice(best_moves) if best_moves else (random.choice(possible_moves) if possible_moves else None)


    def ai_hill_climbing_move(self, variant='steepest_ascent'): 
        possible_moves = self.get_possible_moves()
        if not possible_moves: return None
        
        for r_m, c_m in possible_moves:
            temp_board_win = [row[:] for row in self.board]
            temp_board_win[r_m][c_m] = self.ai_player_mark
            if self._check_win_on_board_at_coord(temp_board_win, self.ai_player_mark,r_m,c_m):
                return (r_m, c_m)
        
        for r_m, c_m in possible_moves:
            temp_board_block = [row[:] for row in self.board]
            temp_board_block[r_m][c_m] = self.human_player_mark
            if self._check_win_on_board_at_coord(temp_board_block, self.human_player_mark,r_m,c_m):
                return (r_m, c_m) 

        current_board_score = self.evaluate_board_heuristic(self.board, self.ai_player_mark, True)
        best_move = None
        best_neighbor_score = current_board_score 
        
        shuffled_moves = list(possible_moves) 
        random.shuffle(shuffled_moves) 

        for r_move, c_move in shuffled_moves:
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
        
        if variant == 'steepest_ascent' and best_move is not None and best_neighbor_score > current_board_score : 
            return best_move
        return random.choice(possible_moves) if possible_moves else None


    def ai_beam_search_move(self, beam_width=config.CARO_BEAM_WIDTH, depth=config.CARO_BEAM_DEPTH): 
        possible_first_moves = self.get_possible_moves()
        if not possible_first_moves: return None
        current_beam = [] 
        for r_move, c_move in possible_first_moves:
            temp_board = [row[:] for row in self.board]
            temp_board[r_move][c_move] = self.ai_player_mark
            if self._check_win_on_board_at_coord(temp_board, self.ai_player_mark,r_move,c_move): return (r_move,c_move) 
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
                valid_sequence = True
                for r_s, c_s in move_sequence_so_far:
                    if 0 <= r_s < self.board_size and 0 <= c_s < self.board_size and board_after_sequence[r_s][c_s] == 0:
                        board_after_sequence[r_s][c_s] = player_for_seq_step
                    else: valid_sequence = False; break
                    player_for_seq_step = self.human_player_mark if player_for_seq_step == self.ai_player_mark else self.ai_player_mark
                if not valid_sequence: continue
                
                possible_next_sim_moves = self.get_possible_moves(board_after_sequence)
                if not possible_next_sim_moves:
                    score = self.evaluate_board_heuristic(board_after_sequence, self.ai_player_mark, True)
                    next_beam_candidates.append((score, move_sequence_so_far))
                    continue

                for next_r, next_c in possible_next_sim_moves:
                    board_after_next_sim_move = [row[:] for row in board_after_sequence]
                    board_after_next_sim_move[next_r][next_c] = current_sim_player_mark
                    new_sequence = move_sequence_so_far + [(next_r, next_c)]
                    
                    if self._check_win_on_board_at_coord(board_after_next_sim_move, current_sim_player_mark,next_r,next_c):
                        score = config.CARO_REWARD_WIN + depth if current_sim_player_mark == self.ai_player_mark else config.CARO_REWARD_LOSS - depth
                    else: 
                        score = self.evaluate_board_heuristic(board_after_next_sim_move, self.ai_player_mark, True)
                    next_beam_candidates.append((score, new_sequence))
            if not next_beam_candidates: break 
            next_beam_candidates.sort(key=lambda x: x[0], reverse=is_ai_turn_in_simulation) 
            current_beam = next_beam_candidates[:beam_width]

        if current_beam:
            best_sequence_overall = current_beam[0][1] 
            return best_sequence_overall[0] 
        return random.choice(possible_first_moves) if possible_first_moves else None


    def draw(self, surface, main_game_time_remaining): 
        super().draw(surface, main_game_time_remaining) 

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
                center_x, center_y = rect.centerx, rect.centery
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
        
        if self.winner_mark is not None and self.winner_mark != 0 and self.winning_line_coords:
            if len(self.winning_line_coords) >= 2:
                start_cell = self.winning_line_coords[0]
                end_cell = self.winning_line_coords[-1]
                
                start_pixel_x = self.board_rect.left + start_cell[1] * self.tile_size + self.tile_size // 2
                start_pixel_y = self.board_rect.top + start_cell[0] * self.tile_size + self.tile_size // 2
                end_pixel_x = self.board_rect.left + end_cell[1] * self.tile_size + self.tile_size // 2
                end_pixel_y = self.board_rect.top + end_cell[0] * self.tile_size + self.tile_size // 2
                
                pygame.draw.line(surface, config.CARO_WIN_LINE_COLOR, 
                                 (start_pixel_x, start_pixel_y), 
                                 (end_pixel_x, end_pixel_y), config.CARO_WIN_LINE_THICKNESS)

        if self.display_message: 
            msg_surf = self.font.render(self.display_message, True, self.display_message_color) 
            msg_rect = msg_surf.get_rect(center=(self.screen_width // 2, self.board_rect.top - 25)) 
            surface.blit(msg_surf, msg_rect)