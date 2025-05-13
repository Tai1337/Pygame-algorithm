import pygame
import random
from collections import deque 
import src.config as config
from .base_minigame import BaseMiniGame

class SnakeGame(BaseMiniGame):
    def __init__(self, screen_width, screen_height, ui_manager):
        super().__init__(screen_width, screen_height, ui_manager)
        
        self.cell_size = config.SNAKE_CELL_SIZE
        self.grid_width = config.SNAKE_GRID_WIDTH 
        self.grid_height = config.SNAKE_GRID_HEIGHT

        self.game_area_pixel_width = self.grid_width * self.cell_size
        self.game_area_pixel_height = self.grid_height * self.cell_size

        self.game_area_rect = pygame.Rect(
            (self.screen_width - self.game_area_pixel_width) // 2,
            (self.screen_height - self.game_area_pixel_height) // 2 + 20, 
            self.game_area_pixel_width,
            self.game_area_pixel_height
        )
        self.game_surface = pygame.Surface((self.game_area_pixel_width, self.game_area_pixel_height))

        try:
            self.score_font = pygame.font.Font(config.DEFAULT_FONT_PATH, 30) 
        except pygame.error as e:
            print(f"Lỗi font cho Snake game: {e}")
            self.score_font = pygame.font.SysFont(None, 30)

        self.snake_segments = [] 
        self.direction = (1, 0)
        self.pending_direction = (1,0)
        self.food_pos = (0, 0)
        self.score = 0
        self.move_timer = 0.0

        self.snake_body_color = config.SNAKE_COLOR
        self.snake_head_color = config.SNAKE_HEAD_COLOR
        self.food_color = config.FOOD_COLOR
        self.game_area_background_color = config.SNAKE_GAME_AREA_BG_COLOR
        self.grid_line_color = config.SNAKE_GRID_LINE_COLOR

        self.pending_collision_penalty = 0 

    def _reset_snake_after_collision(self):
        """Reset rắn về trạng thái ban đầu, reset điểm số và đặt lại mồi."""
        print("Snake: Resetting after collision.")
        self.direction = (1, 0) 
        self.pending_direction = (1,0)
        center_x = self.grid_width // 2
        center_y = self.grid_height // 2
        self.snake_segments = [] 
        for i in range(config.SNAKE_INITIAL_LENGTH):
            self.snake_segments.append((center_x - i, center_y))
        
        self.score = 0
        
        self._place_food() 
        self.move_timer = 0.0

    def _place_food(self):
        while True:
            self.food_pos = (random.randint(0, self.grid_width - 1),
                             random.randint(0, self.grid_height - 1))
            if self.food_pos not in self.snake_segments:
                break

    def start_game(self):
        super().start_game()
        self.direction = (1, 0) 
        self.pending_direction = (1,0)
        center_x = self.grid_width // 2
        center_y = self.grid_height // 2
        self.snake_segments = [] 
        for i in range(config.SNAKE_INITIAL_LENGTH):
            self.snake_segments.append((center_x - i, center_y))

        self._place_food()
        self.score = 0
        self.move_timer = 0.0
        self.pending_collision_penalty = 0

    def handle_event(self, event):
        if super().handle_event(event): 
            return True 
        
        if not self.is_active or self.won: 
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                if self.direction != (0, 1): self.pending_direction = (0, -1)
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                if self.direction != (0, -1): self.pending_direction = (0, 1)
            elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                if self.direction != (1, 0): self.pending_direction = (-1, 0)
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                if self.direction != (-1, 0): self.pending_direction = (1, 0)
        return False

    def update(self, dt):
        if not self.is_active or self.won: 
            return not self.is_active 

        self.move_timer += dt
        if self.move_timer >= config.SNAKE_PLAYER_MOVE_INTERVAL:
            self.move_timer -= config.SNAKE_PLAYER_MOVE_INTERVAL
            
            self.direction = self.pending_direction

            head_x, head_y = self.snake_segments[0]
            new_head = (head_x + self.direction[0], head_y + self.direction[1])

            collided = False
            
            if not (0 <= new_head[0] < self.grid_width and \
                    0 <= new_head[1] < self.grid_height):
                print("Snake: Hit wall.")
                collided = True
            
            elif new_head in self.snake_segments: 
                print("Snake: Hit self.")
                collided = True

            if collided:
                self.pending_collision_penalty += config.SNAKE_COLLISION_COST
                self._reset_snake_after_collision() 
                
                return False 

            
            self.snake_segments.insert(0, new_head)

            if new_head == self.food_pos:
                self.score += 1
                if self.score >= config.SNAKE_POINTS_TO_WIN:
                    self.won = True
                    self.is_active = False 
                    print("Snake: Player won the game!")
                    return True 
                self._place_food()
            else:
                self.snake_segments.pop() 
        
        return False 

    def draw(self, surface, main_game_time_remaining):
        super().draw(surface, main_game_time_remaining)
        self.game_surface.fill(self.game_area_background_color)

        for x_line in range(0, self.game_area_pixel_width, self.cell_size):
            pygame.draw.line(self.game_surface, self.grid_line_color, (x_line, 0), (x_line, self.game_area_pixel_height))
        for y_line in range(0, self.game_area_pixel_height, self.cell_size):
            pygame.draw.line(self.game_surface, self.grid_line_color, (0, y_line), (self.game_area_pixel_width, y_line))
        
        for i, segment in enumerate(self.snake_segments):
            rect = pygame.Rect(segment[0] * self.cell_size, segment[1] * self.cell_size, self.cell_size, self.cell_size)
            color_to_use = self.snake_head_color if i == 0 else self.snake_body_color
            pygame.draw.rect(self.game_surface, color_to_use, rect, border_radius=5)
            pygame.draw.rect(self.game_surface, config.BLACK, rect, 1, border_radius=5) 
        
        if self.food_pos:
            food_rect = pygame.Rect(self.food_pos[0] * self.cell_size, self.food_pos[1] * self.cell_size, self.cell_size, self.cell_size)
            pygame.draw.rect(self.game_surface, self.food_color, food_rect, border_radius=self.cell_size // 3)
            inner_food_radius = self.cell_size // 4
            pygame.draw.circle(self.game_surface, (max(0,self.food_color[0]-50), max(0,self.food_color[1]-50), max(0,self.food_color[2]-50)), food_rect.center, inner_food_radius)
        
        score_text = f"Điểm: {self.score} / {config.SNAKE_POINTS_TO_WIN}"
        score_surf = self.score_font.render(score_text, True, config.WHITE)
        score_rect = score_surf.get_rect(topleft=(10, 10)) 
        self.game_surface.blit(score_surf, score_rect)
        
        surface.blit(self.game_surface, self.game_area_rect.topleft)

    def cleanup_ui(self): 
        super().cleanup_ui()
        pass