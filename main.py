# main.py

import pygame
import csv
import sys
import os
import io
import pygame_gui

from player import Player
from pathfinder import PathFinder
from point_manager import PointManager
from pathfinding_algorithms import DEFAULT_PATHFINDING_COST # Cần cho logic kiểm tra tiền khi nhấn 'P'
from eight_puzzle_game import EightPuzzleGame # <<<<<< THÊM IMPORT NÀY

# --- Hằng số ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 32
FPS = 60
THEME_FILE_PATH = 'theme.json' # Đường dẫn đến file theme

# --- Màu sắc (chỉ giữ lại những màu không thuộc UI nếu cần) ---
RED = (255, 0, 0) # Dùng cho debug tile

# --- Đường dẫn file ---
MAP_IMAGE_PATH = "map.png"
PLAYER_IMAGE_PATH = "character"
FLOOR_BLOCK_CSV_PATH = "map_floorblock.csv"
ENTITY_CSV_PATH = "map_Entity.csv"

# --- Game States ---  <<<<<< THÊM TRẠNG THÁI GAME
ST_PLAYING_MAIN = "playing_main"
ST_PLAYING_PUZZLE = "playing_puzzle"

# --- Hàm đọc dữ liệu CSV ---
def load_csv(filepath):
    data = []
    if not os.path.exists(filepath):
        print(f"Lỗi: Không tìm thấy file CSV '{filepath}'")
        pygame.quit()
        sys.exit()
    try:
        with open(filepath, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row_data in reader:
                data.append(list(row_data))
    except Exception as e:
        print(f"Lỗi khi đọc file CSV '{filepath}': {e}")
        pygame.quit()
        sys.exit()
    return data

# --- Lớp Tile ---
class Tile(pygame.sprite.Sprite):
    def __init__(self, x, y, size, is_collidable=True):
        super().__init__()
        self.image = pygame.Surface([size, size], pygame.SRCALPHA)
        self.image.set_alpha(0) # Ô va chạm sẽ trong suốt, chỉ dùng để debug
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.is_collidable = is_collidable

    def draw(self, surface, camera): # Vẽ viền đỏ để debug
        if camera.camera_rect.colliderect(self.rect):
             debug_rect = pygame.Rect(self.rect.x, self.rect.y, TILE_SIZE, TILE_SIZE)
             pygame.draw.rect(surface, RED, camera.apply_rect(debug_rect), 1)

# --- Lớp Camera ---
class Camera:
    def __init__(self, world_width, world_height):
        self.camera_rect = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        self.world_width = world_width
        self.world_height = world_height

    def apply(self, entity):
        return entity.rect.move(-self.camera_rect.x, -self.camera_rect.y)

    def apply_rect(self, rect):
        return rect.move(-self.camera_rect.x, -self.camera_rect.y)

    def update(self, target_entity):
        x = -target_entity.rect.centerx + SCREEN_WIDTH // 2
        y = -target_entity.rect.centery + SCREEN_HEIGHT // 2
        # Giới hạn camera trong thế giới game
        x = min(0, x)
        y = min(0, y)
        x = max(-(self.world_width - SCREEN_WIDTH), x)
        y = max(-(self.world_height - SCREEN_HEIGHT), y)
        self.camera_rect.topleft = (round(-x), round(-y))

# --- Hàm chính ---
def main():
    # ... (Phần khởi tạo pygame, screen, clock, ui_manager, background, map data, player, camera, point_manager, path_finder không đổi) ...
    try:
        if sys.stdout.encoding != 'utf-8':
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        if sys.stderr.encoding != 'utf-8':
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except Exception as e:
        print(f"Không thể đặt encoding UTF-8 cho output: {e}")

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Game Thu Thập Điểm - Pygame Taxi")
    clock = pygame.time.Clock()

    ui_manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT), THEME_FILE_PATH)

    try:
        background_img_full = pygame.image.load(MAP_IMAGE_PATH).convert()
    except pygame.error as e:
        print(f"Lỗi nghiêm trọng khi tải ảnh nền '{MAP_IMAGE_PATH}': {e}")
        pygame.quit()
        sys.exit()
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file ảnh nền '{MAP_IMAGE_PATH}'")
        pygame.quit()
        sys.exit()

    floor_block_data = load_csv(FLOOR_BLOCK_CSV_PATH)
    entity_data = load_csv(ENTITY_CSV_PATH)

    num_rows = len(floor_block_data)
    num_cols = max(len(r) for r in floor_block_data) if num_rows > 0 else 0
    world_pixel_width = num_cols * TILE_SIZE
    world_pixel_height = num_rows * TILE_SIZE

    collidable_tiles = pygame.sprite.Group()
    for r_idx, row_data in enumerate(floor_block_data):
        for c_idx, tile_value in enumerate(row_data):
            value = tile_value.strip()
            if value != '-1' and value != '':
                collidable_tiles.add(Tile(c_idx * TILE_SIZE, r_idx * TILE_SIZE, TILE_SIZE, is_collidable=True))

    player_start_x, player_start_y = 100, 100
    player_found = False
    for r_idx, row_data in enumerate(entity_data):
        for c_idx, entity_value in enumerate(row_data):
            if entity_value.strip() == '100':
                player_start_x, player_start_y = c_idx * TILE_SIZE, r_idx * TILE_SIZE
                player_found = True
                break
        if player_found:
            break
    if not player_found:
        print(f"Cảnh báo: Không tìm thấy ID '100' cho người chơi trong '{ENTITY_CSV_PATH}'. Dùng vị trí mặc định ({player_start_x}, {player_start_y}).")

    try:
        player = Player(player_start_x, player_start_y, PLAYER_IMAGE_PATH)
    except Exception as e:
        print(f"Lỗi nghiêm trọng khi tạo Player: {e}")
        pygame.quit()
        sys.exit()

    camera = Camera(world_pixel_width, world_pixel_height)
    point_manager = PointManager(entity_data, TILE_SIZE)
    path_finder = PathFinder(floor_block_data, TILE_SIZE, ui_manager, player)

    eight_puzzle_minigame = EightPuzzleGame(SCREEN_WIDTH, SCREEN_HEIGHT)
    current_game_state = ST_PLAYING_MAIN
    points_to_collect_value = 0

    money_label = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect(10, 10, 200, 30),
        text=f"Tiền: {player.money}",
        manager=ui_manager,
        object_id="#money_label"
    )
    status_message_label = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect(SCREEN_WIDTH // 2 - 175, 10, 350, 30),
        text="",
        manager=ui_manager,
        object_id="#status_message"
    )
    status_message_timer = 0

    print("Bắt đầu vòng lặp game...")
    running = True
    debug_draw_tiles = False

    while running:
        time_delta = clock.tick(FPS) / 1000.0

        if status_message_timer > 0:
            status_message_timer -= time_delta
            if status_message_timer <= 0:
                status_message_label.set_text("")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if current_game_state == ST_PLAYING_PUZZLE:
                        eight_puzzle_minigame.is_active = False
                        current_game_state = ST_PLAYING_MAIN
                        status_message_label.set_text("Đã hủy giải đố.")
                        status_message_timer = 2
                    elif current_game_state == ST_PLAYING_MAIN and path_finder.input_active:
                        path_finder.disable_input()
                    else:
                        running = False

                if current_game_state == ST_PLAYING_MAIN:
                    if event.key == pygame.K_F1:
                        debug_draw_tiles = not debug_draw_tiles
                        print(f"Debug vẽ tile: {'Bật' if debug_draw_tiles else 'Tắt'}")
                    if event.key == pygame.K_p and not path_finder.input_active:
                        path_finder.enable_input()
                        print("Mở giao diện chọn gói cước Taxi.")

            if current_game_state == ST_PLAYING_MAIN:
                 path_finder.handle_input(event, point_manager)

            ui_manager.process_events(event)

            if current_game_state == ST_PLAYING_PUZZLE:
                puzzle_should_close_signal = eight_puzzle_minigame.handle_event(event)
                # puzzle_should_close_signal giờ chủ yếu là khi ESC hoặc click khi đã thắng
                if puzzle_should_close_signal:
                    # Nếu đóng mà không phải do thắng (ESC), thì set thông báo
                    # Việc thắng đã được xử lý ngay khi eight_puzzle_minigame.just_won = True
                    if not eight_puzzle_minigame.check_win() and not eight_puzzle_minigame.just_won : # Thêm check just_won để không ghi đè thông báo thắng
                        status_message_label.set_text("Giải đố thất bại!")
                        status_message_timer = 2
                    current_game_state = ST_PLAYING_MAIN
                    eight_puzzle_minigame.is_active = False # Đảm bảo puzzle đóng


        # --- Game Logic Cập nhật ---
        if current_game_state == ST_PLAYING_MAIN:
            player.update(collidable_tiles, time_delta)
            camera.update(player)
            keys = pygame.key.get_pressed()
            can_attempt, potential_value = point_manager.can_attempt_collect(player.rect.center, keys[pygame.K_f])
            if can_attempt:
                current_game_state = ST_PLAYING_PUZZLE
                points_to_collect_value = potential_value
                eight_puzzle_minigame.start_game() # start_game đã reset just_won và win_processed_in_main
                player.set_actions([])
                status_message_label.set_text("Giải đố để nhận điểm!")
                status_message_timer = 3

            if keys[pygame.K_p] and not path_finder.input_active and point_manager.is_visible and point_manager.current_point_center:
                path_actions, success = path_finder.find_path_to_point(player.rect.center, point_manager.current_point_center)
                money_label.set_text(f"Tiền: {player.money}")
                if success and path_actions:
                    player.set_actions(path_actions)
                    status_message_label.set_text("Taxi đang đến!")
                    status_message_timer = 2
                elif success and not path_actions:
                    status_message_label.set_text("Taxi đã thử nhưng không tìm thấy đường!")
                    status_message_timer = 2
                elif not success:
                    status_message_label.set_text("Yêu cầu Taxi thất bại!")
                    status_message_timer = 2

        elif current_game_state == ST_PLAYING_PUZZLE:
            eight_puzzle_minigame.update(time_delta) # Update puzzle (timer, etc.)

            # >>>>> LOGIC XỬ LÝ THẮNG NGAY LẬP TỨC <<<<<
            if eight_puzzle_minigame.just_won and not eight_puzzle_minigame.win_processed_in_main:
                player.add_money(points_to_collect_value)
                money_label.set_text(f"Tiền: {player.money}")
                status_message_label.set_text(f"Giải đố thành công! +{points_to_collect_value} tiền")
                status_message_timer = 3
                point_manager.finalize_collection() # THU THẬP VÀ SPAWN ĐIỂM MỚI NGAY
                eight_puzzle_minigame.win_processed_in_main = True # Đánh dấu đã xử lý thắng cho lượt này

            # Kiểm tra nếu puzzle UI nên đóng (do timer hết hoặc người dùng click/ESC)
            if not eight_puzzle_minigame.is_active:
                # Nếu is_active là False, nghĩa là puzzle đã tự đóng hoặc được đóng từ event loop
                # Chuyển về game chính. Các thông báo đã được set.
                current_game_state = ST_PLAYING_MAIN


        ui_manager.update(time_delta)

        # --- Vẽ màn hình ---
        screen.fill((0,0,0))
        background_rect = background_img_full.get_rect(topleft=(0,0))
        screen.blit(background_img_full, camera.apply_rect(background_rect))

        if debug_draw_tiles and current_game_state == ST_PLAYING_MAIN:
            for tile_sprite in collidable_tiles:
                tile_sprite.draw(screen, camera)

        point_manager.draw(screen, camera)
        player.draw(screen, camera)

        if current_game_state == ST_PLAYING_PUZZLE:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            eight_puzzle_minigame.draw(screen) # Puzzle vẫn được vẽ để hiển thị thông báo thắng

        ui_manager.draw_ui(screen)
        pygame.display.flip()

    print("Kết thúc game.")
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()