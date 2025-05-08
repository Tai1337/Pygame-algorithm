# eight_puzzle_game.py
import pygame
import random

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
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font = pygame.font.Font(None, 50)
        self.solved_board = [[1, 2, 3], [4, 5, 6], [7, 8, 0]]
        self.board = []
        self.empty_pos = None
        self.is_active = False

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
        self.just_won = False  # <<<< THÊM CỜ NÀY
        self.win_processed_in_main = False # <<<< THÊM CỜ NÀY (để main.py chỉ xử lý thắng 1 lần)


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
                self.just_won = False # <<<< RESET KHI TẠO PUZZLE MỚI
                self.win_processed_in_main = False # <<<< RESET
                if self.board != self.solved_board:
                    break

    def start_game(self):
        self._generate_solvable_puzzle()
        self.is_active = True
        self.win_message = ""
        self.win_message_timer = 0
        self.just_won = False # <<<< RESET KHI BẮT ĐẦU
        self.win_processed_in_main = False # <<<< RESET
        print("8-Puzzle game started. Board:", self.board)

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
        # Không cho di chuyển nữa nếu cờ just_won đã được đặt (chờ main.py xử lý)
        # hoặc nếu game không active
        if not self.is_active or self.just_won:
            return

        er, ec = self.empty_pos
        if (abs(r - er) == 1 and c == ec) or (abs(c - ec) == 1 and r == er):
            self.board[er][ec] = self.board[r][c]
            self.board[r][c] = 0
            self.empty_pos = (r, c)
            if self.check_win(): # Không cần self.just_won ở đây nữa, vì đã check ở trên
                self.win_message = "victory!"
                self.win_message_timer = 3 # Thời gian hiển thị thông báo
                self.just_won = True      # <<<< BÁO HIỆU ĐÃ THẮNG
                print("Puzzle solved! Signalling win.")

    def check_win(self):
        return self.board == self.solved_board

    def handle_event(self, event):
        if not self.is_active:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Nếu đã thắng và thông báo đang hiển thị, click chuột sẽ đóng puzzle
            if self.check_win() and self.win_message_timer > 0 :
                self.is_active = False
                return True # Báo hiệu puzzle nên đóng

            # Nếu chưa thắng (hoặc thông báo thắng chưa hiện/đã tắt), xử lý di chuyển ô
            if not self.just_won: # Chỉ cho phép di chuyển nếu chưa thắng (just_won)
                clicked_tile_pos = self.get_tile_at_mouse_pos(*event.pos)
                if clicked_tile_pos:
                    self.move_tile(*clicked_tile_pos) # move_tile sẽ set just_won nếu thắng
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.is_active = False
                return True # Báo hiệu puzzle nên đóng (thất bại)
        return False

    def update(self, dt):
        if self.win_message_timer > 0:
            self.win_message_timer -= dt
            if self.win_message_timer <= 0:
                if self.check_win(): # Nếu đã thắng và hết giờ thông báo, tự đóng puzzle
                    self.is_active = False
        # self.just_won sẽ được main.py reset sau khi xử lý (qua self.win_processed_in_main)

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
                    pygame.draw.rect(puzzle_surface, BLACK, rect)
        if self.win_message_timer > 0 and self.win_message: # Hiển thị thông báo nếu có
            msg_surf = self.message_font.render(self.win_message, True, WHITE)
            msg_rect = msg_surf.get_rect(center=(self.puzzle_width // 2, self.puzzle_height - 30))
            puzzle_surface.blit(msg_surf, msg_rect)
        surface.blit(puzzle_surface, self.puzzle_rect.topleft)