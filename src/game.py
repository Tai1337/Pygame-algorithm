import pygame
import sys
import os
import io
import pygame_gui
import random

import src.config as config
from src.utils.file_handle import load_csv
from src.core.player import Player
from src.pathfinding.pathfinder import PathFinder
from src.core.point_manager import PointManager
from src.core.camera import Camera
from src.core.title import Tile
from src.minigames.eight_puzzle_game import EightPuzzleGame
from src.minigames.snake_game import SnakeGame
from src.minigames.mouse_cheese_game import MouseCheeseGame
from src.minigames.caro_game import CaroGame
from src.ui.minigame_selector_ui import MinigameSelectorUI

class Game:
    def __init__(self):
        self._initialize_pygame_and_display()
        self._load_main_assets_and_ui_manager()
        self._setup_map_and_world() 
        
        self.player = None 
        self.camera = None
        self.point_manager = None
        self.path_finder = None
        self.all_minigame_instances = []
        self.minigame_selector = MinigameSelectorUI(self.ui_manager)
        
        self.main_game_timer_label = None
        self.money_label = None
        self.items_collected_label = None
        self.status_message_label = None
        self.training_input_window = None
        self.training_input_entry = None
        self.training_input_confirm_button = None
        self.training_input_message_label = None
        
        self.pending_minigame = None  # Lưu minigame chờ khi nhập số lượt huấn luyện
        
        self._reset_game_state_and_entities()
        print("Game initialized and ready.")

    def _reset_game_state_and_entities(self):
        print("Resetting game state and entities...")
        player_start_x, player_start_y = self._determine_player_start_pos()
        if self.player is None:
            self.player = Player(player_start_x, player_start_y)
        else:
            self.player.x = float(player_start_x)
            self.player.y = float(player_start_y)
            self.player.rect.topleft = (round(self.player.x), round(self.player.y))
            self.player.money = config.INITIAL_PLAYER_MONEY
            self.player.items_collected_count = 0
            self.player.actions = []
            self.player.target_path_nodes = []
            self.player.facing_direction = 'down'
            self.player.animation_timer = 0.0

        if self.camera is None:
            self.camera = Camera(self.world_pixel_width, self.world_pixel_height)
        self.camera.update(self.player)

        if self.point_manager is None:
            self.point_manager = PointManager(self.entity_data)
        else:
            if hasattr(self.point_manager, 'reset'):
                self.point_manager.reset(self.entity_data)
            else:
                self.point_manager = PointManager(self.entity_data)

        if self.path_finder is None:
            self.path_finder = PathFinder(self.floor_block_data, self.ui_manager, self.player, self.point_manager)
        else:
            self.path_finder.player = self.player
            self.path_finder.point_manager = self.point_manager
            if self.path_finder.input_active: self.path_finder.disable_input()

        self._initialize_minigames_instances()
        if self.minigame_selector.is_visible: self.minigame_selector.kill()
        self._cleanup_training_input_ui()

        self.current_minigame_instance = None
        self.current_game_state = config.ST_PLAYING_MAIN
        self.main_game_timer_active = True
        self.main_game_time_remaining = config.MAIN_GAME_TIME_LIMIT_SECONDS
        self.status_message_timer = 0.0
        self.running = True
        self.debug_draw_tiles = False
        self.game_over_message_shown = False

        self._setup_main_ui_labels()

    def _initialize_pygame_and_display(self):
        try:
            if sys.stdout.encoding != 'utf-8': sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
            if sys.stderr.encoding != 'utf-8': sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
        except Exception as e: print(f"Không thể đặt UTF-8: {e}")
        pygame.init()
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        pygame.display.set_caption("Game Giao Hàng & Mini-games")
        self.clock = pygame.time.Clock()

    def _load_main_assets_and_ui_manager(self):
        self.ui_manager = pygame_gui.UIManager((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), config.THEME_FILE_PATH)
        try:
            self.background_img_full = pygame.image.load(config.MAP_IMAGE_PATH).convert()
        except Exception as e:
            print(f"Lỗi tải ảnh nền '{config.MAP_IMAGE_PATH}': {e}"); pygame.quit(); sys.exit()

    def _setup_map_and_world(self):
        self.floor_block_data = load_csv(config.FLOOR_BLOCK_CSV_PATH)
        self.entity_data = load_csv(config.ENTITY_CSV_PATH)
        num_rows = len(self.floor_block_data)
        num_cols = max(len(r) for r in self.floor_block_data if r) if num_rows > 0 and any(r for r in self.floor_block_data) else 0
        if num_rows == 0 or num_cols == 0:
            print("Lỗi: Dữ liệu bản đồ không hợp lệ."); pygame.quit(); sys.exit()
        
        self.world_pixel_width = num_cols * config.TILE_SIZE
        self.world_pixel_height = num_rows * config.TILE_SIZE
        self.collidable_tiles = pygame.sprite.Group()
        for r_idx, row_data in enumerate(self.floor_block_data):
            for c_idx, tile_value in enumerate(row_data):
                if tile_value.strip() not in ['-1', '']:
                    self.collidable_tiles.add(Tile(c_idx * config.TILE_SIZE, r_idx * config.TILE_SIZE, config.TILE_SIZE))

    def _determine_player_start_pos(self):
        start_x, start_y = config.TILE_SIZE, config.TILE_SIZE
        found = False
        if not hasattr(self, 'entity_data') or not self.entity_data:
            print("Lỗi: entity_data chưa được tải khi xác định vị trí người chơi.")
            return start_x, start_y

        for r_idx, row in enumerate(self.entity_data):
            for c_idx, val in enumerate(row):
                if val.strip() == config.PLAYER_ENTITY_ID:
                    start_x, start_y = c_idx * config.TILE_SIZE, r_idx * config.TILE_SIZE
                    found = True; break
            if found: break
        if not found: print(f"CẢNH BÁO: Không tìm thấy ID người chơi '{config.PLAYER_ENTITY_ID}'.")
        return start_x, start_y

    def _initialize_minigames_instances(self):
        eight_puzzle = EightPuzzleGame(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, self.ui_manager)
        snake_game = SnakeGame(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, self.ui_manager)
        maze_game = MouseCheeseGame(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, self.ui_manager)
        caro_game = CaroGame(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, self.ui_manager)
        self.all_minigame_instances = [eight_puzzle, snake_game, maze_game, caro_game]
        self.point_to_minigame_map = {}
        self.current_minigame_pool_index = 0

    def _setup_main_ui_labels(self):
        if hasattr(self, 'main_game_timer_label') and self.main_game_timer_label and self.main_game_timer_label.alive():
            self.main_game_timer_label.kill()
        self.main_game_timer_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, 240, 30),
            text=f"Thời gian: {int(self.main_game_time_remaining // 60):02d}:{int(self.main_game_time_remaining % 60):02d}",
            manager=self.ui_manager, object_id="#main_timer_label"
        )

        if hasattr(self, 'money_label') and self.money_label and self.money_label.alive():
            self.money_label.kill()
        self.money_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 40, 200, 30), text=f"Tiền: {self.player.money}",
            manager=self.ui_manager, object_id="#money_label"
        )

        if hasattr(self, 'items_collected_label') and self.items_collected_label and self.items_collected_label.alive():
            self.items_collected_label.kill()
        self.items_collected_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 70, 240, 30), text=f"Hàng đã giao: {self.player.items_collected_count}",
            manager=self.ui_manager, object_id="#items_label"
        )

        if hasattr(self, 'status_message_label') and self.status_message_label and self.status_message_label.alive():
            self.status_message_label.kill()
        self.status_message_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(config.SCREEN_WIDTH // 2 - 200, 10, 400, 30), text="",
            manager=self.ui_manager, object_id="#status_message"
        )

    def _setup_training_input_ui(self):
        self._cleanup_training_input_ui()
        window_width = 400
        window_height = 200
        self.training_input_window = pygame_gui.elements.UIWindow(
            rect=pygame.Rect((config.SCREEN_WIDTH - window_width) // 2, (config.SCREEN_HEIGHT - window_height) // 2, window_width, window_height),
            manager=self.ui_manager,
            window_display_title="Nhập Lượt Huấn Luyện",
            resizable=False
        )
        self.training_input_message_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, window_width - 20, 30),
            text=config.MAZE_TRAINING_PROMPT,
            manager=self.ui_manager,
            container=self.training_input_window
        )
        self.training_input_entry = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(10, 50, window_width - 20, 30),
            manager=self.ui_manager,
            container=self.training_input_window
        )
        self.training_input_confirm_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10, 90, window_width - 20, 40),
            text="Xác nhận",
            manager=self.ui_manager,
            container=self.training_input_window
        )

    def _cleanup_training_input_ui(self):
        if self.training_input_window and self.training_input_window.alive():
            self.training_input_window.kill()
        self.training_input_window = None
        self.training_input_entry = None
        self.training_input_confirm_button = None
        self.training_input_message_label = None

    def _handle_game_end_options(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                print("Player chose to restart the game.")
                self._reset_game_state_and_entities()
                return False
            elif event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                print("Player chose to quit after game end.")
                self.running = False
                return True
        return False

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False

            is_game_won_or_over = (self.current_game_state == config.ST_PLAYER_WON or \
                                   self.current_game_state == config.ST_GAME_OVER_TIME or \
                                   self.current_game_state == config.ST_GAME_OVER_MONEY)

            if is_game_won_or_over:
                self._handle_game_end_options(event)
                self.ui_manager.process_events(event)
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.current_game_state == config.ST_CHOOSING_MINIGAME and self.minigame_selector.is_visible:
                        self.minigame_selector.kill()
                        self.current_game_state = config.ST_PLAYING_MAIN
                        self.point_manager.collected_point_for_puzzle_center = None
                        self._set_status_message("Đã hủy chọn mini-game.", 2)
                    elif self.current_game_state == config.ST_ENTERING_TRAINING_EPISODES and self.training_input_window:
                        self._cleanup_training_input_ui()
                        self.current_game_state = config.ST_PLAYING_MAIN
                        self.point_manager.collected_point_for_puzzle_center = None
                        self.pending_minigame = None
                        self._set_status_message("Đã hủy nhập lượt huấn luyện.", 2)
                    elif self.current_game_state == config.ST_PLAYING_PUZZLE and self.current_minigame_instance and self.current_minigame_instance.is_active:
                        if self.current_minigame_instance.handle_event(event):
                            self._process_minigame_end(player_won=False, was_cancelled_by_esc=True)
                    elif self.current_game_state == config.ST_PLAYING_MAIN and self.path_finder.input_active:
                        self.path_finder.disable_input()
                    else: self.running = False
                
                if self.current_game_state == config.ST_PLAYING_MAIN:
                    if event.key == pygame.K_F1: self.debug_draw_tiles = not self.debug_draw_tiles
                    if event.key == pygame.K_p and (not self.path_finder or not self.path_finder.input_active):
                        if self.point_manager and self.point_manager.is_visible and self.point_manager.current_point_center:
                            if self.path_finder: self.path_finder.enable_input()
                        else: self._set_status_message("Không có điểm đến cho Taxi!", 2)
            
            if self.current_game_state == config.ST_PLAYING_MAIN and self.path_finder and self.path_finder.input_active:
                self.path_finder.handle_input(event, self.point_manager)

            if self.current_game_state == config.ST_CHOOSING_MINIGAME and self.minigame_selector.is_visible:
                selection_result = self.minigame_selector.process_event(event)
                if isinstance(selection_result, object) and hasattr(selection_result, 'start_game'):
                    self.pending_minigame = selection_result
                    if isinstance(self.pending_minigame, MouseCheeseGame):
                        self.current_game_state = config.ST_ENTERING_TRAINING_EPISODES
                        self.minigame_selector.kill()
                        self._setup_training_input_ui()
                    else:
                        self.current_minigame_instance = selection_result
                        if hasattr(self.current_minigame_instance, 'solved_by_ai'): self.current_minigame_instance.solved_by_ai = False
                        self.current_minigame_instance.start_game()
                        self.current_game_state = config.ST_PLAYING_PUZZLE
                        self.player.set_actions([], None)
                        minigame_name = config.MINIGAME_DISPLAY_NAMES.get(self.current_minigame_instance.__class__.__name__, "Mini-game")
                        self._set_status_message(f"Bắt đầu {minigame_name}!", 3)
                elif selection_result == "closed":
                    self.current_game_state = config.ST_PLAYING_MAIN
                    self.point_manager.collected_point_for_puzzle_center = None
                    self._set_status_message("Đã đóng chọn mini-game.", 2)
            
            elif self.current_game_state == config.ST_ENTERING_TRAINING_EPISODES and self.training_input_window:
                if event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element == self.training_input_confirm_button:
                    try:
                        episodes = int(self.training_input_entry.get_text())
                        if episodes <= 0:
                            self.training_input_message_label.set_text(config.MAZE_INVALID_EPISODES_MESSAGE)
                        elif episodes * config.MAZE_TRAINING_COST_PER_EPISODE > self.player.money:
                            self.training_input_message_label.set_text(config.MAZE_INSUFFICIENT_MONEY_MESSAGE)
                        else:
                            self.player.spend_money(episodes * config.MAZE_TRAINING_COST_PER_EPISODE)
                            self.current_minigame_instance = self.pending_minigame
                            self.current_minigame_instance.start_game(training_episodes=episodes)
                            self.current_game_state = config.ST_PLAYING_PUZZLE
                            self._cleanup_training_input_ui()
                            self.pending_minigame = None
                            minigame_name = config.MINIGAME_DISPLAY_NAMES.get(self.current_minigame_instance.__class__.__name__, "Mini-game")
                            self._set_status_message(f"Bắt đầu {minigame_name} sau {episodes} lượt huấn luyện!", 3)
                    except ValueError:
                        self.training_input_message_label.set_text(config.MAZE_INVALID_EPISODES_MESSAGE)

            elif self.current_game_state == config.ST_PLAYING_PUZZLE and self.current_minigame_instance and self.current_minigame_instance.is_active:
                event_result_minigame = self.current_minigame_instance.handle_event(event)
                if event_result_minigame == config.PUZZLE_EVENT_AI_SOLVE_REQUEST:
                    if self.player.money >= config.PUZZLE_SOLVE_COST:
                        self.player.spend_money(config.PUZZLE_SOLVE_COST)
                        self.current_minigame_instance.attempt_ai_solve()
                        self._set_status_message(f"AI đang giải... (-{config.PUZZLE_SOLVE_COST} tiền)", float('inf'))
                    else: self._set_status_message(f"Không đủ tiền nhờ AI (cần {config.PUZZLE_SOLVE_COST}).", 3)
                elif event_result_minigame is True:
                    self._process_minigame_end(player_won=self.current_minigame_instance.won)
            
            self.ui_manager.process_events(event)

    def _update_timers_and_status(self, time_delta):
        if self.status_message_timer > 0 and self.status_message_timer != float('inf'):
            self.status_message_timer -= time_delta
            if self.status_message_timer <= 0:
                if self.status_message_label.alive(): self.status_message_label.set_text("")
                self.status_message_timer = 0

        if self.main_game_timer_active:
            self.main_game_time_remaining -= time_delta
            if self.main_game_timer_label.alive():
                minutes = int(self.main_game_time_remaining // 60)
                seconds = int(self.main_game_time_remaining % 60)
                self.main_game_timer_label.set_text(f"Thời gian: {minutes:02d}:{seconds:02d}" if self.main_game_time_remaining > 0 else "HẾT GIỜ!")

    def _check_and_handle_game_over_conditions(self):
        if self.game_over_message_shown:
            return True

        if self.player.items_collected_count >= config.TARGET_ITEMS_TO_WIN and self.main_game_time_remaining > 0:
            print("Người chơi đã thắng game!"); self._set_status_message("CHÚC MỪNG, BẠN ĐÃ THẮNG!", is_game_over_message=True)
            self.current_game_state = config.ST_PLAYER_WON; self.game_over_message_shown = True
            self._cleanup_active_minigame_and_ui(); return True

        if self.main_game_time_remaining <= 0:
            self.main_game_time_remaining = 0; print("Hết thời gian! GAME OVER.")
            self._set_status_message("HẾT GIỜ! BẠN THUA CUỘC!", is_game_over_message=True)
            self.current_game_state = config.ST_GAME_OVER_TIME; self.game_over_message_shown = True
            self._cleanup_active_minigame_and_ui(); return True
        
        if self.player.money <= 0:
            print("Hết tiền! GAME OVER."); 
            self._set_status_message("BẠN ĐÃ HẾT TIỀN! GAME OVER!", is_game_over_message=True)
            self.current_game_state = config.ST_GAME_OVER_MONEY; self.game_over_message_shown = True
            self._cleanup_active_minigame_and_ui(); return True
        return False

    def _cleanup_active_minigame_and_ui(self):
        if self.current_minigame_instance and self.current_minigame_instance.is_active:
            if hasattr(self.current_minigame_instance, 'cleanup_ui'): self.current_minigame_instance.cleanup_ui()
            self.current_minigame_instance.is_active = False
            self.current_minigame_instance = None
        if self.minigame_selector.is_visible: self.minigame_selector.kill()
        if self.training_input_window: self._cleanup_training_input_ui()
        if self.path_finder.input_active: self.path_finder.disable_input()

    def _set_status_message(self, message, duration=2.0, is_game_over_message=False):
        if self.status_message_label and self.status_message_label.alive():
            self.status_message_label.set_text(message)
        self.status_message_timer = float('inf') if is_game_over_message else duration
        print(f"[STATUS MSG]: {message} (Duration: {'inf' if is_game_over_message else duration})")

    def _process_minigame_end(self, player_won, was_cancelled_by_esc=False):
        if not self.current_minigame_instance: return

        minigame_class_name = self.current_minigame_instance.__class__.__name__
        minigame_display_name = config.MINIGAME_DISPLAY_NAMES.get(minigame_class_name, minigame_class_name)
        
        if hasattr(self.current_minigame_instance, 'cleanup_ui'):
            self.current_minigame_instance.cleanup_ui()
        
        was_solved_by_ai = getattr(self.current_minigame_instance, 'solved_by_ai', False)
        
        if player_won:
            if not was_solved_by_ai:
                self.player.collect_item(config.POINT_COLLECT_VALUE)
                additional_reward = config.MAZE_GAME_WIN_REWARD_MAIN if isinstance(self.current_minigame_instance, MouseCheeseGame) else config.MINIGAME_WIN_REWARD
                self.player.money += additional_reward
                self._set_status_message(f"Hoàn thành {minigame_display_name}! Thưởng: +{config.POINT_COLLECT_VALUE + additional_reward} tiền.", 4)
            else:
                self.player.items_collected_count += 1
                self._set_status_message(f"AI đã hoàn thành {minigame_display_name}!", 3)
            self.point_manager.finalize_collection()
        else:
            if isinstance(self.current_minigame_instance, MouseCheeseGame) and not was_cancelled_by_esc:
                self.current_game_state = config.ST_ENTERING_TRAINING_EPISODES
                self.pending_minigame = self.current_minigame_instance
                self.current_minigame_instance.is_active = False
                self.current_minigame_instance = None
                self._setup_training_input_ui()
                return
            if not was_cancelled_by_esc:
                self.player.money += config.MINIGAME_LOSE_PENALTY
                self._set_status_message(f"{minigame_display_name} thất bại! Phạt {abs(config.MINIGAME_LOSE_PENALTY)} tiền.", 3)
            
            if self.point_manager.collected_point_for_puzzle_center is not None:
                self.point_manager.collected_point_for_puzzle_center = None
        
        self.current_game_state = config.ST_PLAYING_MAIN
        self.current_minigame_instance.is_active = False
        self.current_minigame_instance = None

    def _update_game_logic(self, time_delta):
        is_game_won_or_over = (self.current_game_state == config.ST_PLAYER_WON or \
                              self.current_game_state == config.ST_GAME_OVER_TIME or \
                              self.current_game_state == config.ST_GAME_OVER_MONEY)
        if is_game_won_or_over: return

        if self.current_game_state == config.ST_PLAYING_MAIN:
            self.player.update(self.collidable_tiles, time_delta)
            self.camera.update(self.player)
            is_at_point_for_auto, _ = self.point_manager.is_player_at_point_for_auto_puzzle(self.player.rect.center)
            if is_at_point_for_auto and not self.current_minigame_instance and not self.minigame_selector.is_visible and not self.training_input_window:
                if self.all_minigame_instances:
                    self.current_game_state = config.ST_CHOOSING_MINIGAME
                    self.minigame_selector.show(self.all_minigame_instances)
                    self.player.set_actions([], None)
                else:
                    if self.point_manager.collected_point_for_puzzle_center:
                        self.player.collect_item(config.POINT_COLLECT_VALUE)
                        self.point_manager.finalize_collection()
                        self._set_status_message(f"Thu thập điểm! +{config.POINT_COLLECT_VALUE}", 2)
        
        elif self.current_game_state == config.ST_PLAYING_PUZZLE and self.current_minigame_instance:
            game_ended_by_update = self.current_minigame_instance.update(time_delta)
            
            if isinstance(self.current_minigame_instance, SnakeGame):
                if hasattr(self.current_minigame_instance, 'pending_collision_penalty') and \
                   self.current_minigame_instance.pending_collision_penalty > 0:
                    penalty_amount = self.current_minigame_instance.pending_collision_penalty
                    if self.player.spend_money(penalty_amount):
                        self._set_status_message(f"Rắn va chạm! Trừ {penalty_amount} tiền.", 2)
                    else:
                        self.player.money -= penalty_amount
                        self._set_status_message(f"Rắn va chạm! Không đủ tiền phạt! (-{penalty_amount})", 2)
                    self.current_minigame_instance.pending_collision_penalty = 0
            
            if game_ended_by_update:
                self._process_minigame_end(player_won=self.current_minigame_instance.won)
        
        if self.money_label.alive(): self.money_label.set_text(f"Tiền: {self.player.money}")
        if self.items_collected_label.alive(): self.items_collected_label.set_text(f"Hàng đã giao: {self.player.items_collected_count}")
        self.ui_manager.update(time_delta)

    def _draw_game_elements(self):
        self.screen.fill(config.BLACK)
        background_rect = self.background_img_full.get_rect(topleft=(0,0))
        self.screen.blit(self.background_img_full, self.camera.apply_rect(background_rect))

        is_game_won_or_over = (self.current_game_state == config.ST_PLAYER_WON or \
                               self.current_game_state == config.ST_GAME_OVER_TIME or \
                               self.current_game_state == config.ST_GAME_OVER_MONEY)

        if self.debug_draw_tiles and self.current_game_state == config.ST_PLAYING_MAIN and not is_game_won_or_over:
            for tile_sprite in self.collidable_tiles:
                tile_sprite.draw(self.screen, self.camera)

        if not is_game_won_or_over:
            self.point_manager.draw(self.screen, self.camera)
            self.player.draw(self.screen, self.camera)

        if self.current_game_state == config.ST_PLAYING_PUZZLE and self.current_minigame_instance and self.current_minigame_instance.is_active:
            self.current_minigame_instance.draw(self.screen, self.main_game_time_remaining)
        elif is_game_won_or_over:
            game_end_font = pygame.font.Font(None, 60)
            message = ""
            color = config.RED
            if self.current_game_state == config.ST_PLAYER_WON:
                message = "CHÚC MỪNG, BẠN ĐÃ THẮNG!"
                color = config.GREEN
            elif self.current_game_state == config.ST_GAME_OVER_TIME:
                message = "HẾT GIỜ! GAME OVER!"
            elif self.current_game_state == config.ST_GAME_OVER_MONEY:
                message = "HẾT TIỀN! GAME OVER!"
            
            if message:
                lines = message.split("! ")
                y_offset = self.screen.get_height() // 2 - (len(lines) * (game_end_font.get_height() // 1.5)) // 2

                for i, line in enumerate(lines):
                    game_end_text = game_end_font.render(line + ("!" if i < len(lines) -1 and "!" not in line else ""), True, color)
                    text_rect = game_end_text.get_rect(center=(config.SCREEN_WIDTH/2, y_offset + i * (game_end_font.get_height() + 5)))
                    self.screen.blit(game_end_text, text_rect)
                
                y_offset += len(lines) * (game_end_font.get_height() + 5) + 20

                play_again_font = pygame.font.Font(None, 36)
                play_again_text = play_again_font.render("Nhấn 'R' để chơi lại, 'ESC' hoặc 'Q' để thoát", True, config.WHITE)
                play_again_rect = play_again_text.get_rect(center=(config.SCREEN_WIDTH/2, y_offset))
                self.screen.blit(play_again_text, play_again_rect)

        self.ui_manager.draw_ui(self.screen)
        pygame.display.flip()

    def run(self):
        print("Bắt đầu vòng lặp game trong Game Class...")
        self.running = True
        while self.running:
            time_delta = self.clock.tick(config.FPS) / 1000.0
            
            self._update_timers_and_status(time_delta)
            game_has_ended = self._check_and_handle_game_over_conditions()
            self._handle_events()
            
            if not game_has_ended:
                self._update_game_logic(time_delta)
            
            self._draw_game_elements()

        print("Kết thúc game trong Game Class.")
        if hasattr(self, 'minigame_selector') and self.minigame_selector.is_visible:
            self.minigame_selector.kill()
        if self.training_input_window:
            self._cleanup_training_input_ui()
        pygame.quit()