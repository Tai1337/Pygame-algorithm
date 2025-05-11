import os
import pygame

# --- Hàm trợ giúp để lấy đường dẫn tài sản ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ASSETS_DIR = os.path.join(PROJECT_ROOT, 'assets')

def get_asset_path(relative_path_from_assets_dir):
    return os.path.join(ASSETS_DIR, relative_path_from_assets_dir)

# --- Cài đặt màn hình và game ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 32
FPS = 60

# --- Màu sắc ---
RED = (255, 0, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
BLUE = (100, 100, 255)
YELLOW = (255, 255, 0)
TEXT_COLOR = BLACK
PUZZLE_BG_COLOR = (50, 50, 50, 200)

# --- Đường dẫn tệp tài sản ---
MAP_IMAGE_PATH = get_asset_path("images/map.png")
PLAYER_IMAGE_BASE_PATH = get_asset_path("images/character")
POINT_IMAGE_PATH = get_asset_path("images/poin.png")
FLOOR_BLOCK_CSV_PATH = get_asset_path("maps_data/map_floorblock.csv")
ENTITY_CSV_PATH = get_asset_path("maps_data/map_Entity.csv")
Q_TABLE_TRAINED_PATH = get_asset_path("q_tables/q_table_trained.json")
THEME_FILE_PATH = get_asset_path("ui_themes/theme.json")

# --- Trạng thái Game ---
ST_PLAYING_MAIN = "playing_main"
ST_PLAYING_PUZZLE = "playing_puzzle"
ST_PLAYING_CARO = "playing_caro"
ST_PLAYING_MOUSE_CHEESE = "playing_mouse_cheese"  # Thêm trạng thái cho MouseCheeseGame
ST_CHOOSING_MINIGAME = "choosing_minigame"
ST_INPUT_MOUSE_CHEESE_TRAIN = "input_mouse_cheese_train"  # Trạng thái nhập số lần train

# --- Hằng số cho Player ---
PLAYER_DEFAULT_SPEED = 4
INITIAL_PLAYER_MONEY = 500
PLAYER_ENTITY_ID = '100'

# --- Hằng số cho PointManager ---
POINT_ENTITY_ID = '214'
COLLECT_DISTANCE_SQ = (TILE_SIZE * 1.5)**2
POINT_COLLECT_VALUE = 25
PLAYER_AT_POINT_DISTANCE_SQ = (TILE_SIZE // 2)**2

# --- Hằng số cho 8-Puzzle Game ---
PUZZLE_GRID_SIZE = 3
PUZZLE_TILE_SIZE = 80
PUZZLE_GAP = 5
PUZZLE_BORDER = 10

# --- Hằng số cho Pathfinding Algorithms ---
BEAM_SEARCH_WIDTH_DEFAULT = 3
DEFAULT_PATHFINDING_ALGORITHM_NAME = "A* (A-star)"
BACKTRACKING_MAX_DEPTH_FACTOR = 1.5
BACKTRACKING_MAX_CALLS_FACTOR = 5

# --- Tiền tính taxi ---
TAXI_BASE_FARE = 5
TAXI_COST_PER_VISITED_NODE = 0.05
TAXI_COST_PER_MOVE = 0.5
TAXI_MIN_FARE_IF_PATH_FOUND = 10

# --- Cài đặt Game Caro ---
CARO_BOARD_SIZE = 10
CARO_WIN_LENGTH = 5
CARO_TILE_SIZE = 40
CARO_FONT_SIZE = 30
CARO_MESSAGE_FONT_SIZE = 36
CARO_MARK_THICKNESS = 4
CARO_WIN_LINE_THICKNESS = 5
CARO_BOARD_BG_COLOR = (200, 200, 200)
CARO_GRID_LINE_COLOR = BLACK
CARO_X_COLOR = BLUE
CARO_O_COLOR = RED
CARO_WIN_LINE_COLOR = GREEN
CARO_OVERLAY_COLOR = (0, 0, 0, 150)
DEFAULT_CARO_AI = 'minimax'
CARO_MINIMAX_DEPTH = 3
CARO_BEAM_WIDTH = 3
CARO_BEAM_DEPTH = 2
CARO_QL_LEARNING_RATE = 0.1
CARO_QL_DISCOUNT_FACTOR = 0.9
CARO_QL_EXPLORATION_RATE = 0.1
CARO_REWARD_WIN = 100
CARO_REWARD_LOSS = -100
CARO_REWARD_DRAW = 10
CARO_REWARD_MOVE = -1

# --- Cài đặt MouseCheeseGame ---
MOUSE_CHEESE_COST_PER_TRAIN = 5  # Chi phí mỗi lần train
MOUSE_CHEESE_REWARD = 35  # Thưởng khi thắng (đã có trong mouse_cheese_game.py)
MOUSE_CHEESE_MAX_TRAIN = 10  # Giới hạn số lần train tối đa

# --- UI IDs cho lựa chọn Minigame ---
MINIGAME_CHOICE_WINDOW_TITLE = "Chọn Minigame"
CHOOSE_8PUZZLE_BUTTON_ID = "#choose_8puzzle_button"
CHOOSE_CARO_BUTTON_ID = "#choose_caro_button"
CHOOSE_MOUSE_CHEESE_BUTTON_ID = "#choose_mouse_cheese_button"  # ID cho nút MouseCheeseGame
MOUSE_CHEESE_TRAIN_WINDOW_TITLE = "Nhập số lần chơi MouseCheese"
MOUSE_CHEESE_TRAIN_INPUT_ID = "#mouse_cheese_train_input"
MOUSE_CHEESE_CONFIRM_BUTTON_ID = "#mouse_cheese_confirm_button"
MOUSE_CHEESE_CANCEL_BUTTON_ID = "#mouse_cheese_cancel_button"

# --- Hằng số cho 8-Puzzle Game ---
PUZZLE_GRID_SIZE = 3
PUZZLE_TILE_SIZE = 80
PUZZLE_GAP = 5
PUZZLE_BORDER = 10
PUZZLE_SOLVE_COST = 50  # Chi phí để AI giải puzzle
PUZZLE_EVENT_AI_SOLVE_REQUEST = "puzzle_ai_solve_request" # Event ID khi yêu cầu AI giải
SOLVE_AI_BUTTON_WIDTH = 180
SOLVE_AI_BUTTON_HEIGHT = 40   # Hằng số gây lỗi nếu thiếu
SOLVE_AI_BUTTON_MARGIN_TOP = 20 # Khoảng cách từ puzzle xuống nút. Hằng số này cũng cần có.
SOLVE_AI_BUTTON_TEXT = f"Giải bằng AI ({PUZZLE_SOLVE_COST} tiền)"
AI_PUZZLE_SOLVE_STEP_DURATION = 0.3