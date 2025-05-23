import os
import pygame

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ASSETS_DIR = os.path.join(PROJECT_ROOT, 'assets')

def get_asset_path(relative_path_from_assets_dir):
    return os.path.join(ASSETS_DIR, relative_path_from_assets_dir)

# Cài đặt màn hình
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 32
FPS = 60

TARGET_ITEMS_TO_WIN = 4 # Số lượng vật phẩm cần thu thập để thắng
MAIN_GAME_TIME_LIMIT_SECONDS = 300 # Thời gian chơi game

# Cài đặt màu sắc
RED = (255, 0, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
BLUE = (100, 100, 255)
TEXT_COLOR = BLACK
PUZZLE_BG_COLOR = (50, 50, 50, 200)
GRAY = (200, 200, 200)
LIGHT_GRAY = (211, 211, 211)
LIGHT_BLUE = (173, 216, 230)
DARK_BLUE = (0, 0, 139)
GREEN_SOLVE = (0, 100, 0)
RED_MSG = (200, 0, 0)
BLUE_MSG = (0, 0, 200)
SELECTED_COLOR = (255, 165, 0)
BUTTON_COLOR = (100, 180, 100)
BUTTON_TEXT_COLOR = (0, 0, 0)
TRY_COLOR = (255, 215, 0)
KEEP_COLOR = (0, 200, 0)
BACKTRACK_COLOR = (255, 69, 0)
TRY_COLOR = (255, 215, 0)  
KEEP_COLOR = (0, 200, 0)  
BACKTRACK_COLOR = (255, 69, 0)  

# Đường dẫn link và hình ảnh
MAP_IMAGE_PATH = get_asset_path("images/map.png")
PLAYER_IMAGE_BASE_PATH = get_asset_path("images/character")
POINT_IMAGE_PATH = get_asset_path("images/poin.png")

FLOOR_BLOCK_CSV_PATH = get_asset_path("maps_data/map_floorblock.csv")
ENTITY_CSV_PATH = get_asset_path("maps_data/map_Entity.csv")
MAZE_Q_TABLE_CSV_PATH = get_asset_path("q_tables/maze_q_table.csv") # Tệp hướng dẫn q_learning
THEME_FILE_PATH = get_asset_path("ui_themes/theme.json")

# Trạng thái chơi game
ST_PLAYING_MAIN = "playing_main"
ST_PLAYING_PUZZLE = "playing_puzzle"
ST_CHOOSING_MINIGAME = "choosing_minigame"
ST_ENTERING_TRAINING_EPISODES = "entering_training_episodes" # Nhập số lượt huấn luyện
ST_PLAYER_WON = "PLAYER_WON"
ST_GAME_OVER_TIME = "GAME_OVER_TIME"
ST_GAME_OVER_MONEY = "GAME_OVER_MONEY"

# Cài đặt người chơi
PLAYER_DEFAULT_SPEED = 4
INITIAL_PLAYER_MONEY = 100
PLAYER_ENTITY_ID = '100'

# Cài đặt điểm để thu thập
POINT_ENTITY_ID = '214'
COLLECT_DISTANCE_SQ = (TILE_SIZE * 1.5)**2
POINT_COLLECT_VALUE = 25
PLAYER_AT_POINT_DISTANCE_SQ = (TILE_SIZE // 2)**2

# Phần thưởng và hình phạt
MINIGAME_WIN_REWARD = 20
MINIGAME_LOSE_PENALTY = -10

# Dùng để tính gói cước
TAXI_BASE_FARE = 5
TAXI_COST_PER_VISITED_NODE = 0.01
TAXI_COST_PER_MOVE = 0.05
TAXI_MIN_FARE_IF_PATH_FOUND = 10

# Hằng số cho game 8-Puzzle
PUZZLE_GRID_SIZE = 3
PUZZLE_TILE_SIZE = 80
PUZZLE_GAP = 5
PUZZLE_BORDER = 10
SOLVE_AI_BUTTON_WIDTH = 200
SOLVE_AI_BUTTON_HEIGHT = 40
SOLVE_AI_BUTTON_MARGIN_TOP = 10
PUZZLE_SOLVE_COST = 30
SOLVE_AI_BUTTON_TEXT = "Bỏ qua trò chơi (Trừ {cost} tiền)"
AI_SOLVED_DEDUCTION_MESSAGE = "Đã bỏ qua trò chơi, trừ {cost} tiền"
PUZZLE_EVENT_AI_SOLVE_REQUEST = pygame.USEREVENT + 10
PUZZLE_AI_UCS_MAX_EXPLORE_NODES = 700000
AI_PUZZLE_SOLVE_STEP_DURATION = 0.4

# Hằng số cho game Sudoku
SUDOKU_GRID_SIZE = 4
SUDOKU_CELL_SIZE = 80
SUDOKU_SOLVE_COST = 30
SUDOKU_TIME_LIMIT = 60
SUDOKU_AI_STEP_DURATION = 0.5

# Hằng số cho game con rắn
SNAKE_CELL_SIZE = 20
SNAKE_GRID_WIDTH = 25
SNAKE_GRID_HEIGHT = 20
SNAKE_INITIAL_LENGTH = 3
SNAKE_POINTS_TO_WIN = 5
SNAKE_PLAYER_MOVE_INTERVAL = 0.1
SNAKE_COLLISION_COST = 10
SNAKE_COLOR = (34, 177, 76)
SNAKE_HEAD_COLOR = (0, 128, 0)
FOOD_COLOR = (237, 28, 36)
SNAKE_GAME_AREA_BG_COLOR = (30, 30, 30)
SNAKE_GRID_LINE_COLOR = (50, 50, 50)

# Hằng số cho game Caro
CARO_BOARD_SIZE = 15
CARO_WIN_LENGTH = 5
CARO_TILE_SIZE = 30
CARO_FONT_SIZE = 30
CARO_MESSAGE_FONT_SIZE = 30
CARO_OVERLAY_COLOR = (30, 30, 30, 200)
CARO_BOARD_BG_COLOR = (50, 50, 50)
CARO_GRID_LINE_COLOR = (100, 100, 100)
CARO_X_COLOR = (255, 100, 100)
CARO_O_COLOR = (100, 100, 255)
CARO_WIN_LINE_COLOR = (255, 255, 0)
CARO_WIN_LINE_THICKNESS = 5
CARO_MARK_THICKNESS = 4
DEFAULT_CARO_AI = 'minimax'
CARO_MINIMAX_DEPTH = 2
CARO_BEAM_WIDTH = 3
CARO_BEAM_DEPTH = 2
CARO_QL_LEARNING_RATE = 0.1
CARO_QL_DISCOUNT_FACTOR = 0.9
CARO_QL_EXPLORATION_RATE = 0.1
CARO_REWARD_WIN = 100
CARO_REWARD_LOSS = -100
CARO_REWARD_DRAW = 0
CARO_REWARD_MOVE = -1

# Hằng số cho game con chuột và phô mai
MAZE_CELL_SIZE = 40
DEFAULT_MAZE_LAYOUT = [
    [0, 1, 0, 0, 0],
    [0, 1, 0, 1, 0],
    [0, 0, 0, 1, 0],
    [0, 1, 1, 1, 0],
    [0, 0, 0, 0, 0]
]
MAZE_INITIAL_CHEESE_POSITIONS = frozenset([(0, 4), (4, 4)])
MAZE_START_POS = (0, 0)
MAZE_TARGET_CHEESE_COUNT = 2
MOUSE_IMAGE_PATH = get_asset_path("images/character/mouse.png")
CHEESE_IMAGE_PATH = get_asset_path("images/character/cheese.png")
MAZE_QL_LEARNING_RATE = 0.1
MAZE_QL_DISCOUNT_FACTOR = 0.95
MAZE_QL_EPSILON_START = 1.0
MAZE_QL_EPSILON_END = 0.05
MAZE_QL_EPSILON_DECAY_RATE = 0.9995
MAZE_QL_INITIAL_Q_VALUE = 0.0
MAZE_REWARD_STEP = -0.1
MAZE_REWARD_WALL = -2.0
MAZE_REWARD_CHEESE = 20.0
MAZE_REWARD_WIN_ALL_CHEESE = 60.0
MAZE_MAX_STEPS_FACTOR = 1.2
MAZE_GAME_WIN_REWARD_MAIN = 20
MAZE_PATH_COLOR = (0, 200, 0)
MAZE_FONT_SIZE = 24
MAZE_TRAINING_COST_PER_EPISODE = 1
MAZE_TRAINING_PROMPT = "Nhập số lượt huấn luyện cho AI (1 lượt = 1 tiền):"
MAZE_INSUFFICIENT_MONEY_MESSAGE = "Không đủ tiền cho số lượt huấn luyện này!"
MAZE_INVALID_EPISODES_MESSAGE = "Vui lòng nhập một số nguyên dương."
MAZE_RETRY_TRAINING_MESSAGE = "AI không ăn đủ phô mai. Nhập thêm lượt huấn luyện:"
MAZE_MOUSE_MOVE_INTERVAL = 0.2

# Bảng lựa chọn Minigame
MINIGAME_SELECTION_WINDOW_TITLE = "Chọn Minigame"
MINIGAME_SELECTION_PROMPT = "Chọn một Minigame để chơi:"
MINIGAME_SELECTION_WINDOW_WIDTH = 400
MINIGAME_SELECTION_WINDOW_HEIGHT = 300
MINIGAME_SELECTION_BUTTON_HEIGHT = 50
MINIGAME_SELECTION_BUTTON_MARGIN = 10
MINIGAME_DISPLAY_NAMES = {
    "EightPuzzleGame": "8-Puzzle",
    "SnakeGame": "Rắn Săn Mồi",
    "MazeGame": "Chuột và Phô Mát",
    "CaroGame": "Cờ Caro",
    "SudokuGame": "Sudoku 4x4"
}

# Hằng số cho giao diện người dùng
CONFIRM_BUTTON_WIDTH = 100
CONFIRM_BUTTON_HEIGHT = 40
CONFIRM_BUTTON_TEXT = "Xác nhận"

# Hằng số cho thuật toán tìm đường
BEAM_SEARCH_WIDTH_DEFAULT = 3
DEFAULT_PATHFINDING_ALGORITHM_NAME = "A* (A-star)"
BACKTRACKING_MAX_DEPTH_FACTOR = 1.5
BACKTRACKING_MAX_CALLS_FACTOR = 5

# Hằng số cho các thông báo
STATUS_PANEL_X = 10
STATUS_PANEL_Y_START = 10
STATUS_PANEL_WIDTH = 250  
STATUS_PANEL_HEIGHT = 40  
STATUS_PANEL_SPACING = 5   
STATUS_TEXT_PADDING = 8 


# Hằng số cho font chữ
DEFAULT_FONT_PATH = get_asset_path("fonts/Roboto-Regular.ttf")
DEFAULT_FONT_SIZE_SMALL = 24
DEFAULT_FONT_SIZE_MEDIUM = 30
DEFAULT_FONT_SIZE_LARGE = 36