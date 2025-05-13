
import pygame
import os
import src.config as config

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, speed=config.PLAYER_DEFAULT_SPEED):
        super().__init__()
        self.load_images(config.PLAYER_IMAGE_BASE_PATH)
        self.image = self.images['idle']
        self.rect = self.image.get_rect()
        self.x = float(x)
        self.y = float(y)
        self.rect.topleft = (round(self.x), round(self.y))
        self.speed = speed
        self.actions = []
        self.target_path_nodes = []
        self.action_index = 0
        self.move_progress = 0
        self.current_dx_normalized = 0
        self.current_dy_normalized = 0
        self.money = config.INITIAL_PLAYER_MONEY
        self.facing_direction = 'down'
        self.animation_timer = 0
        self.animation_speed = 0.2

        
        self.items_collected_count = 0

    def load_images(self, image_path_base_dir):
       
        self.images = {}
        try:
            self.images['down'] = pygame.image.load(os.path.join(image_path_base_dir, "s.png")).convert_alpha()
            self.images['up'] = pygame.image.load(os.path.join(image_path_base_dir, "w.png")).convert_alpha()
            self.images['left_1'] = pygame.image.load(os.path.join(image_path_base_dir, "a.png")).convert_alpha()
            self.images['left_2'] = pygame.image.load(os.path.join(image_path_base_dir, "a2.png")).convert_alpha()
            self.images['right_1'] = pygame.image.load(os.path.join(image_path_base_dir, "d.png")).convert_alpha()
            self.images['right_2'] = pygame.image.load(os.path.join(image_path_base_dir, "d2.png")).convert_alpha()
            self.images['idle'] = pygame.image.load(os.path.join(image_path_base_dir, "player.png")).convert_alpha()
        except pygame.error as e:
            raise Exception(f"Lỗi Pygame khi tải ảnh người chơi từ '{image_path_base_dir}': {e}")
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Lỗi: Không tìm thấy file ảnh người chơi trong '{image_path_base_dir}': {e}")


    def set_actions(self, actions, path_nodes=None):
       
        self.actions = actions
        self.target_path_nodes = path_nodes if path_nodes else []
        self.action_index = 0
        self.move_progress = 0
        self.current_dx_normalized = 0
        self.current_dy_normalized = 0
        if not actions:
            self.target_path_nodes = []

    def add_money(self, amount):
        
        if amount < 0:
            print("Cảnh báo: Không thể cộng số tiền âm.")
            return
        self.money += amount

    def spend_money(self, amount):
        
        if amount < 0:
            print("Cảnh báo: Không thể tiêu số tiền âm.")
            return False
        if self.money >= amount:
            self.money -= amount
            return True
        else:
            return False

  
    def collect_item(self, item_value):
        """
        Xử lý khi người chơi thu thập một món hàng/điểm.
        item_value: Giá trị tiền của món hàng/điểm đó.
        """
        self.add_money(item_value) 
        self.items_collected_count += 1 
        print(f"Người chơi đã thu thập món hàng thứ {self.items_collected_count}. Tổng tiền: {self.money}")


    def move(self, dx_pixel, dy_pixel, collidable_tiles):
       
        new_x = self.x + dx_pixel
        new_y = self.y + dy_pixel
        old_x, old_y = self.x, self.y
        temp_rect_x = self.rect.copy()
        temp_rect_x.x = round(new_x)
        collision_x = False
        for tile in collidable_tiles:
            if tile.is_collidable and temp_rect_x.colliderect(tile.rect):
                collision_x = True
                if dx_pixel > 0: new_x = tile.rect.left - self.rect.width
                elif dx_pixel < 0: new_x = tile.rect.right
                if self.actions: self.set_actions([], None)
                break
        self.x = new_x
        self.rect.x = round(self.x)
        temp_rect_y = self.rect.copy()
        temp_rect_y.y = round(new_y)
        collision_y = False
        for tile in collidable_tiles:
            if tile.is_collidable and temp_rect_y.colliderect(tile.rect):
                collision_y = True
                if dy_pixel > 0: new_y = tile.rect.top - self.rect.height
                elif dy_pixel < 0: new_y = tile.rect.bottom
                if self.actions: self.set_actions([], None)
                break
        self.y = new_y
        self.rect.y = round(self.y)
        return collision_x or collision_y

    def update(self, collidable_tiles, delta_time):
       
        self.animation_timer += delta_time
        final_anim_dx = 0
        final_anim_dy = 0
        is_currently_moving = False

        if self.actions and self.action_index < len(self.actions):
            if self.move_progress == 0: 
                action = self.actions[self.action_index]
                if action == 'W': self.current_dx_normalized, self.current_dy_normalized = 0, -1
                elif action == 'S': self.current_dx_normalized, self.current_dy_normalized = 0, 1
                elif action == 'A': self.current_dx_normalized, self.current_dy_normalized = -1, 0
                elif action == 'D': self.current_dx_normalized, self.current_dy_normalized = 1, 0
            
            final_anim_dx = self.current_dx_normalized
            final_anim_dy = self.current_dy_normalized
            is_currently_moving = (final_anim_dx != 0 or final_anim_dy != 0)
            move_x_pixel = self.current_dx_normalized * self.speed
            move_y_pixel = self.current_dy_normalized * self.speed
            self.move(move_x_pixel, move_y_pixel, collidable_tiles)

            if not self.actions: 
                self.move_progress = 0
                self.action_index = 0
                self.current_dx_normalized = 0
                self.current_dy_normalized = 0
                is_currently_moving = False
                final_anim_dx = 0
                final_anim_dy = 0
            else:
                self.move_progress += self.speed
                if self.move_progress >= config.TILE_SIZE:
                    if self.target_path_nodes and self.action_index < len(self.target_path_nodes) -1:
                        target_node_coords = self.target_path_nodes[self.action_index + 1]
                        self.x = float(target_node_coords[1] * config.TILE_SIZE)
                        self.y = float(target_node_coords[0] * config.TILE_SIZE)
                        self.rect.x = round(self.x)
                        self.rect.y = round(self.y)
                    self.move_progress = 0
                    self.action_index += 1
                    if self.action_index >= len(self.actions):
                        self.set_actions([], None)
                        is_currently_moving = False
                        final_anim_dx = 0
                        final_anim_dy = 0
        else: 
            keys = pygame.key.get_pressed()
            manual_dx_normalized, manual_dy_normalized = 0, 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]: manual_dx_normalized = -1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]: manual_dx_normalized = 1
            if keys[pygame.K_UP] or keys[pygame.K_w]: manual_dy_normalized = -1
            if keys[pygame.K_DOWN] or keys[pygame.K_s]: manual_dy_normalized = 1

            final_anim_dx = manual_dx_normalized
            final_anim_dy = manual_dy_normalized
            is_currently_moving = (final_anim_dx != 0 or final_anim_dy != 0)

            if is_currently_moving:
                move_x_pixel = manual_dx_normalized * self.speed
                move_y_pixel = manual_dy_normalized * self.speed
                self.move(move_x_pixel, move_y_pixel, collidable_tiles)
        
        if is_currently_moving:
            if final_anim_dx < 0: 
                self.image = self.images['left_1'] if self.animation_timer < self.animation_speed else self.images['left_2']
                self.facing_direction = 'left'
            elif final_anim_dx > 0: 
                self.image = self.images['right_1'] if self.animation_timer < self.animation_speed else self.images['right_2']
                self.facing_direction = 'right'
            elif final_anim_dy < 0: 
                self.image = self.images['up']
                self.facing_direction = 'up'
            elif final_anim_dy > 0: 
                self.image = self.images['down']
                self.facing_direction = 'down'
        else: 
            self.image = self.images['idle']

        if self.animation_timer >= self.animation_speed * 2:
            self.animation_timer = 0


    def draw(self, surface, camera):
      
        surface.blit(self.image, camera.apply(self))