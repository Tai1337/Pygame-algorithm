import pygame
import pygame_gui
import random
from .base_minigame import BaseMiniGame
import src.config as config

class SudokuGame(BaseMiniGame):
    def __init__(self, screen_width, screen_height, ui_manager):
        super().__init__(screen_width, screen_height, ui_manager)
        self.grid_dimension = config.SUDOKU_GRID_SIZE
        self.cell_size = config.SUDOKU_CELL_SIZE
        self.grid_size = self.grid_dimension * self.cell_size
        self.width, self.height = self.grid_size, self.grid_size + 120
        self.time_limit = config.SUDOKU_TIME_LIMIT
        self.time_remaining = self.time_limit

        try:
            self.font_cell = pygame.font.Font(None, int(self.cell_size * 0.7))
            self.font_button = pygame.font.Font(None, 24)
            self.font_message = pygame.font.Font(None, 20)
            self.font_timer = pygame.font.Font(None, 20)  # Giảm từ 28 xuống 20
        except pygame.error:
            self.font_cell = pygame.font.SysFont("Consolas", int(self.cell_size * 0.7), bold=True)
            self.font_button = pygame.font.SysFont("Arial", 24)
            self.font_message = pygame.font.SysFont("Arial", 20)
            self.font_timer = pygame.font.SysFont("Arial", 20)  # Giảm từ 28 xuống 20

        self.board_initial = [[0] * self.grid_dimension for _ in range(self.grid_dimension)]
        self.board_current = [[0] * self.grid_dimension for _ in range(self.grid_dimension)]
        self.board_solved_overlay = [[0] * self.grid_dimension for _ in range(self.grid_dimension)]
        self.selected_cell = None
        self.is_solving = False
        self.solved_by_ai = False
        self.solve_ai_button = None
        self.confirm_button = None

        self.puzzle_rect = pygame.Rect(
            (self.screen_width - self.grid_size) // 2,
            (self.screen_height - self.height) // 2,
            self.grid_size, self.grid_size
        )

    def start_game(self):
        super().start_game()
        self._generate_random_board()
        self.board_current = [row[:] for row in self.board_initial]
        self.board_solved_overlay = [[0] * self.grid_dimension for _ in range(self.grid_dimension)]
        self.selected_cell = None
        self.is_solving = False
        self.solved_by_ai = False
        self.time_remaining = self.time_limit
        self.cleanup_ui()
        self._create_ai_button()

    def _generate_random_board(self):
        self.board_initial = [[0] * self.grid_dimension for _ in range(self.grid_dimension)]
        self._fill_diagonal()
        self.solve_sudoku_recursive(self.board_initial)
        full_board = [row[:] for row in self.board_initial]
        num_clues = random.randint(6, 8)
        cells = [(i, j) for i in range(self.grid_dimension) for j in range(self.grid_dimension)]
        random.shuffle(cells)
        for i, (row, col) in enumerate(cells):
            if i >= self.grid_dimension * self.grid_dimension - num_clues:
                break
            self.board_initial[row][col] = 0

    def _fill_diagonal(self):
        for box in range(0, self.grid_dimension, 2):
            nums = list(range(1, self.grid_dimension + 1))
            random.shuffle(nums)
            idx = 0
            for i in range(box, box + 2):
                for j in range(box, box + 2):
                    self.board_initial[i][j] = nums[idx]
                    idx += 1

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
            object_id="#solve_ai_sudoku_button"
        )

    def _create_confirm_button(self):
        if self.confirm_button and self.confirm_button.alive():
            self.confirm_button.enable()
            self.confirm_button.show()
            return
        button_rect_x = self.puzzle_rect.centerx - config.CONFIRM_BUTTON_WIDTH // 2
        button_rect_y = self.puzzle_rect.bottom + config.SOLVE_AI_BUTTON_MARGIN_TOP + config.SOLVE_AI_BUTTON_HEIGHT + 10
        self.confirm_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(button_rect_x, button_rect_y, config.CONFIRM_BUTTON_WIDTH, config.CONFIRM_BUTTON_HEIGHT),
            text=config.CONFIRM_BUTTON_TEXT,
            manager=self.ui_manager,
            object_id="#confirm_sudoku_button"
        )

    def cleanup_ui(self):
        super().cleanup_ui()
        if self.solve_ai_button and self.solve_ai_button.alive():
            self.solve_ai_button.kill()
        if self.confirm_button and self.confirm_button.alive():
            self.confirm_button.kill()
        self.solve_ai_button = None
        self.confirm_button = None

    def find_empty_location(self, board):
        for i in range(self.grid_dimension):
            for j in range(self.grid_dimension):
                if board[i][j] == 0:
                    return (i, j)
        return None

    def is_valid(self, board, num, pos):
        row, col = pos
        for j in range(self.grid_dimension):
            if board[row][j] == num and col != j:
                return False
        for i in range(self.grid_dimension):
            if board[i][col] == num and row != i:
                return False
        box_x = col // 2
        box_y = row // 2
        for i in range(box_y * 2, box_y * 2 + 2):
            for j in range(box_x * 2, box_x * 2 + 2):
                if board[i][j] == num and (i, j) != pos:
                    return False
        return True

    def solve_sudoku_recursive(self, board, visual=False):
        empty_pos = self.find_empty_location(board)
        if not empty_pos:
            return True
        row, col = empty_pos
        for num in range(1, self.grid_dimension + 1):
            if visual:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return "QUIT"
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.is_solving = False
                        return False
            if self.is_valid(board, num, (row, col)):
                board[row][col] = num
                if visual:
                    self.board_solved_overlay[row][col] = num
                    pygame.display.flip()
                    pygame.time.delay(int(config.SUDOKU_AI_STEP_DURATION * 1000))
                if self.solve_sudoku_recursive(board, visual):
                    if visual:
                        self.board_solved_overlay[row][col] = num
                        pygame.display.flip()
                        pygame.time.delay(int(config.SUDOKU_AI_STEP_DURATION * 1000))
                    return True
                board[row][col] = 0
                if visual:
                    self.board_solved_overlay[row][col] = 0
                    pygame.display.flip()
                    pygame.time.delay(int(config.SUDOKU_AI_STEP_DURATION * 1000))
        return False

    def attempt_ai_solve(self):
        if self.won or self.solved_by_ai or self.is_solving:
            return
        print("Attempting AI solve for Sudoku 4x4...")
        self.is_solving = True
        board_to_solve = [row[:] for row in self.board_current]
        self.board_solved_overlay = [[0] * self.grid_dimension for _ in range(self.grid_dimension)]
        result = self.solve_sudoku_recursive(board_to_solve, visual=True)
        self.is_solving = False
        if result == "QUIT" or result is False:
            self.solved_by_ai = False
            if self.solve_ai_button and self.solve_ai_button.alive():
                self.solve_ai_button.enable()
        else:
            self.board_current = [row[:] for row in board_to_solve]
            self.board_solved_overlay = [[0] * self.grid_dimension for _ in range(self.grid_dimension)]
            self.won = True
            self.solved_by_ai = True
            if self.solve_ai_button and self.solve_ai_button.alive():
                self.solve_ai_button.disable()
            self._create_confirm_button()
        pygame.display.flip()

    def check_win(self):
        for r in range(self.grid_dimension):
            for c in range(self.grid_dimension):
                if self.board_current[r][c] == 0:
                    return False
                temp_board = [row[:] for row in self.board_current]
                temp_board[r][c] = 0
                if not self.is_valid(temp_board, self.board_current[r][c], (r, c)):
                    return False
        return True

    def handle_event(self, event):
        if super().handle_event(event):
            self.cleanup_ui()
            return True
        if not self.is_active:
            return True
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if self.solve_ai_button and self.solve_ai_button.alive() and event.ui_element == self.solve_ai_button:
                if not self.won and not self.solved_by_ai and not self.is_solving:
                    return config.PUZZLE_EVENT_AI_SOLVE_REQUEST
                return False
            if self.confirm_button and self.confirm_button.alive() and event.ui_element == self.confirm_button:
                self.is_active = False
                self.cleanup_ui()
                return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_solving or (self.won and self.solved_by_ai):
                return False
            mx, my = event.pos
            if self.puzzle_rect.collidepoint(mx, my):
                local_x = mx - self.puzzle_rect.left
                local_y = my - self.puzzle_rect.top
                grid_r = local_y // self.cell_size
                grid_c = local_x // self.cell_size
                if 0 <= grid_r < self.grid_dimension and 0 <= grid_c < self.grid_dimension:
                    self.selected_cell = (grid_r, grid_c)
                else:
                    self.selected_cell = None
        if event.type == pygame.KEYDOWN:
            if self.is_solving or (self.won and self.solved_by_ai):
                return False
            if self.selected_cell:
                r, c = self.selected_cell
                if self.board_initial[r][c] == 0:
                    if pygame.K_1 <= event.key <= pygame.K_4:
                        num_entered = event.key - pygame.K_0
                        temp_board_check = [row[:] for row in self.board_current]
                        temp_board_check[r][c] = num_entered
                        self.board_current[r][c] = num_entered
                        self.board_solved_overlay[r][c] = 0
                    elif event.key in (pygame.K_BACKSPACE, pygame.K_DELETE, pygame.K_0):
                        self.board_current[r][c] = 0
                        self.board_solved_overlay[r][c] = 0
                    if self.check_win():
                        self.won = True
                        self.is_active = False
                        if self.solve_ai_button and self.solve_ai_button.alive():
                            self.solve_ai_button.disable()
                        self.cleanup_ui()
                        return True
            if event.key == pygame.K_ESCAPE:
                if not self.is_solving and not (self.won and self.solved_by_ai):
                    self.selected_cell = None
        return False

    def update(self, dt):
        if not self.is_active:
            return True
        if self.won and not self.solved_by_ai:
            return True
        if self.time_remaining <= 0:
            self.won = False
            self.is_active = False
            self.cleanup_ui()
            return True
        self.time_remaining -= dt
        if self.solve_ai_button and self.solve_ai_button.alive():
            if self.won or self.is_solving:
                if self.solve_ai_button.is_enabled:
                    self.solve_ai_button.disable()
            else:
                if not self.solve_ai_button.is_enabled:
                    self.solve_ai_button.enable()
        if self.confirm_button and self.confirm_button.alive():
            if not (self.won and self.solved_by_ai):
                if self.confirm_button.is_enabled:
                    self.confirm_button.disable()
            else:
                if not self.confirm_button.is_enabled:
                    self.confirm_button.enable()
        return False

    def draw(self, surface, main_game_time_remaining):
        super().draw(surface, main_game_time_remaining)
        puzzle_surface = pygame.Surface((self.grid_size, self.height), pygame.SRCALPHA)
        puzzle_surface.fill(config.WHITE)

        for r in range(self.grid_dimension):
            for c in range(self.grid_dimension):
                rect = pygame.Rect(c * self.cell_size, r * self.cell_size, self.cell_size, self.cell_size)
                if self.selected_cell and self.selected_cell == (r, c) and not (self.won and self.solved_by_ai):
                    pygame.draw.rect(puzzle_surface, config.SELECTED_COLOR, rect)
                else:
                    pygame.draw.rect(puzzle_surface, config.LIGHT_GRAY, rect, 1)
                num_initial = self.board_initial[r][c]
                num_current = self.board_current[r][c]
                num_overlay = self.board_solved_overlay[r][c]
                display_num_str = ""
                color = config.BLACK
                if num_current != 0:
                    display_num_str = str(num_current)
                    color = config.LIGHT_BLUE if num_initial != 0 else \
                            config.GREEN_SOLVE if self.won and self.solved_by_ai else \
                            config.DARK_BLUE
                elif num_overlay != 0:
                    display_num_str = str(num_overlay)
                    color = config.TRY_COLOR if self.is_solving else \
                            config.KEEP_COLOR if not self.is_solving else \
                            config.BACKTRACK_COLOR
                if display_num_str:
                    text_surface = self.font_cell.render(display_num_str, True, color)
                    text_rect = text_surface.get_rect(center=(c * self.cell_size + self.cell_size // 2, r * self.cell_size + self.cell_size // 2))
                    puzzle_surface.blit(text_surface, text_rect)

        for i in range(self.grid_dimension + 1):
            line_width = 3 if i % 2 == 0 else 1
            pygame.draw.line(puzzle_surface, config.BLACK, (0, i * self.cell_size), (self.grid_size, i * self.cell_size), line_width)
            pygame.draw.line(puzzle_surface, config.BLACK, (i * self.cell_size, 0), (i * self.cell_size, self.grid_size), line_width)

        timer_text = f"Time: {int(self.time_remaining)}s"
        timer_surface = self.font_timer.render(timer_text, True, config.BLACK)
        timer_rect = timer_surface.get_rect(center=(self.grid_size // 2, self.grid_size + 90))  # Căn giữa, dưới nút Confirm
        puzzle_surface.blit(timer_surface, timer_rect)

        surface.blit(puzzle_surface, self.puzzle_rect.topleft)