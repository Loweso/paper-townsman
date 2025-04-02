import pygame
import random
import os
from settings import *
from math import atan2, degrees

class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos, groups, obstacle_sprites, player, bullet_sprites, enemyID):
        super().__init__(groups)

        # Load animation frames
        self.load_images("assets/enemy/")
        self.current_frame = 0
        self.animation_speed = 0.15
        self.image = self.frames[self.current_frame]  
        self.rect = self.image.get_rect(topleft=pos)

        # Define hitbox
        self.hitbox = pygame.Rect(0, 0, ENEMY_HITBOX_WIDTH, ENEMY_HITBOX_HEIGHT)
        self.hitbox.center = self.rect.center

        # AI attributes
        self.player = player
        self.bullet_sprites = bullet_sprites
        self.obstacle_sprites = obstacle_sprites
        self.speed = 1.5
        self.detection_radius = 200
        self.agro_radius = 300
        self.direction = pygame.math.Vector2()
        self.health = ENEMY_HEALTH
        self.enemyID = enemyID
        
        # AI state variables
        self.has_detected_player = False
        self.teleport_cooldown = 0
        self.teleport_delay = 4000  # ms between teleports
        self.last_teleport_time = 0
        self.path_update_time = 0
        self.path_update_delay = 500  # ms between path recalculations
        self.wandering_direction = pygame.math.Vector2()
        self.wandering_time = 0
        self.state = "wandering"  # or "chasing", "teleporting"
        
        # For line of sight check
        self.line_of_sight = False
        self.vision_angle = 90
        
        # For path prediction
        self.player_last_pos = pygame.math.Vector2(self.player.rect.center)
        self.player_velocity = pygame.math.Vector2()

    def load_images(self, folder):
        self.frames = []
        for filename in sorted(os.listdir(folder)):
            if filename.endswith((".png", ".gif")):
                img_path = os.path.join(folder, filename)
                img = pygame.image.load(img_path).convert_alpha()
                img = pygame.transform.scale(img, (ENEMY_SIZE, ENEMY_SIZE))
                self.frames.append(img)

        if not self.frames:
            raise ValueError(f"No valid images found in {folder}!")

    def animate(self):
        self.current_frame += self.animation_speed
        if self.current_frame >= len(self.frames):
            self.current_frame = 0
        self.image = self.frames[int(self.current_frame)]
        # Removed rotation code to keep enemy vertical

    def update_player_velocity(self):
        current_pos = pygame.math.Vector2(self.player.rect.center)
        self.player_velocity = current_pos - self.player_last_pos
        self.player_last_pos = current_pos

    def check_line_of_sight(self):
        """Check if player is within vision cone and not blocked by obstacles"""
        player_vec = pygame.math.Vector2(self.player.rect.center) - pygame.math.Vector2(self.rect.center)
        distance = player_vec.length()
        
        if distance > self.detection_radius:
            return False
            
        # Check if player is within vision angle
        direction_angle = degrees(atan2(-self.direction.y, self.direction.x)) if self.direction.length() > 0 else 0
        player_angle = degrees(atan2(-player_vec.y, player_vec.x))
        angle_diff = (player_angle - direction_angle + 180) % 360 - 180
        
        if abs(angle_diff) > self.vision_angle/2 and self.direction.length() > 0:
            return False
            
        # Raycast to check for obstacles
        step = 10
        steps = int(distance / step)
        for i in range(1, steps):
            test_point = self.rect.center + player_vec.normalize() * i * step
            for sprite in self.obstacle_sprites:
                if sprite.hitbox.collidepoint(test_point):
                    return False
                    
        return True

    def decide_state(self):
        current_time = pygame.time.get_ticks()
        distance_to_player = pygame.math.Vector2(self.player.rect.center).distance_to(self.rect.center)
        
        # Update has_detected_player if player is within agro radius
        if distance_to_player <= self.agro_radius or self.has_detected_player:
            self.has_detected_player = True
            self.state = "chasing"
            
            # Chance to teleport when chasing
            if (current_time - self.last_teleport_time > self.teleport_delay and 
                random.random() < 0.02 and distance_to_player > 100):
                self.attempt_teleport()
        elif self.state == "chasing" and distance_to_player > self.agro_radius * 1.5:
            # Lost player, return to wandering
            self.state = "wandering"
            self.has_detected_player = False
        elif self.state == "wandering":
            # Random direction changes while wandering
            if current_time - self.wandering_time > 2000:
                self.wandering_direction = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
                if self.wandering_direction.length() > 0:
                    self.wandering_direction = self.wandering_direction.normalize()
                self.wandering_time = current_time

    def attempt_teleport(self):
        """Teleport to a random position near the player, avoiding obstacles"""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_teleport_time < self.teleport_delay:
            return
            
        # Try to find a valid position near player
        for _ in range(10):  # Try 10 random positions
            offset = pygame.math.Vector2(random.randint(-150, 150), random.randint(-150, 150))
            new_pos = self.player.rect.center + offset
            
            # Create temp rect to check collisions
            temp_rect = self.rect.copy()
            temp_rect.center = new_pos
            temp_hitbox = self.hitbox.copy()
            temp_hitbox.center = new_pos
            
            # Check if position is valid (not in obstacle)
            valid_position = True
            for sprite in self.obstacle_sprites:
                if temp_hitbox.colliderect(sprite.hitbox):
                    valid_position = False
                    break
                    
            if valid_position:
                self.rect.center = new_pos
                self.hitbox.center = new_pos
                self.last_teleport_time = current_time
                self.state = "teleporting"
                return

    def move(self):
        current_time = pygame.time.get_ticks()
        
        if self.state == "chasing":
            # Predict player movement based on velocity
            predicted_pos = pygame.math.Vector2(self.player.rect.center) + self.player_velocity * 0.5
            
            # Removed randomness from movement to make it smoother
            self.direction = (predicted_pos - pygame.math.Vector2(self.rect.center)).normalize()
                
        elif self.state == "wandering":
            self.direction = self.wandering_direction
            
        # Move only if not recently teleported
        if current_time - self.last_teleport_time > 300:
            self.hitbox.x += self.direction.x * self.speed
            self.collision('horizontal')
            self.hitbox.y += self.direction.y * self.speed
            self.collision('vertical')
            self.rect.center = self.hitbox.center

    def collision(self, direction):
        for sprite in self.obstacle_sprites:
            if sprite.hitbox.colliderect(self.hitbox):
                if direction == 'horizontal':
                    if self.direction.x > 0:
                        self.hitbox.right = sprite.hitbox.left
                    elif self.direction.x < 0:
                        self.hitbox.left = sprite.hitbox.right
                elif direction == 'vertical':
                    if self.direction.y > 0:
                        self.hitbox.bottom = sprite.hitbox.top
                    elif self.direction.y < 0:
                        self.hitbox.top = sprite.hitbox.bottom

                # Change direction when hitting obstacle
                if self.state == "wandering":
                    self.wandering_direction = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
                    if self.wandering_direction.length() > 0:
                        self.wandering_direction = self.wandering_direction.normalize()
                    self.wandering_time = pygame.time.get_ticks()

    def check_bullet_collision(self):
        for bullet in self.bullet_sprites:
            if self.hitbox.colliderect(bullet.rect):
                self.health -= BULLET_DAMAGE 
                bullet.kill()

                if self.health <= 0:
                    if hasattr(self.player, "level"):
                        self.player.level.register_enemy_death(self.enemyID)
                    self.kill()

    def update(self):
        self.update_player_velocity()
        self.line_of_sight = self.check_line_of_sight()
        self.decide_state()
        self.move()
        self.animate()
        self.check_bullet_collision()