# src/core/point_manager.py
import pygame
import random
import src.config as config # Import config

class PointManager:
    def __init__(self, entity_data): # tile_size, POINT_IMAGE_PATH, POINT_ID được lấy từ config
        self.tile_size = config.TILE_SIZE
        self.spawn_points_pixels = []
        self._find_spawn_points(entity_data) # entity_data vẫn cần được truyền vào

        self.image = None
        try:
            # Sử dụng đường dẫn ảnh từ config
            self.image = pygame.image.load(config.POINT_IMAGE_PATH).convert_alpha()
        except pygame.error as e:
            print(f"Lỗi Pygame khi tải ảnh điểm '{config.POINT_IMAGE_PATH}': {e}")
        except FileNotFoundError:
             print(f"Cảnh báo: Không tìm thấy file ảnh điểm '{config.POINT_IMAGE_PATH}'.")

        self.current_point_rect = None
        self.current_point_center = None # Tọa độ pixel của tâm điểm hiện tại
        self.is_visible = False
        self.collected_point_for_puzzle_center = None 

        if not self.spawn_points_pixels:
            print(f"Cảnh báo: Không tìm thấy vị trí nào có ID '{config.POINT_ENTITY_ID}' cho điểm thu thập.")
        else:
             self.spawn_new_point()

    def _find_spawn_points(self, entity_data):
        """Tìm tất cả các vị trí có thể spawn điểm dựa trên entity_data."""
        for r, row in enumerate(entity_data):
            for c, entity_value in enumerate(row):
                if entity_value.strip() == config.POINT_ENTITY_ID: # Sử dụng POINT_ID từ config
                    # Tính tọa độ pixel của tâm ô
                    center_x = c * self.tile_size + self.tile_size // 2
                    center_y = r * self.tile_size + self.tile_size // 2
                    self.spawn_points_pixels.append((center_x, center_y))

    def spawn_new_point(self, exclude_center=None):
        """Spawn một điểm mới tại một vị trí ngẫu nhiên, có thể loại trừ một vị trí."""
        if not self.spawn_points_pixels:
            self.is_visible = False
            self.current_point_rect = None
            self.current_point_center = None
            return

        possible_spawns = self.spawn_points_pixels
        if exclude_center and len(self.spawn_points_pixels) > 1:
            # Loại trừ vị trí vừa thu thập để điểm mới không xuất hiện ngay tại đó
            possible_spawns = [p for p in self.spawn_points_pixels if p != exclude_center]
            if not possible_spawns: # Nếu loại trừ làm rỗng danh sách (chỉ có 1 điểm spawn)
                possible_spawns = self.spawn_points_pixels # Thì vẫn dùng danh sách cũ

        self.current_point_center = random.choice(possible_spawns)

        if self.image:
            img_width, img_height = self.image.get_size()
            rect_x = self.current_point_center[0] - img_width // 2
            rect_y = self.current_point_center[1] - img_height // 2
            self.current_point_rect = pygame.Rect(rect_x, rect_y, img_width, img_height)
            self.is_visible = True
        else: # Không có ảnh thì không hiển thị
            self.is_visible = False
            self.current_point_rect = None # Đảm bảo rect cũng là None
        
        self.collected_point_for_puzzle_center = None # Reset khi spawn điểm mới

    def can_attempt_collect(self, player_center, f_key_pressed):
        """
        Kiểm tra xem người chơi có thể thử thu thập điểm không (khi nhấn F).
        Khoảng cách này có thể lớn hơn khoảng cách kích hoạt puzzle tự động.
        """
        if not self.is_visible or not self.current_point_center or not f_key_pressed:
            return False, 0

        dist_sq = (player_center[0] - self.current_point_center[0])**2 + \
                  (player_center[1] - self.current_point_center[1])**2

        if dist_sq <= config.COLLECT_DISTANCE_SQ: # Sử dụng hằng số từ config
            self.collected_point_for_puzzle_center = self.current_point_center
            return True, config.POINT_COLLECT_VALUE # Sử dụng hằng số từ config
        return False, 0

    def is_player_at_point_for_auto_puzzle(self, player_center):
        """
        Kiểm tra xem người chơi có ở đủ gần điểm để tự động kích hoạt puzzle không.
        """
        if not self.is_visible or not self.current_point_center:
            return False, 0

        dist_sq = (player_center[0] - self.current_point_center[0])**2 + \
                  (player_center[1] - self.current_point_center[1])**2

        if dist_sq <= config.PLAYER_AT_POINT_DISTANCE_SQ: # Sử dụng hằng số từ config
            self.collected_point_for_puzzle_center = self.current_point_center
            return True, config.POINT_COLLECT_VALUE # Sử dụng hằng số từ config
        return False, 0

    def finalize_collection(self):
        """
        Hoàn tất việc thu thập điểm SAU KHI giải đố thành công.
        """
        if self.collected_point_for_puzzle_center:
            excluded_center = self.collected_point_for_puzzle_center
            self.is_visible = False
            self.current_point_rect = None
            self.current_point_center = None
            self.collected_point_for_puzzle_center = None 
            self.spawn_new_point(exclude_center=excluded_center)
            return True
        return False

    def draw(self, surface, camera):
        if self.is_visible and self.current_point_rect and self.image:
            screen_pos_rect = camera.apply_rect(self.current_point_rect)
            surface.blit(self.image, screen_pos_rect)