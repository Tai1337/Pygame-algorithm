# main.py
import pygame
import sys
import os
import io
import pygame_gui
import src.config as config
from src.utils.file_handle import load_csv
from src.core.player import Player
from src.pathfinding.pathfinder import PathFinder # Giữ lại nếu bạn sử dụng nó ở đâu đó
from src.core.point_manager import PointManager
from src.core.eight_puzzle_game import EightPuzzleGame
from src.core.camera import Camera
from src.core.title import Tile # 'Tile' nên là 'tile' nếu tên file là tile.py
from src.core.caro_game import CaroGame
from src.core.mouse_cheese_game import MazeGame

def main():
    # ... (phần khởi tạo pygame, screen, clock, ui_manager, background, map data, player, camera, point_manager giữ nguyên) ...
    try:
        if sys.stdout.encoding != 'utf-8':
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        if sys.stderr.encoding != 'utf-8':
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except Exception as e_io_setup:
        print(f"Không thể đặt encoding UTF-8 cho output: {e_io_setup}")

    pygame.init()
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption("Game Thu Thập Điểm - Pygame Taxi")
    clock = pygame.time.Clock()

    ui_manager = pygame_gui.UIManager((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), config.THEME_FILE_PATH)

    try:
        background_img_full = pygame.image.load(config.MAP_IMAGE_PATH).convert()
    except pygame.error as e_bg:
        print(f"Lỗi nghiêm trọng khi tải ảnh nền '{config.MAP_IMAGE_PATH}': {e_bg}")
        pygame.quit()
        sys.exit()
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file ảnh nền '{config.MAP_IMAGE_PATH}'")
        pygame.quit()
        sys.exit()

    floor_block_data = load_csv(config.FLOOR_BLOCK_CSV_PATH)
    entity_data = load_csv(config.ENTITY_CSV_PATH)

    num_rows = len(floor_block_data)
    num_cols = 0
    if num_rows > 0:
        try:
            num_cols = max(len(r) for r in floor_block_data if r)
        except ValueError:
            num_cols = 0

    if num_rows == 0 or num_cols == 0:
        print("Lỗi: Dữ liệu bản đồ floor_block_data không hợp lệ.")
        pygame.quit()
        sys.exit()

    world_pixel_width = num_cols * config.TILE_SIZE
    world_pixel_height = num_rows * config.TILE_SIZE

    collidable_tiles = pygame.sprite.Group()
    for r_idx, row_data in enumerate(floor_block_data):
        for c_idx, tile_value in enumerate(row_data):
            value = tile_value.strip()
            if value != '-1' and value != '':
                collidable_tiles.add(Tile(c_idx * config.TILE_SIZE, r_idx * config.TILE_SIZE, config.TILE_SIZE, is_collidable=True))

    player_start_x, player_start_y = config.TILE_SIZE, config.TILE_SIZE
    player_found_in_entity = False
    for r_idx, row_data_entity in enumerate(entity_data):
        for c_idx, entity_value in enumerate(row_data_entity):
            if entity_value.strip() == config.PLAYER_ENTITY_ID:
                player_start_x = c_idx * config.TILE_SIZE
                player_start_y = r_idx * config.TILE_SIZE
                player_found_in_entity = True
                print(f"Người chơi xuất phát từ Entity ID '{config.PLAYER_ENTITY_ID}' tại ô (hàng:{r_idx}, cột:{c_idx}) -> pixel (x:{player_start_x}, y:{player_start_y})")
                break
        if player_found_in_entity:
            break
    if not player_found_in_entity:
        print(f"CẢNH BÁO: Không tìm thấy ID '{config.PLAYER_ENTITY_ID}' cho người chơi. Sử dụng vị trí mặc định.")

    try:
        player = Player(player_start_x, player_start_y)
    except Exception as e_player:
        print(f"Lỗi nghiêm trọng khi tạo Player: {e_player}")
        pygame.quit()
        sys.exit()

    camera = Camera(world_pixel_width, world_pixel_height)
    point_manager = PointManager(entity_data)
    # path_finder đã bị comment ở file gốc, nếu cần thì khởi tạo lại
    path_finder = PathFinder(floor_block_data, ui_manager, player, point_manager)


    font = pygame.font.Font(None, 36)
    eight_puzzle_minigame = EightPuzzleGame(ui_manager) # Truyền ui_manager
    caro_minigame = CaroGame(config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
    maze_minigame = MazeGame(screen, font, player, config)

    current_game_state = config.ST_PLAYING_MAIN
    points_to_collect_value = 0 # Giá trị điểm của minigame hiện tại
    minigame_choice_window = None
    # ... (các biến UI khác cho minigame choice và mouse cheese train)
    choose_8puzzle_button = None
    choose_caro_button = None
    choose_mouse_cheese_button = None
    minigame_choice_title = None

    mouse_cheese_train_window = None
    mouse_cheese_train_input = None
    mouse_cheese_confirm_button = None
    mouse_cheese_cancel_button = None
    mouse_cheese_train_count = 0
    mouse_cheese_current_train = 0


    money_label = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect(10, 10, 200, 30),
        text=f"Tiền: {player.money}", manager=ui_manager, object_id="#money_label"
    )
    status_message_label = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect(config.SCREEN_WIDTH // 2 - 200, 10, 400, 30),
        text="", manager=ui_manager, object_id="#status_message"
    )
    status_message_timer = 0

    running = True
    debug_draw_tiles = False # Biến này có vẻ không được sử dụng để vẽ tile pathfinding

    # ... (các hàm show/hide UI giữ nguyên: show_minigame_choice_ui, hide_minigame_choice_ui, etc.)
    def show_minigame_choice_ui():
        nonlocal minigame_choice_window, choose_8puzzle_button, choose_caro_button, choose_mouse_cheese_button, minigame_choice_title
        if minigame_choice_window is not None: return
        window_width, window_height = 300, 250
        window_x, window_y = (config.SCREEN_WIDTH - window_width) // 2, (config.SCREEN_HEIGHT - window_height) // 2
        minigame_choice_window = pygame_gui.elements.UIWindow(
            rect=pygame.Rect(window_x, window_y, window_width, window_height),
            manager=ui_manager, window_display_title=config.MINIGAME_CHOICE_WINDOW_TITLE
        )
        minigame_choice_title = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 5, window_width - 20, 30), text="Chọn Minigame:",
            manager=ui_manager, container=minigame_choice_window
        )
        button_width_ui = window_width - 40
        choose_8puzzle_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(20, 45, button_width_ui, 40), text="8-Puzzle",
            manager=ui_manager, container=minigame_choice_window, object_id=config.CHOOSE_8PUZZLE_BUTTON_ID
        )
        choose_caro_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(20, 95, button_width_ui, 40), text="Cờ Caro",
            manager=ui_manager, container=minigame_choice_window, object_id=config.CHOOSE_CARO_BUTTON_ID
        )
        choose_mouse_cheese_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(20, 145, button_width_ui, 40), text="Chuột và Pho Mát",
            manager=ui_manager, container=minigame_choice_window, object_id=config.CHOOSE_MOUSE_CHEESE_BUTTON_ID
        )

    def hide_minigame_choice_ui():
        nonlocal minigame_choice_window, choose_8puzzle_button, choose_caro_button, choose_mouse_cheese_button, minigame_choice_title
        if choose_8puzzle_button: choose_8puzzle_button.kill(); choose_8puzzle_button = None
        if choose_caro_button: choose_caro_button.kill(); choose_caro_button = None
        if choose_mouse_cheese_button: choose_mouse_cheese_button.kill(); choose_mouse_cheese_button = None
        if minigame_choice_title: minigame_choice_title.kill(); minigame_choice_title = None
        if minigame_choice_window: minigame_choice_window.kill(); minigame_choice_window = None

    def show_mouse_cheese_train_ui():
        nonlocal mouse_cheese_train_window, mouse_cheese_train_input, mouse_cheese_confirm_button, mouse_cheese_cancel_button
        if mouse_cheese_train_window is not None: return
        window_width, window_height = 300, 200
        window_x, window_y = (config.SCREEN_WIDTH - window_width) // 2, (config.SCREEN_HEIGHT - window_height) // 2
        mouse_cheese_train_window = pygame_gui.elements.UIWindow(
            rect=pygame.Rect(window_x, window_y, window_width, window_height),
            manager=ui_manager, window_display_title=config.MOUSE_CHEESE_TRAIN_WINDOW_TITLE
        )
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 5, window_width - 20, 30), text="Nhập số lần chơi (1-10):",
            manager=ui_manager, container=mouse_cheese_train_window
        )
        mouse_cheese_train_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(20, 45, window_width - 40, 40), manager=ui_manager,
            container=mouse_cheese_train_window, object_id=config.MOUSE_CHEESE_TRAIN_INPUT_ID
        )
        mouse_cheese_train_input.set_allowed_characters('numbers')
        mouse_cheese_confirm_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(20, 95, (window_width - 60) // 2, 40), text="Xác nhận",
            manager=ui_manager, container=mouse_cheese_train_window, object_id=config.MOUSE_CHEESE_CONFIRM_BUTTON_ID
        )
        mouse_cheese_cancel_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((window_width - 40) // 2 + 20, 95, (window_width - 60) // 2, 40), text="Hủy",
            manager=ui_manager, container=mouse_cheese_train_window, object_id=config.MOUSE_CHEESE_CANCEL_BUTTON_ID
        )

    def hide_mouse_cheese_train_ui():
        nonlocal mouse_cheese_train_window, mouse_cheese_train_input, mouse_cheese_confirm_button, mouse_cheese_cancel_button
        if mouse_cheese_train_input: mouse_cheese_train_input.kill(); mouse_cheese_train_input = None
        if mouse_cheese_confirm_button: mouse_cheese_confirm_button.kill(); mouse_cheese_confirm_button = None
        if mouse_cheese_cancel_button: mouse_cheese_cancel_button.kill(); mouse_cheese_cancel_button = None
        if mouse_cheese_train_window: mouse_cheese_train_window.kill(); mouse_cheese_train_window = None


    while running:
        time_delta = clock.tick(config.FPS) / 1000.0
        camera.update(player)

        if status_message_timer > 0:
            status_message_timer -= time_delta
            if status_message_timer <= 0:
                status_message_label.set_text("")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if current_game_state == config.ST_PLAYING_PUZZLE:
                        eight_puzzle_minigame.is_active = False # Main set is_active
                        eight_puzzle_minigame.cleanup_ui() # Dọn dẹp nút AI
                        current_game_state = config.ST_PLAYING_MAIN
                        status_message_label.set_text("Đã hủy 8-Puzzle.")
                        status_message_timer = 2
                        if point_manager.collected_point_for_puzzle_center: # Hoàn lại điểm nếu hủy
                            point_manager.collected_point_for_puzzle_center = None
                    # ... (xử lý ESC cho các minigame khác và trạng thái khác)
                    elif current_game_state == config.ST_PLAYING_CARO:
                        caro_minigame.is_active = False
                        current_game_state = config.ST_PLAYING_MAIN
                        status_message_label.set_text("Đã hủy Cờ Caro.")
                        status_message_timer = 2
                        if point_manager.collected_point_for_puzzle_center: point_manager.collected_point_for_puzzle_center = None
                    elif current_game_state == config.ST_PLAYING_MOUSE_CHEESE:
                        maze_minigame.is_active = False
                        current_game_state = config.ST_PLAYING_MAIN
                        status_message_label.set_text("Đã hủy Chuột và Pho Mát.")
                        status_message_timer = 2
                        if point_manager.collected_point_for_puzzle_center: point_manager.collected_point_for_puzzle_center = None
                        mouse_cheese_train_count = 0; mouse_cheese_current_train = 0
                    elif current_game_state == config.ST_CHOOSING_MINIGAME:
                        hide_minigame_choice_ui()
                        current_game_state = config.ST_PLAYING_MAIN
                        status_message_label.set_text("Đã hủy chọn minigame.")
                        status_message_timer = 2
                        if point_manager.collected_point_for_puzzle_center: point_manager.collected_point_for_puzzle_center = None
                    elif current_game_state == config.ST_INPUT_MOUSE_CHEESE_TRAIN:
                        hide_mouse_cheese_train_ui()
                        current_game_state = config.ST_PLAYING_MAIN
                        status_message_label.set_text("Đã hủy nhập số lần chơi.")
                        status_message_timer = 2
                        if point_manager.collected_point_for_puzzle_center: point_manager.collected_point_for_puzzle_center = None
                    elif current_game_state == config.ST_PLAYING_MAIN and path_finder.input_active:
                         path_finder.disable_input()
                    else:
                        running = False
                
                # ... (xử lý các phím khác như F1, P, Ctrl+F)
                if current_game_state == config.ST_PLAYING_MAIN and not path_finder.input_active:
                    if event.key == pygame.K_F1:
                        debug_draw_tiles = not debug_draw_tiles
                        print(f"Debug vẽ tile: {'Bật' if debug_draw_tiles else 'Tắt'}")
                    if event.key == pygame.K_p: # Logic cho phím P (tìm đường)
                        if point_manager.is_visible and point_manager.current_point_center:
                            path_finder.enable_input() # Kích hoạt UI chọn thuật toán của PathFinder
                        else:
                            status_message_label.set_text("Không có điểm đến cho Taxi!")
                            status_message_timer = 2
                    if event.key == pygame.K_f: # Logic cho Ctrl+F (mở minigame)
                        keys_pressed = pygame.key.get_pressed()
                        is_ctrl_pressed = keys_pressed[pygame.K_LCTRL] or keys_pressed[pygame.K_RCTRL]
                        if is_ctrl_pressed:
                            is_near_point, value_of_point = point_manager.is_player_at_point_for_auto_puzzle(player.rect.center)
                            if is_near_point and not eight_puzzle_minigame.is_active and \
                               not caro_minigame.is_active and not maze_minigame.is_active and \
                               minigame_choice_window is None and mouse_cheese_train_window is None:
                                points_to_collect_value = value_of_point # Lưu giá trị điểm sẽ nhận
                                current_game_state = config.ST_CHOOSING_MINIGAME
                                show_minigame_choice_ui()
                                player.set_actions([], None) # Dừng di chuyển của player
                                status_message_label.set_text("Đến điểm! Chọn một minigame.")
                                status_message_timer = 3
                            elif not is_near_point:
                                status_message_label.set_text("Cần ở gần điểm hơn để chơi minigame (Ctrl+F).")
                                status_message_timer = 2
                            else:
                                status_message_label.set_text("Không thể mở giao diện chọn minigame.")
                                status_message_timer = 2


            if current_game_state == config.ST_PLAYING_MAIN and path_finder.input_active:
                path_finder.handle_input(event, point_manager) # Xử lý input cho PathFinder UI

            # --- Xử lý sự kiện cho 8-Puzzle ---
            if current_game_state == config.ST_PLAYING_PUZZLE and eight_puzzle_minigame.is_active:
                puzzle_event_outcome = eight_puzzle_minigame.handle_event(event)

                if puzzle_event_outcome == config.PUZZLE_EVENT_AI_SOLVE_REQUEST:
                    if player.money >= config.PUZZLE_SOLVE_COST:
                        player.spend_money(config.PUZZLE_SOLVE_COST)
                        eight_puzzle_minigame.attempt_ai_solve() # AI giải, set just_won, solved_by_ai
                        # Thông báo thắng/thua và thưởng sẽ được xử lý khi puzzle đóng (puzzle_event_outcome == True)
                        if eight_puzzle_minigame.solved_by_ai and eight_puzzle_minigame.just_won:
                            status_message_label.set_text(f"AI đã giải! (-{config.PUZZLE_SOLVE_COST} tiền).")
                        else: # AI không giải được (trường hợp hiếm)
                            status_message_label.set_text(f"AI không giải được. (-{config.PUZZLE_SOLVE_COST} tiền).")
                        status_message_timer = 2 # Thông báo tạm thời
                    else:
                        status_message_label.set_text(f"Không đủ {config.PUZZLE_SOLVE_COST} tiền cho AI!")
                        status_message_timer = 2
                
                elif puzzle_event_outcome == True: # Puzzle báo hiệu nên đóng (thắng, thua, ESC)
                    if eight_puzzle_minigame.just_won and not eight_puzzle_minigame.win_processed_in_main:
                        player.add_money(points_to_collect_value) # Thưởng tiền
                        if eight_puzzle_minigame.solved_by_ai:
                            status_message_label.set_text(f"AI giải! +{points_to_collect_value} (-{config.PUZZLE_SOLVE_COST}) tiền")
                        else:
                            status_message_label.set_text(f"Thắng 8-Puzzle! +{points_to_collect_value} tiền")
                        point_manager.finalize_collection()
                        eight_puzzle_minigame.win_processed_in_main = True
                    elif not eight_puzzle_minigame.just_won: # Không thắng (ví dụ: thoát bằng ESC)
                        status_message_label.set_text("8-Puzzle: Không hoàn thành!")
                        if point_manager.collected_point_for_puzzle_center: # Hoàn lại điểm nếu hủy/không hoàn thành
                            point_manager.collected_point_for_puzzle_center = None
                    
                    status_message_timer = 3
                    current_game_state = config.ST_PLAYING_MAIN
                    eight_puzzle_minigame.is_active = False
                    eight_puzzle_minigame.cleanup_ui() # Dọn dẹp nút AI

            # --- Xử lý sự kiện cho Caro ---
            if current_game_state == config.ST_PLAYING_CARO and caro_minigame.is_active:
                caro_should_close_signal = caro_minigame.handle_event(event)
                if caro_should_close_signal:
                    if caro_minigame.winner == caro_minigame.human_player_mark:
                        player.add_money(points_to_collect_value)
                        point_manager.finalize_collection()
                    elif caro_minigame.winner == caro_minigame.ai_player_mark or caro_minigame.winner == 0: # Hòa hoặc AI thắng
                        if point_manager.collected_point_for_puzzle_center: # Hoàn lại điểm nếu không thắng
                            point_manager.collected_point_for_puzzle_center = None
                    status_message_label.set_text(caro_minigame.message)
                    status_message_timer = caro_minigame.message_timer if caro_minigame.message_timer > 0 else 3
                    current_game_state = config.ST_PLAYING_MAIN
                    caro_minigame.is_active = False
            
            # --- Xử lý sự kiện cho MazeGame ---
            if current_game_state == config.ST_PLAYING_MOUSE_CHEESE and maze_minigame.is_active:
                maze_minigame.handle_event(event)


            # --- Xử lý các nút UI chung (chọn minigame, nhập số lần train) ---
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if current_game_state == config.ST_CHOOSING_MINIGAME:
                    if choose_8puzzle_button and event.ui_element == choose_8puzzle_button:
                        hide_minigame_choice_ui()
                        current_game_state = config.ST_PLAYING_PUZZLE
                        eight_puzzle_minigame.start_game() # Tạo nút AI ở đây
                        eight_puzzle_minigame.is_active = True
                        player.set_actions([], None)
                        status_message_label.set_text("Giải đố 8-Puzzle!")
                        status_message_timer = 2
                    # ... (xử lý chọn Caro, Mouse & Cheese) ...
                    elif choose_caro_button and event.ui_element == choose_caro_button:
                        hide_minigame_choice_ui()
                        current_game_state = config.ST_PLAYING_CARO
                        caro_minigame.start_new_game(ai_difficulty=config.DEFAULT_CARO_AI)
                        caro_minigame.is_active = True
                        player.set_actions([], None)
                        status_message_label.set_text("Chơi Cờ Caro!")
                        status_message_timer = 2
                    elif choose_mouse_cheese_button and event.ui_element == choose_mouse_cheese_button:
                        hide_minigame_choice_ui()
                        current_game_state = config.ST_INPUT_MOUSE_CHEESE_TRAIN
                        show_mouse_cheese_train_ui()
                        player.set_actions([], None)
                        status_message_label.set_text("Nhập số lần chơi Chuột và Pho Mát.")
                        status_message_timer = 2
                
                elif current_game_state == config.ST_INPUT_MOUSE_CHEESE_TRAIN:
                    # ... (xử lý xác nhận/hủy cho Mouse & Cheese train) ...
                    if mouse_cheese_confirm_button and event.ui_element == mouse_cheese_confirm_button:
                        try:
                            train_count = int(mouse_cheese_train_input.get_text())
                            if 1 <= train_count <= config.MOUSE_CHEESE_MAX_TRAIN:
                                total_cost = train_count * config.MOUSE_CHEESE_COST_PER_TRAIN
                                if player.spend_money(total_cost):
                                    mouse_cheese_train_count = train_count
                                    mouse_cheese_current_train = 0
                                    hide_mouse_cheese_train_ui()
                                    current_game_state = config.ST_PLAYING_MOUSE_CHEESE
                                    maze_minigame.start_game()
                                    maze_minigame.is_active = True
                                    status_message_label.set_text(f"Bắt đầu {train_count} lần chơi (-{total_cost} tiền).")
                                    status_message_timer = 2
                                else:
                                    status_message_label.set_text(f"Không đủ tiền! Cần: {total_cost}")
                                    status_message_timer = 2
                            else:
                                status_message_label.set_text(f"Số lần chơi từ 1-{config.MOUSE_CHEESE_MAX_TRAIN}.")
                                status_message_timer = 2
                        except ValueError:
                            status_message_label.set_text("Vui lòng nhập một số hợp lệ.")
                            status_message_timer = 2
                    elif mouse_cheese_cancel_button and event.ui_element == mouse_cheese_cancel_button:
                        hide_mouse_cheese_train_ui()
                        current_game_state = config.ST_PLAYING_MAIN
                        status_message_label.set_text("Đã hủy nhập số lần chơi.")
                        status_message_timer = 2


            ui_manager.process_events(event)

        if not running:
            break

        # --- Cập nhật trạng thái game ---
        if current_game_state == config.ST_PLAYING_MAIN:
            player.update(collidable_tiles, time_delta)
        elif current_game_state == config.ST_PLAYING_PUZZLE:
            if eight_puzzle_minigame.is_active:
                eight_puzzle_minigame.update(time_delta)
                # Không cần kiểm tra game_over ở đây nữa, vì việc đóng puzzle được xử lý qua event
        # ... (cập nhật cho Caro, MazeGame) ...
        elif current_game_state == config.ST_PLAYING_CARO:
            if caro_minigame.is_active: caro_minigame.update(time_delta)
        elif current_game_state == config.ST_PLAYING_MOUSE_CHEESE:
            if maze_minigame.is_active:
                maze_minigame.update()
                if not maze_minigame.is_active: # Maze tự set is_active = False khi kết thúc 1 lượt
                    if maze_minigame.game_won:
                        player.add_money(config.MOUSE_CHEESE_REWARD)
                        status_message_label.set_text(f"Thắng Chuột và Pho Mát! +{config.MOUSE_CHEESE_REWARD} tiền")
                        point_manager.finalize_collection() # Chỉ finalize nếu thắng
                    else:
                        status_message_label.set_text("Chuột và Pho Mát: Không thắng!")
                        if point_manager.collected_point_for_puzzle_center: # Hoàn lại điểm nếu không thắng
                             point_manager.collected_point_for_puzzle_center = None
                    status_message_timer = 2
                    mouse_cheese_current_train += 1
                    if mouse_cheese_current_train < mouse_cheese_train_count:
                        maze_minigame.start_game() # Bắt đầu lượt mới
                        maze_minigame.is_active = True
                        status_message_label.set_text(f"Lần chơi {mouse_cheese_current_train + 1}/{mouse_cheese_train_count}")
                        status_message_timer = 1.5
                    else: # Hết số lượt train
                        current_game_state = config.ST_PLAYING_MAIN
                        mouse_cheese_train_count = 0
                        mouse_cheese_current_train = 0
                        if point_manager.collected_point_for_puzzle_center and not maze_minigame.game_won : # Nếu lượt cuối không thắng và điểm vẫn còn
                            point_manager.collected_point_for_puzzle_center = None


        ui_manager.update(time_delta)
        money_label.set_text(f"Tiền: {player.money}")

        # --- Vẽ màn hình ---
        screen.fill(config.BLACK) # Màu nền mặc định
        # Vẽ bản đồ chính và camera
        background_rect = background_img_full.get_rect(topleft=(0, 0))
        screen.blit(background_img_full, camera.apply_rect(background_rect))

        if debug_draw_tiles and current_game_state == config.ST_PLAYING_MAIN:
            for tile_sprite in collidable_tiles:
                tile_sprite.draw(screen, camera) # Giả sử Tile có hàm draw(surface, camera)

        if current_game_state in [config.ST_PLAYING_MAIN, config.ST_CHOOSING_MINIGAME, config.ST_INPUT_MOUSE_CHEESE_TRAIN] or path_finder.input_active:
            point_manager.draw(screen, camera)
            player.draw(screen, camera)
        
        # Vẽ minigames nếu đang active
        if current_game_state == config.ST_PLAYING_PUZZLE and eight_puzzle_minigame.is_active:
            # Lớp phủ mờ cho minigame (có thể vẽ ở đây hoặc trong draw của minigame)
            overlay_surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay_surface.fill(config.CARO_OVERLAY_COLOR) # Dùng chung màu overlay
            screen.blit(overlay_surface, (0,0))
            eight_puzzle_minigame.draw(screen)
        elif current_game_state == config.ST_PLAYING_CARO and caro_minigame.is_active:
            overlay_surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay_surface.fill(config.CARO_OVERLAY_COLOR)
            screen.blit(overlay_surface, (0,0))
            caro_minigame.draw(screen)
        elif current_game_state == config.ST_PLAYING_MOUSE_CHEESE and maze_minigame.is_active:
            # MazeGame tự vẽ overlay nếu cần
            maze_minigame.draw()


        ui_manager.draw_ui(screen) # Vẽ tất cả các element của pygame_gui
        pygame.display.flip()

    print("Kết thúc game.")
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()