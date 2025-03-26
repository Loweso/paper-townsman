import pygame
import os
from settings import *

class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos, groups, obstacle_sprites, player, bullet_sprites, enemyID):
        super().__init__(groups)

        # Load animation frames
        self.load_images("assets/enemy/")
        self.current_frame = 0
        self.animation_speed = 0.15  # Adjust speed of animation
        self.image = self.frames[self.current_frame]  
        self.rect = self.image.get_rect(topleft=pos)

        # Define hitbox size (smaller than actual image)
        self.hitbox = pygame.Rect(0, 0, ENEMY_HITBOX_WIDTH, ENEMY_HITBOX_HEIGHT)
        self.hitbox.center = self.rect.center  # Align hitbox to sprite center

        self.player = player
        self.bullet_sprites = bullet_sprites
        self.obstacle_sprites = obstacle_sprites
        self.speed = 2
        self.detection_radius = 200  
        self.direction = pygame.math.Vector2()
        self.health = ENEMY_HEALTH

        self.enemyID = enemyID

    def load_images(self, folder):
        self.frames = []
        for filename in sorted(os.listdir(folder)):  # Ensure correct frame order
            if filename.endswith(".png") or filename.endswith(".gif"):  # Add more extensions if needed
                img_path = os.path.join(folder, filename)
                img = pygame.image.load(img_path).convert_alpha()
                img = pygame.transform.scale(img, (ENEMY_SIZE, ENEMY_SIZE))  # Scale to tile size
                self.frames.append(img)

        if not self.frames:
            raise ValueError(f"No valid images found in {folder}!")

    def animate(self):
        self.current_frame += self.animation_speed
        if self.current_frame >= len(self.frames):
            self.current_frame = 0  # Loop animation

        self.image = self.frames[int(self.current_frame)]

    def move_towards_player(self):
        distance = pygame.math.Vector2(self.player.rect.center).distance_to(self.rect.center)
        
        if distance <= self.detection_radius:
            self.direction = pygame.math.Vector2(self.player.rect.center) - pygame.math.Vector2(self.rect.center)
            if self.direction.length() > 0:
                self.direction = self.direction.normalize()

            # Move only using self.direction
            self.hitbox.x += self.direction.x * self.speed
            self.collision('horizontal')
            self.hitbox.y += self.direction.y * self.speed
            self.collision('vertical')

            # Update sprite rect to match hitbox position
            self.rect.center = self.hitbox.center

    def check_bullet_collision(self):
        for bullet in self.bullet_sprites:
            if self.hitbox.colliderect(bullet.rect):
                self.health -= BULLET_DAMAGE 
                bullet.kill()

                if self.health <= 0:
                    if hasattr(self.player, "level"):  # Check if player has a reference to Level
                        self.player.level.register_enemy_death(self.enemyID)
                    self.kill()

    def collision(self, direction):
        for sprite in self.obstacle_sprites:
            if sprite.hitbox.colliderect(self.hitbox):
                if direction == 'horizontal':
                    if self.direction.x > 0:  # Moving right
                        self.hitbox.right = sprite.hitbox.left
                    elif self.direction.x < 0:  # Moving left
                        self.hitbox.left = sprite.hitbox.right
                elif direction == 'vertical':
                    if self.direction.y > 0:  # Moving down
                        self.hitbox.bottom = sprite.hitbox.top
                    elif self.direction.y < 0:  # Moving up
                        self.hitbox.top = sprite.hitbox.bottom

                # Stop movement when hitting an obstacle
                self.direction.x = 0
                self.direction.y = 0

    def update(self):
        self.animate()
        self.move_towards_player()
        self.check_bullet_collision()
