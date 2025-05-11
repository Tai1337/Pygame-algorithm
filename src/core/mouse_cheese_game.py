import pygame
import numpy as np
import random
from collections import defaultdict
import os

# Pygame Settings
CELL_SIZE = 80

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (200, 200, 200)

DEFAULT_MAZE = [
    [0, 1, 0, 0, 0],
    [0, 1, 0, 1, 0],
    [0, 0, 0, 1, 0],
    [0, 1, 1, 1, 0],
    [0, 0, 0, 0, 0]
]

script_dir = os.path.dirname(os.path.abspath(__file__))

class MazeGame:
    def __init__(self, screen, font, player, app_config):
        self.screen = screen
        self.font = font
        self.player = player
        self.config = app_config

        self.maze = np.array(DEFAULT_MAZE)
        self.grid_height, self.grid_width = self.maze.shape

        self.screen_width = self.grid_width * CELL_SIZE
        self.screen_height = self.grid_height * CELL_SIZE
        self.clock = pygame.time.Clock()

        self.initial_cheese_positions = frozenset([(0, 4), (4, 4)])  # Vị trí pho mát mặc định
        self.start_pos = (0, 0)  # Vị trí chuột mặc định
        self.target_cheese_count = 2

        mouse_image_path = os.path.join(script_dir, "mouse.png")
        cheese_image_path = os.path.join(script_dir, "cheese.png")

        try:
            original_mouse_image = pygame.image.load(mouse_image_path).convert_alpha()
            self.mouse_image = pygame.transform.scale(original_mouse_image, (int(CELL_SIZE * 0.7), int(CELL_SIZE * 0.7)))
        except pygame.error:
            self.mouse_image = None
            print(f"Cannot load mouse.png, using blue rectangle fallback.")

        try:
            original_cheese_image = pygame.image.load(cheese_image_path).convert_alpha()
            self.cheese_image = pygame.transform.scale(original_cheese_image, (int(CELL_SIZE * 0.5), int(CELL_SIZE * 0.5)))
        except pygame.error:
            self.cheese_image = None
            print(f"Cannot load cheese.png, using yellow ellipse fallback.")

        q_agent_params = {
            "learning_rate": 0.1,
            "discount_factor": 0.95,
            "epsilon_decay_rate": 0.9995,
            "initial_q_value": 1.0
        }
        self.q_learning_agent = QLearningAgent(
            actions=[0, 1, 2, 3],
            maze_shape=self.maze.shape,
            **q_agent_params
        )
        self.is_active = False
        self.game_won = False
        self.message = ""
        self.message_color = RED
        self.message_timer = 0
        self.reset_game_state()

    def reset_game_state(self):
        self.mouse_pos = list(self.start_pos)
        self.remaining_cheese = set(self.initial_cheese_positions)
        self.score = 0
        self.steps = 0
        self.current_path = [tuple(self.mouse_pos)]
        return self.get_state()

    def get_state(self):
        return (self.mouse_pos[0], self.mouse_pos[1], frozenset(self.remaining_cheese))

    def perform_action(self, action):
        potential_pos = list(self.mouse_pos)

        if action == 0: potential_pos[0] -= 1
        elif action == 1: potential_pos[0] += 1
        elif action == 2: potential_pos[1] -= 1
        elif action == 3: potential_pos[1] += 1

        current_reward = -0.1
        hit_wall = False

        if not (0 <= potential_pos[0] < self.grid_height and
                0 <= potential_pos[1] < self.grid_width) or \
           self.maze[potential_pos[0], potential_pos[1]] == 1:
            current_reward = -2.0
            hit_wall = True
        else:
            self.mouse_pos = potential_pos
            self.current_path.append(tuple(self.mouse_pos))

        current_pos_tuple = tuple(self.mouse_pos)
        if not hit_wall and current_pos_tuple in self.remaining_cheese:
            self.remaining_cheese.remove(current_pos_tuple)
            self.score += 1
            current_reward += 20

        done = False
        if self.score >= self.target_cheese_count:
            current_reward += 60
            done = True
            self.game_won = True
        elif not self.remaining_cheese and self.score < self.target_cheese_count:
            done = True
            self.game_won = False

        max_allowed_steps = self.grid_width * self.grid_height * (len(self.initial_cheese_positions) + 1.2)
        if max_allowed_steps < 15: max_allowed_steps = 15

        if not done and self.steps > max_allowed_steps:
            done = True
            self.game_won = False

        self.steps += 1
        return self.get_state(), current_reward, done

    def draw_grid(self):
        for r in range(self.grid_height):
            for c in range(self.grid_width):
                rect = pygame.Rect(c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                if self.maze[r, c] == 1:
                    pygame.draw.rect(self.screen, BLACK, rect)
                else:
                    pygame.draw.rect(self.screen, WHITE, rect)
                pygame.draw.rect(self.screen, GRAY, rect, 1)

    def draw_elements(self):
        for r_idx, c_idx in self.remaining_cheese:
            if self.cheese_image:
                img_w, img_h = self.cheese_image.get_size()
                x_pos = c_idx * CELL_SIZE + (CELL_SIZE - img_w) // 2
                y_pos = r_idx * CELL_SIZE + (CELL_SIZE - img_h) // 2
                self.screen.blit(self.cheese_image, (x_pos, y_pos))
            else:
                pygame.draw.ellipse(self.screen, YELLOW,
                                    (c_idx * CELL_SIZE + CELL_SIZE // 3,
                                     r_idx * CELL_SIZE + CELL_SIZE // 3,
                                     CELL_SIZE // 3, CELL_SIZE // 3))
        if self.mouse_image:
            img_w, img_h = self.mouse_image.get_size()
            x_pos = self.mouse_pos[1] * CELL_SIZE + (CELL_SIZE - img_w) // 2
            y_pos = self.mouse_pos[0] * CELL_SIZE + (CELL_SIZE - img_h) // 2
            self.screen.blit(self.mouse_image, (x_pos, y_pos))
        else:
            pygame.draw.rect(self.screen, BLUE,
                             (self.mouse_pos[1] * CELL_SIZE + CELL_SIZE // 4,
                              self.mouse_pos[0] * CELL_SIZE + CELL_SIZE // 4,
                              CELL_SIZE // 2, CELL_SIZE // 2))

    def draw_path(self, path, color=GREEN, width=3):
        if len(path) > 1:
            path_points = [(c * CELL_SIZE + CELL_SIZE // 2, r * CELL_SIZE + CELL_SIZE // 2) for r, c in path]
            pygame.draw.lines(self.screen, color, False, path_points, width)

    def draw_text(self, text, position, color=RED):
        try:
            img = self.font.render(text, True, color)
            self.screen.blit(img, position)
        except Exception:
            pass

    def handle_event(self, event):
        if not self.is_active:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and self.message:
                self.message = ""
                self.message_timer = 0
                print("MazeGame: Exiting message screen.")
            elif event.type == pygame.MOUSEBUTTONDOWN and self.message:
                self.message = ""
                self.message_timer = 0
                print("MazeGame: Exiting message screen via click.")
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.is_active = False
                self.game_won = False
                self.message = "Game Exited."
                self.message_color = RED
                self.message_timer = 2
                print("MazeGame: Player exited with ESC.")
                return

    def update(self):
        if not self.is_active:
            if self.message_timer > 0:
                self.message_timer -= 1 / self.config.FPS
                if self.message_timer <= 0:
                    self.message = ""
            return

        state = self.get_state()
        action = self.q_learning_agent.choose_action(state, learn=False)  # Không học khi chơi
        next_state, reward, done = self.perform_action(action)
        state = next_state

        if done:
            self.is_active = False
            if self.game_won:
                self.message = f"ATE {self.score} CHEESES! +{self.config.MOUSE_CHEESE_REWARD} Money!"
                self.message_color = GREEN
            else:
                self.message = "Goal not achieved."
                self.message_color = RED
            self.message_timer = 2
            print(f"MazeGame: Game ended. Won: {self.game_won}")

        y_offset = 10
        line_height = 30
        current_y = y_offset
        self.draw_text(f"Steps: {self.steps}", (10, current_y))
        current_y += line_height
        self.draw_text(f"Cheese Eaten: {self.score}/{self.target_cheese_count}", (10, current_y))
        current_y += line_height
        status_text = "Finding cheese..."
        if self.score >= self.target_cheese_count:
            status_text = f"ATE {self.target_cheese_count} CHEESES!"
        self.draw_text(status_text, (10, current_y))

    def draw(self):
        if self.is_active or self.message:
            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (0, 0))

        self.screen.fill(WHITE)
        self.draw_grid()
        self.draw_elements()
        self.draw_path(self.current_path, RED, 3)

        y_offset = 10
        line_height = 30
        current_y = y_offset
        self.draw_text(f"Steps: {self.steps}", (10, current_y))
        current_y += line_height
        self.draw_text(f"Cheese Eaten: {self.score}/{self.target_cheese_count}", (10, current_y))
        current_y += line_height
        status_text = "Finding cheese..."
        if self.score >= self.target_cheese_count:
            status_text = f"ATE {self.target_cheese_count} CHEESES!"
        self.draw_text(status_text, (10, current_y))

        if self.message:
            msg_surf = self.font.render(self.message, True, self.message_color)
            msg_rect = msg_surf.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
            self.screen.blit(msg_surf, msg_rect)
            esc_surf = self.font.render("Press ESC or click to continue", True, GRAY)
            esc_rect = esc_surf.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 40))
            self.screen.blit(esc_surf, esc_rect)

    def start_game(self):
        self.is_active = True
        self.reset_game_state()
        self.q_learning_agent.epsilon = 0  # Không khám phá khi chơi
        print("MazeGame: Minigame started.")

class QLearningAgent:
    def __init__(self, actions, maze_shape,
                 learning_rate=0.1,
                 discount_factor=0.95,
                 epsilon_start=1.0,
                 epsilon_end=0.05,
                 epsilon_decay_rate=0.9995,
                 initial_q_value=1.0):
        self.actions = actions
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = epsilon_start
        self.epsilon_min = epsilon_end
        self.epsilon_decay = epsilon_decay_rate
        self.q_table = defaultdict(lambda: np.full(len(actions), initial_q_value, dtype=float))
        self.maze_rows, self.maze_cols = maze_shape
        self.current_episode_num = 0

    def choose_action(self, state, learn=True):
        if learn and random.uniform(0, 1) < self.epsilon:
            return random.choice(self.actions)
        else:
            q_values = self.q_table[state]
            max_q = np.max(q_values)
            return random.choice([i for i, q in enumerate(q_values) if q == max_q])

    def learn(self, state, action, reward, next_state, done):
        current_q = self.q_table[state][action]
        max_future_q = 0 if done else np.max(self.q_table[next_state])
        target_q = reward + self.gamma * max_future_q
        self.q_table[state][action] = current_q + self.lr * (target_q - current_q)

    def decay_epsilon(self):
        if self.epsilon > self.epsilon_min:
            self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)