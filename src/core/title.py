
import pygame
import src.config as config

class Tile(pygame.sprite.Sprite):
    def __init__(self, x, y, size, is_collidable=True):
        super().__init__()
        self.image = pygame.Surface([size, size], pygame.SRCALPHA)
        
        self.image.set_alpha(0) 
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.is_collidable = is_collidable

    def draw(self, surface, camera): 
        """Vẽ tile (thường là đường viền debug) nếu nó là vật cản và trong tầm nhìn camera."""
        if self.is_collidable and camera.camera_rect.colliderect(self.rect):
             debug_rect_on_screen = camera.apply_rect(self.rect)
             pygame.draw.rect(surface, config.RED, debug_rect_on_screen, 1)