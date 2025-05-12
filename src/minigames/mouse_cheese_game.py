import pygame
import numpy as np
import random
import os
import src.config as config
from .base_minigame import BaseMiniGame
from .maze_ql_agent import MazeQLearningAgent

class MouseCheeseGame(BaseMiniGame):
    def __init__(self, screen_width, screen_height, ui_manager):
        super().__init__(screen_width, screen_height, ui_manager)

        self.maze_layout = np.array(config.DEFAULT_MAZE_LAYOUT)
        self.grid_height, self.grid_width = self.maze_layout.shape
        self.cell_size = config.MAZE_CELL_SIZE

        self.game_area_pixel_width = self.grid_width * self.cell_size
        self.game_area_pixel_height = self.grid_height * self.cell_size
        self.game_area_rect = pygame.Rect(
            (self.screen_width - self.game_area_pixel_width) // 2,
            (self.screen_height - self.game_area_pixel_height) // 2,
            self.game_area_pixel_width,
            self.game_area_pixel_height
        )
        self.game_surface = pygame.Surface((self.game_area_pixel_width, self.game_area_pixel_height))
        
        try:
            self.status_font = pygame.font.Font(None, config.MAZE_FONT_SIZE)
        except pygame.error as e:
            self.status_font = pygame.font.SysFont(None, config.MAZE_FONT_SIZE)

        self.initial_cheese_pos = config.MAZE_INITIAL_CHEESE_POSITIONS
        self.start_pos = config.MAZE_START_POS
        self.target_cheese_count = config.MAZE_TARGET_CHEESE_COUNT

        try:
            mouse_img_orig = pygame.image.load(config.MOUSE_IMAGE_PATH).convert_alpha()
            self.mouse_image = pygame.transform.scale(mouse_img_orig, (int(self.cell_size*0.7), int(self.cell_size*0.7)))
        except Exception as e:
            print(f"Lỗi tải ảnh chuột: {e}. Dùng hình chữ nhật.")
            self.mouse_image = None
        try:
            cheese_img_orig = pygame.image.load(config.CHEESE_IMAGE_PATH).convert_alpha()
            self.cheese_image = pygame.transform.scale(cheese_img_orig, (int(self.cell_size*0.5), int(self.cell_size*0.5)))
        except Exception as e:
            print(f"Lỗi tải ảnh phô mai: {e}. Dùng hình ellipse.")
            self.cheese_image = None

        self.q_agent = MazeQLearningAgent(
            actions=[0, 1, 2, 3],
            maze_shape=self.maze_layout.shape,
            learning_rate=config.MAZE_QL_LEARNING_RATE,
            discount_factor=config.MAZE_QL_DISCOUNT_FACTOR,
            epsilon_start=config.MAZE_QL_EPSILON_START,
            epsilon_end=config.MAZE_QL_EPSILON_END,
            epsilon_decay_rate=config.MAZE_QL_EPSILON_DECAY_RATE,
            initial_q_value=config.MAZE_QL_INITIAL_Q_VALUE
        )

        self.display_message = ""
        self.display_message_timer = 0
        self.training_episodes = 0
        self.move_timer = 0.0  # Bộ đếm thời gian cho di chuyển chuột
        
        self.reset_game_internal_state()

    def reset_game_internal_state(self):
        self.mouse_pos_list = list(self.start_pos)
        self.remaining_cheese_set = set(self.initial_cheese_pos)
        self.score = 0
        self.steps = 0
        self.current_path_coords = [tuple(self.mouse_pos_list)]
        self.game_won_internal = False
        return self._get_current_state_tuple()

    def start_game(self, training_episodes=0):
        super().start_game()
        self.training_episodes = training_episodes
        self.move_timer = 0.0  # Reset timer khi bắt đầu game
        if training_episodes > 0:
            self.train_agent(training_episodes)
        self.reset_game_internal_state()
        self.q_agent.epsilon = 0.0
        self.display_message = ""
        self.display_message_timer = 0
        print(f"{self.__class__.__name__} started. Mouse at {self.mouse_pos_list}, Cheese: {self.remaining_cheese_set}")

    def train_agent(self, episodes):
        self.q_agent.epsilon = config.MAZE_QL_EPSILON_START
        for episode in range(episodes):
            state = self.reset_game_internal_state()
            done = False
            steps = 0
            max_steps = max(15, int(self.grid_width * self.grid_height * len(self.initial_cheese_pos) * config.MAZE_MAX_STEPS_FACTOR))

            while not done and steps <= max_steps:
                action = self.q_agent.choose_action(state, learn=True)
                next_state, reward, done = self._perform_ai_action(action)
                self.q_agent.update_q_table(state, action, reward, next_state)
                state = next_state
                steps += 1
                self.q_agent.decay_epsilon()
            print(f"Training episode {episode + 1}/{episodes} completed. Score: {self.score}")
        self.q_agent.save_q_table(config.MAZE_Q_TABLE_CSV_PATH)
        self.q_agent.epsilon = 0.0

    def _get_current_state_tuple(self):
        return (self.mouse_pos_list[0], self.mouse_pos_list[1], frozenset(self.remaining_cheese_set))

    def _perform_ai_action(self, action_idx):
        potential_next_mouse_pos = list(self.mouse_pos_list)
        if action_idx == 0: potential_next_mouse_pos[0] -= 1
        elif action_idx == 1: potential_next_mouse_pos[0] += 1
        elif action_idx == 2: potential_next_mouse_pos[1] -= 1
        elif action_idx == 3: potential_next_mouse_pos[1] += 1

        current_reward = config.MAZE_REWARD_STEP
        hit_wall_this_step = False
        is_done_this_step = False

        if not (0 <= potential_next_mouse_pos[0] < self.grid_height and \
                0 <= potential_next_mouse_pos[1] < self.grid_width) or \
           self.maze_layout[potential_next_mouse_pos[0], potential_next_mouse_pos[1]] == 1:
            current_reward = config.MAZE_REWARD_WALL
            hit_wall_this_step = True
        else:
            self.mouse_pos_list = potential_next_mouse_pos
            self.current_path_coords.append(tuple(self.mouse_pos_list))

        current_mouse_pos_tuple = tuple(self.mouse_pos_list)
        if not hit_wall_this_step and current_mouse_pos_tuple in self.remaining_cheese_set:
            self.remaining_cheese_set.remove(current_mouse_pos_tuple)
            self.score += 1
            current_reward += config.MAZE_REWARD_CHEESE
            print(f"MazeAI: Ate cheese! Score: {self.score}, Remaining: {len(self.remaining_cheese_set)}")

        if self.score >= self.target_cheese_count:
            current_reward += config.MAZE_REWARD_WIN_ALL_CHEESE
            is_done_this_step = True
            self.game_won_internal = True
        elif not self.remaining_cheese_set and self.score < self.target_cheese_count:
            is_done_this_step = True
            self.game_won_internal = False
        
        max_steps_calc = self.grid_width * self.grid_height * (len(self.initial_cheese_pos) * config.MAZE_MAX_STEPS_FACTOR)
        max_steps_allowed = max(15, int(max_steps_calc))

        self.steps += 1
        if not is_done_this_step and self.steps > max_steps_allowed:
            is_done_this_step = True
            self.game_won_internal = False
            print(f"MazeAI: Out of steps ({self.steps}/{max_steps_allowed}).")
            current_reward = config.MAZE_REWARD_WALL

        return self._get_current_state_tuple(), current_reward, is_done_this_step

    def handle_event(self, event):
        if super().handle_event(event):
            return True
        
        if not self.is_active:
            if self.display_message_timer > 0:
                if event.type == pygame.MOUSEBUTTONDOWN or \
                   (event.type == pygame.KEYDOWN and event.key != pygame.K_ESCAPE):
                    self.display_message_timer = 0
                    self.display_message = ""
            return False
        return False

    def update(self, dt):
        if not self.is_active or self.won:
            if self.display_message_timer > 0:
                self.display_message_timer -= dt
                if self.display_message_timer <= 0:
                    self.display_message = ""
            return not self.is_active

        # Cập nhật timer cho di chuyển chuột
        self.move_timer += dt
        if self.move_timer < config.MAZE_MOUSE_MOVE_INTERVAL:
            return False  # Chưa đến lúc di chuyển

        # Đủ thời gian, thực hiện di chuyển và reset timer
        self.move_timer = 0.0

        current_state = self._get_current_state_tuple()
        action = self.q_agent.choose_action(current_state, learn=False)
        next_state, reward, done = self._perform_ai_action(action)

        if done:
            self.is_active = self.won = self.game_won_internal  # Sửa lỗi cú pháp
            if self.won:
                self.display_message = f"AI đã ăn hết {self.score} phô mai!"
                self.display_message_color = config.GREEN
            else:
                self.display_message = config.MAZE_RETRY_TRAINING_MESSAGE
                self.display_message_color = config.RED
            self.display_message_timer = 5
            print(f"MazeGame: AI finished. Won: {self.won}")
            return True
            
        if self.display_message_timer > 0:
            self.display_message_timer -= dt
            if self.display_message_timer <= 0:
                self.display_message = ""
                self.display_message_timer = 0

        return False

    def _draw_grid_on_surface(self, surface_to_draw_on):
        for r in range(self.grid_height):
            for c in range(self.grid_width):
                rect = pygame.Rect(c * self.cell_size, r * self.cell_size, self.cell_size, self.cell_size)
                if self.maze_layout[r, c] == 1:
                    pygame.draw.rect(surface_to_draw_on, config.BLACK, rect)
                else:
                    pygame.draw.rect(surface_to_draw_on, config.WHITE, rect)
                pygame.draw.rect(surface_to_draw_on, config.GRAY, rect, 1)

    def _draw_elements_on_surface(self, surface_to_draw_on):
        for r_idx, c_idx in self.remaining_cheese_set:
            if self.cheese_image:
                img_w, img_h = self.cheese_image.get_size()
                x_pos = c_idx * self.cell_size + (self.cell_size - img_w) // 2
                y_pos = r_idx * self.cell_size + (self.cell_size - img_h) // 2
                surface_to_draw_on.blit(self.cheese_image, (x_pos, y_pos))
            else:
                pygame.draw.ellipse(surface_to_draw_on, config.YELLOW,
                                    (c_idx * self.cell_size + self.cell_size // 4,
                                     r_idx * self.cell_size + self.cell_size // 4,
                                     self.cell_size // 2, self.cell_size // 2))
        if self.mouse_image:
            img_w, img_h = self.mouse_image.get_size()
            x_pos = self.mouse_pos_list[1] * self.cell_size + (self.cell_size - img_w) // 2
            y_pos = self.mouse_pos_list[0] * self.cell_size + (self.cell_size - img_h) // 2
            surface_to_draw_on.blit(self.mouse_image, (x_pos, y_pos))
        else:
            pygame.draw.rect(surface_to_draw_on, config.BLUE,
                             (self.mouse_pos_list[1] * self.cell_size + self.cell_size // 4,
                              self.mouse_pos_list[0] * self.cell_size + self.cell_size // 4,
                              self.cell_size // 2, self.cell_size // 2))
    
    def _draw_path_on_surface(self, surface_to_draw_on, path_coords, color=config.MAZE_PATH_COLOR, width=3):
        if len(path_coords) > 1:
            path_pixel_points = [(c * self.cell_size + self.cell_size // 2, 
                                  r * self.cell_size + self.cell_size // 2) 
                                 for r, c in path_coords]
            pygame.draw.lines(surface_to_draw_on, color, False, path_pixel_points, width)

    def _draw_status_text_on_surface(self, surface_to_draw_on):
        y_offset = 10
        line_height = config.MAZE_FONT_SIZE + 2
        texts_to_draw = [
            f"Bước đi: {self.steps}",
            f"Phô mai: {self.score}/{self.target_cheese_count}",
            f"Lượt huấn luyện: {self.training_episodes}"
        ]
        if self.is_active and not self.won:
            texts_to_draw.append("AI đang tìm phô mai...")
        for i, text_line in enumerate(texts_to_draw):
            img = self.status_font.render(text_line, True, config.WHITE)
            surface_to_draw_on.blit(img, (10, y_offset + i * line_height))

    def draw(self, surface, main_game_time_remaining):
        super().draw(surface, main_game_time_remaining)
        self.game_surface.fill(config.WHITE)
        self._draw_grid_on_surface(self.game_surface)
        self._draw_elements_on_surface(self.game_surface)
        if self.current_path_coords:
            self._draw_path_on_surface(self.game_surface, self.current_path_coords)
        self._draw_status_text_on_surface(self.game_surface)
        surface.blit(self.game_surface, self.game_area_rect.topleft)
        if self.display_message_timer > 0 and self.display_message:
            msg_surf = self.font.render(self.display_message, True, self.display_message_color)
            msg_rect = msg_surf.get_rect(center=(self.screen_width // 2, 
                                                 self.game_area_rect.top - self.font.get_height() - 5))
            surface.blit(msg_surf, msg_rect)

    def cleanup_ui(self):
        super().cleanup_ui()