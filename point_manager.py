# point_manager.py
import pygame
import random

POINT_ID = '214'
POINT_IMAGE_PATH = "poin.png"
COLLECT_DISTANCE_SQ = (32 * 1.5)**2 # Giữ nguyên, là khoảng cách để *thử* nhặt
POINT_COLLECT_VALUE = 25

class PointManager:
    def __init__(self, entity_data, tile_size):
        self.tile_size = tile_size
        self.spawn_points_pixels = []
        self._find_spawn_points(entity_data)

        self.image = None
        try:
            self.image = pygame.image.load(POINT_IMAGE_PATH).convert_alpha()
        except pygame.error as e:
            print(f"Lỗi Pygame khi tải ảnh điểm '{POINT_IMAGE_PATH}': {e}")
        except FileNotFoundError:
             print(f"Cảnh báo: Không tìm thấy file ảnh điểm '{POINT_IMAGE_PATH}'.")

        self.current_point_rect = None
        self.current_point_center = None
        self.is_visible = False
        self.collected_point_for_puzzle_center = None # Lưu vị trí điểm đang chờ giải đố

        if not self.spawn_points_pixels:
            print(f"Cảnh báo: Không tìm thấy vị trí nào có ID '{POINT_ID}'.")
        else:
             self.spawn_new_point()

    def _find_spawn_points(self, entity_data):
        for r, row in enumerate(entity_data):
            for c, entity_value in enumerate(row):
                if entity_value.strip() == POINT_ID:
                    center_x = c * self.tile_size + self.tile_size // 2
                    center_y = r * self.tile_size + self.tile_size // 2
                    self.spawn_points_pixels.append((center_x, center_y))

    def spawn_new_point(self, exclude_center=None):
        if not self.spawn_points_pixels:
            self.is_visible = False
            self.current_point_rect = None
            self.current_point_center = None
            return

        possible_spawns = self.spawn_points_pixels
        if exclude_center and len(self.spawn_points_pixels) > 1:
            possible_spawns = [p for p in self.spawn_points_pixels if p != exclude_center]
            if not possible_spawns:
                possible_spawns = self.spawn_points_pixels

        self.current_point_center = random.choice(possible_spawns)

        if self.image:
            img_width, img_height = self.image.get_size()
            rect_x = self.current_point_center[0] - img_width // 2
            rect_y = self.current_point_center[1] - img_height // 2
            self.current_point_rect = pygame.Rect(rect_x, rect_y, img_width, img_height)
            self.is_visible = True
        else:
            self.is_visible = False
        self.collected_point_for_puzzle_center = None # Reset khi spawn điểm mới

    def can_attempt_collect(self, player_center, f_key_pressed):
        """
        Kiểm tra xem người chơi có ở đủ gần và nhấn F để *thử* thu thập không.
        Returns:
            tuple: (bool: True nếu có thể thử, int: giá trị điểm nếu thử được)
        """
        if not self.is_visible or not self.current_point_center or not f_key_pressed:
            return False, 0

        dist_sq = (player_center[0] - self.current_point_center[0])**2 + \
                  (player_center[1] - self.current_point_center[1])**2

        if dist_sq <= COLLECT_DISTANCE_SQ:
            # Đánh dấu điểm này đang chờ giải đố, nhưng chưa ẩn nó
            self.collected_point_for_puzzle_center = self.current_point_center
            return True, POINT_COLLECT_VALUE
        return False, 0

    def finalize_collection(self):
        """
        Hoàn tất việc thu thập điểm SAU KHI giải đố thành công.
        Ẩn điểm hiện tại và spawn điểm mới.
        """
        if self.collected_point_for_puzzle_center:
            # print(f"Điểm tại {self.collected_point_for_puzzle_center} đã được thu thập (sau puzzle)!")
            excluded_center = self.collected_point_for_puzzle_center
            self.is_visible = False
            self.current_point_rect = None
            self.current_point_center = None
            self.collected_point_for_puzzle_center = None # Quan trọng: reset lại
            self.spawn_new_point(exclude_center=excluded_center)
            return True
        return False


    def draw(self, surface, camera):
        if self.is_visible and self.current_point_rect and self.image:
            screen_pos_rect = camera.apply_rect(self.current_point_rect)
            surface.blit(self.image, screen_pos_rect)