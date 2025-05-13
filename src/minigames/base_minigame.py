
import pygame
import src.config as config

class BaseMiniGame:
    def __init__(self, screen_width, screen_height, ui_manager):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.ui_manager = ui_manager
        self.is_active = False
        self.won = False

        try:
            self.font = pygame.font.Font(config.DEFAULT_FONT_PATH, config.DEFAULT_FONT_SIZE_MEDIUM) 
        except Exception as e:
            print(f"Lỗi tải font mặc định trong BaseMiniGame: {e}. Dùng SysFont.")
            self.font = pygame.font.SysFont("arial", config.DEFAULT_FONT_SIZE_MEDIUM) 

    def start_game(self):
        self.is_active = True
        self.won = False
        print(f"{self.__class__.__name__} started.")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                print(f"{self.__class__.__name__}: ESC pressed, ending minigame (marked as loss).")
                self.is_active = False
                self.won = False
                return True 
        return False

    def update(self, dt):
        if not self.is_active or self.won:
            return False 
        return False

    def draw_main_game_timer(self, surface, x, y, main_game_time_remaining):
        """Vẽ bộ đếm thời gian của GAME CHÍNH."""
        minutes = int(main_game_time_remaining // 60)
        seconds = int(main_game_time_remaining % 60)
        time_text = f"Thời gian còn lại: {minutes:02d}:{seconds:02d}"
        time_surf = self.font.render(time_text, True, config.WHITE)
        surface.blit(time_surf, (x, y))

    def draw(self, surface, main_game_time_remaining):
        """Vẽ các thành phần chung của minigame (lớp phủ mờ)."""
        overlay_surface = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay_surface.fill(config.PUZZLE_BG_COLOR) 
        surface.blit(overlay_surface, (0, 0))
        

    def get_result(self):
        return self.won

    def cleanup_ui(self):
        pass