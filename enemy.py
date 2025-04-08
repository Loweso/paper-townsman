import pygame
import random
import os
import math
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
        best_action = self.get_best_action()
        if best_action == "chase":
            self.state = "chasing"
        elif best_action == "wander":
            self.state = "wandering"
        elif best_action == "teleport":
            self.attempt_teleport()

    def get_best_action(self):
        alpha = float('-inf')
        beta = float('inf')
        _, action = self.alpha_beta(self.rect.center, self.player.rect.center, 2, True, alpha, beta)
        return action

    def alpha_beta(self, enemy_pos, player_pos, depth, maximizing, alpha, beta):
        if depth == 0:
            return self.evaluate_state(enemy_pos, player_pos), None

        if maximizing:
            max_eval = float('-inf')
            best_action = None
            for action in ["chase", "wander", "teleport"]:
                new_pos = self.simulate_action(enemy_pos, action)
                eval, _ = self.alpha_beta(new_pos, player_pos, depth - 1, False, alpha, beta)
                if eval > max_eval:
                    max_eval = eval
                    best_action = action
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval, best_action
        else:
            # Minimize player success (simulate player escaping)
            min_eval = float('inf')
            for player_move in self.simulate_player_moves(player_pos):
                eval, _ = self.alpha_beta(enemy_pos, player_move, depth - 1, True, alpha, beta)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval, None

    def attempt_teleport(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_teleport_time < self.teleport_delay:
            return

        min_distance = 150  # Minimum teleport distance
        max_distance = 200  # Maximum teleport distance

        for _ in range(10):  # Try 10 random positions
            teleport_distance = random.randint(min_distance, max_distance)
            angle = random.uniform(0, 2 * math.pi)  # Use math.pi instead of 3.14159

            #  Use math.cos() and math.sin() correctly
            offset_x = teleport_distance * math.cos(angle)
            offset_y = teleport_distance * math.sin(angle)
            new_pos = pygame.math.Vector2(self.player.rect.center) + pygame.math.Vector2(offset_x, offset_y)

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
                return  # Successfully teleported


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