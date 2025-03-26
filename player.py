import pygame
import os
from settings import *
from bullet import Bullet
import math

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, obstacle_sprites, bullet_sprites, enemy_sprites):
        super().__init__(groups)
        
        self.pos = pygame.math.Vector2(pos)

        # Animations dictionary
        self.animations = {
            'up': [],
            'down': [],
            'left': [],
            'right': [],
            'idle': []
        }

        # Load animation frames
        self.load_animations()

        # Start with down animation
        self.status = 'down'
        self.frame_index = 0
        self.animation_speed = 0.15
        self.image = self.animations[self.status][self.frame_index]
        self.rect = self.image.get_rect(topleft = self.pos)
        self.hitbox = self.rect.inflate(0, -26)
        
        self.enemy_sprites = enemy_sprites
    
        self.health = 100

        self.direction = pygame.math.Vector2()
        self.speed = 5

        self.obstacle_sprites = obstacle_sprites
        self.bullet_sprites = bullet_sprites
        self.visible_sprites = groups[0]
        
        self.shoot = False
        self.shoot_cooldown = 0
        self.gun_barrel_offset = pygame.math.Vector2(GUN_OFFSET_X,GUN_OFFSET_Y)
        self.last_direction = 'down'  # for idle animation
        
        self.load_health_assets()

    def load_animations(self):
        # Example folder structure: assets/player/down/0.png, 1.png, etc.
        directions = ['up', 'down', 'left', 'right']
        for direction in directions:
            path = f'assets/player/{direction}'
            frames = []
            for filename in sorted(os.listdir(path)):
                frame = pygame.image.load(os.path.join(path, filename)).convert_alpha()
                frames.append(frame)
            self.animations[direction] = frames

        # Optionally load idle frame
        idle_frame = pygame.image.load('assets/player/idle.png').convert_alpha()
        self.animations['idle'] = [idle_frame]

    def load_health_assets(self):
        """Load heart images for the health bar."""
        self.red_heart = pygame.image.load('assets/redheart.png').convert_alpha()
        self.heart_size = (20, 20)  
        self.red_heart = pygame.transform.scale(self.red_heart, self.heart_size)
        
    def draw_health(self, surface):
        """Draws only the number of red hearts representing the player's remaining health."""
        heart_x = 20  # X position (left corner)
        heart_y = 20  # Y position (top)
        
        total_hearts = self.health // 20  # Each heart represents 20 health

        for i in range(total_hearts):
            surface.blit(self.red_heart, (heart_x + i * (self.heart_size[0] + 5), heart_y))  # 5px spacing between hearts


    def input(self):
        self.direction.x = 0
        self.direction.y = 0
        keys = pygame.key.get_pressed()
    

        if keys[pygame.K_UP]:
            self.direction.y = -self.speed
            self.status = 'up'
        elif keys[pygame.K_DOWN]:
            self.direction.y = self.speed
            self.status = 'down'
        else:
            self.direction.y = 0

        if keys[pygame.K_LEFT]:
            self.direction.x = -self.speed
            self.status = 'left'
        if keys[pygame.K_RIGHT]:
            self.direction.x = self.speed
        
        if self.direction.x != 0 and self.direction.y != 0:
            self.direction.x /= math.sqrt(2)
            self.direction.y /= math.sqrt(2)
            
        if pygame.mouse.get_pressed() == (1,0,0):
            self.shoot = True
            self.is_shooting()
            self.status = 'right'
        else:
            self.shoot = False

  
    def check_enemy_collision(self):
        """Check if enemy is hit by a bullet"""
        for enemy in self.enemy_sprites:
            if self.hitbox.colliderect(enemy.hitbox):
                self.health -= 20  # Reduce enemy health
                enemy.kill()  # Remove the bullet

                if self.health <= 0:
                    self.kill()
                    exit()# Destroy the enemy if health is zero
        # Store last direction when moving
        if self.direction.x != 0 or self.direction.y != 0:
            self.last_direction = self.status

    def animate(self):
        if self.direction.magnitude() != 0:
            # Moving
            self.frame_index += self.animation_speed
            if self.frame_index >= len(self.animations[self.status]):
                self.frame_index = 0
            self.image = self.animations[self.status][int(self.frame_index)]
        else:
            # Idle
            self.image = self.animations[self.last_direction][0]            

    def collision (self, direction):
        if direction == 'horizontal':
            for sprite in self.obstacle_sprites:
                if sprite.hitbox.colliderect(self.hitbox):
                    if self.direction.x > 0: # moving right
                        self.hitbox.right = sprite.hitbox.left
                    if self.direction.x < 0: # moving left
                        self.hitbox.left = sprite.hitbox.right

        if direction == 'vertical':
            for sprite in self.obstacle_sprites:
                if sprite.hitbox.colliderect(self.hitbox):
                    if self.direction.y > 0: # moving down
                        self.hitbox.bottom = sprite.hitbox.top
                    if self.direction.y < 0: # moving up
                        self.hitbox.top = sprite.hitbox.bottom
    
    def is_shooting(self):
        self.mouse_coords = pygame.mouse.get_pos()
        self.x_change_mouse_player = self.mouse_coords[0] - WIDTH // 2
        self.y_change_mouse_player = self.mouse_coords[1] - HEIGHT // 2
        self.angle = math.degrees(math.atan2(self.y_change_mouse_player, self.x_change_mouse_player))
        
        if self.shoot_cooldown == 0:
            self.shoot_cooldown = SHOOT_COOLDOWN
            spawn_bullet_pos = self.pos + self.gun_barrel_offset.rotate(self.angle)
            self.bullet = Bullet(spawn_bullet_pos[0], spawn_bullet_pos[1], self.angle, self.obstacle_sprites)
            self.bullet_sprites.add(self.bullet)
            self.visible_sprites.add(self.bullet)

    def move(self, speed, x_min, x_max, y_min, y_max):
        if self.direction.magnitude() != 0:
            self.direction = self.direction.normalize()

        self.hitbox.x += self.direction.x * speed
        self.collision('horizontal')

        self.hitbox.y += self.direction.y * speed
        self.collision('vertical')

        self.hitbox.x = max(x_min, min(self.hitbox.x, x_max - self.rect.width))
        self.hitbox.y = max(y_min, min(self.hitbox.y, y_max - self.rect.height))

        self.rect.center = self.hitbox.center
        
        self.pos = pygame.math.Vector2(self.hitbox.center)
    def update(self, *args, **kwargs):
        dialogue_mode = kwargs.get('dialogue_mode', False)
        x_min = kwargs.get('x_min', 0)
        x_max = kwargs.get('x_max', 1000)  # Default values if not provided
        y_min = kwargs.get('y_min', 0)
        y_max = kwargs.get('y_max', 1000)

        if not dialogue_mode:
            self.input()
            self.move(self.speed, x_min, x_max, y_min, y_max)
        else:
            self.direction.x = 0
            self.direction.y = 0

        self.check_enemy_collision()
     
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        self.animate()
        self.draw_health(pygame.display.get_surface()) 
