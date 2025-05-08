# player.py

import pygame

PLAYER_DEFAULT_SPEED = 4
TILE_SIZE = 32
INITIAL_PLAYER_MONEY = 100
CHARACTER_FOLDER = "character"  # Thư mục chứa ảnh nhân vật (nếu bạn dùng)

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, image_path_base, speed=PLAYER_DEFAULT_SPEED):
        super().__init__()
        self.load_images(image_path_base)
        self.image = self.images['idle']  # Ảnh ban đầu
        self.rect = self.image.get_rect()
        self.x = float(x)
        self.y = float(y)
        self.rect.topleft = (round(self.x), round(self.y))
        self.speed = speed
        self.actions = []
        self.action_index = 0
        self.move_progress = 0
        self.current_dx = 0
        self.current_dy = 0
        self.money = INITIAL_PLAYER_MONEY
        self.facing_direction = 'down'  # Thêm hướng mặt (left, right, up, down)
        self.animation_timer = 0
        self.animation_speed = 0.2  # Tốc độ chuyển ảnh (giây)

    def load_images(self, image_path_base):
        """Tải tất cả các ảnh của người chơi."""

        self.images = {}
        try:
            self.images['down'] = pygame.image.load(
                f"{image_path_base}/s.png").convert_alpha()
            self.images['up'] = pygame.image.load(
                f"{image_path_base}/w.png").convert_alpha()
            self.images['left_1'] = pygame.image.load(
                f"{image_path_base}/a.png").convert_alpha()
            self.images['left_2'] = pygame.image.load(
                f"{image_path_base}/a2.png").convert_alpha()
            self.images['right_1'] = pygame.image.load(
                f"{image_path_base}/d.png").convert_alpha()
            self.images['right_2'] = pygame.image.load(
                f"{image_path_base}/d2.png").convert_alpha()
            self.images['idle'] = pygame.image.load(
                f"{image_path_base}/player.png").convert_alpha()
        except pygame.error as e:
            raise Exception(f"Lỗi Pygame khi tải ảnh người chơi: {e}")
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Lỗi: Không tìm thấy file ảnh người chơi: {e}")

    def set_actions(self, actions):
        self.actions = actions
        self.action_index = 0
        self.move_progress = 0
        self.current_dx = 0
        self.current_dy = 0
        # print(f"Debug: Đã thiết lập thao tác với {len(actions)} bước: {actions}")

    def add_money(self, amount):
        if amount < 0:
            print("Cảnh báo: Không thể cộng số tiền âm.")
            return
        self.money += amount
        # print(f"Debug: Người chơi nhận được {amount}. Tổng tiền: {self.money}")

    def spend_money(self, amount):
        if amount < 0:
            print("Cảnh báo: Không thể tiêu số tiền âm.")
            return False
        if self.money >= amount:
            self.money -= amount
            # print(f"Debug: Người chơi đã tiêu {amount}. Còn lại: {self.money}")
            return True
        else:
            print(f"Debug: Người chơi không đủ tiền. Cần {amount}, có {self.money}")
            return False

    def move(self, dx, dy, collidable_tiles):
        new_x = self.x + dx
        new_y = self.y + dy

        temp_rect_x = self.rect.copy()
        temp_rect_x.x = round(new_x)
        collision_x = False
        for tile in collidable_tiles:
            if temp_rect_x.colliderect(tile.rect):
                collision_x = True
                if dx > 0:
                    new_x = tile.rect.left - self.rect.width
                elif dx < 0:
                    new_x = tile.rect.right
                break
        self.x = new_x
        self.rect.x = round(self.x)

        temp_rect_y = self.rect.copy()
        temp_rect_y.y = round(new_y)
        collision_y = False
        for tile in collidable_tiles:
            if temp_rect_y.colliderect(tile.rect):
                collision_y = True
                if dy > 0:
                    new_y = tile.rect.top - self.rect.height
                elif dy < 0:
                    new_y = tile.rect.bottom
                break
        self.y = new_y
        self.rect.y = round(self.y)

    def update(self, collidable_tiles, delta_time):
        self.animation_timer += delta_time

        if self.actions and self.action_index < len(self.actions):
            if self.move_progress == 0:
                action = self.actions[self.action_index]
                if action == 'W':
                    self.current_dx, self.current_dy = 0, -1
                    self.facing_direction = 'up'
                    self.image = self.images['up']
                elif action == 'S':
                    self.current_dx, self.current_dy = 0, 1
                    self.facing_direction = 'down'
                    self.image = self.images['down']
                elif action == 'A':
                    self.current_dx, self.current_dy = -1, 0
                    self.facing_direction = 'left'
                elif action == 'D':
                    self.current_dx, self.current_dy = 1, 0
                    self.facing_direction = 'right'

            move_x = self.current_dx * self.speed
            move_y = self.current_dy * self.speed
            self.move(move_x, move_y, collidable_tiles)
            self.move_progress += self.speed

            if self.move_progress >= TILE_SIZE:
                self.move_progress = 0
                self.action_index += 1
                if self.action_index >= len(self.actions):
                    self.actions = []
                    self.action_index = 0
                    self.current_dx = 0
                    self.current_dy = 0
        else:
            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                dx = -1
                self.facing_direction = 'left'
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dx = 1
                self.facing_direction = 'right'
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                dy = -1
                self.facing_direction = 'up'
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                dy = 1
                self.facing_direction = 'down'
            move_x = dx * self.speed
            move_y = dy * self.speed
            if move_x != 0 or move_y != 0:
                self.move(move_x, move_y, collidable_tiles)
            else:
                self.image = self.images['idle'] # Nếu không di chuyển, hiển thị ảnh idle

        # Cập nhật ảnh dựa trên hướng và thời gian
        if self.facing_direction == 'left':
            if self.animation_timer < self.animation_speed:
                self.image = self.images['left_1']
            else:
                self.image = self.images['left_2']
        elif self.facing_direction == 'right':
            if self.animation_timer < self.animation_speed:
                self.image = self.images['right_1']
            else:
                self.image = self.images['right_2']
        elif self.facing_direction == 'up':
            self.image = self.images['up']
        elif self.facing_direction == 'down':
            self.image = self.images['down']

        if self.animation_timer >= self.animation_speed * 2:
            self.animation_timer = 0

    def draw(self, surface, camera):
        surface.blit(self.image, camera.apply(self))