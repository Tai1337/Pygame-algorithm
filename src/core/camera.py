
import pygame
import src.config as config

class Camera:
    def __init__(self, world_width, world_height):
        self.camera_rect = pygame.Rect(0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
        self.world_width = world_width
        self.world_height = world_height

    def apply(self, entity):
        """Di chuyển đối tượng theo camera để vẽ lên màn hình."""
        return entity.rect.move(-self.camera_rect.x, -self.camera_rect.y)

    def apply_rect(self, rect):
        """Di chuyển một hình chữ nhật theo camera."""
        return rect.move(-self.camera_rect.x, -self.camera_rect.y)

    def update(self, target_entity):
        """Cập nhật vị trí camera để theo dõi đối tượng target_entity."""
        x = -target_entity.rect.centerx + config.SCREEN_WIDTH // 2
        y = -target_entity.rect.centery + config.SCREEN_HEIGHT // 2

        x = min(0, x)  
        y = min(0, y)  

        if self.world_width >= config.SCREEN_WIDTH:
            x = max(-(self.world_width - config.SCREEN_WIDTH), x) 
        else:
            x = 0 

        if self.world_height >= config.SCREEN_HEIGHT:
            y = max(-(self.world_height - config.SCREEN_HEIGHT), y) 
        else:
            y = 0 

        self.camera_rect.topleft = (round(-x), round(-y))