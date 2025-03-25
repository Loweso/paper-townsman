import pygame
from settings import *

class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos, groups, obstacle_sprites, player,bullet_sprites):
        super().__init__(groups)
        original_image = pygame.image.load('assets/rock.png').convert_alpha()
        self.image = pygame.transform.scale(original_image, (TILESIZE, TILESIZE)) 
        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox = self.rect.inflate(0, -10)
        self.direction = pygame.math.Vector2()
        self.health = ENEMY_HEALTH
        
        self.player = player
        self.bullet_sprites = bullet_sprites
        self.obstacle_sprites = obstacle_sprites
        self.speed = 2  # Adjust speed as needed
        self.detection_radius = 200  # Enemy moves if the player is within this range

    def move_towards_player(self):
        """Move towards the player only if within detection radius"""
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

            self.rect.center = self.hitbox.center  # Ensure rect follows hitbox

    def check_bullet_collision(self):
        """Check if enemy is hit by a bullet"""
        for bullet in self.bullet_sprites:
            if self.hitbox.colliderect(bullet.rect):
                self.health -= BULLET_DAMAGE  # Reduce enemy health
                bullet.kill()  # Remove the bullet

                if self.health <= 0:
                    self.kill()  # Destroy the enemy if health is zero
    
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
        self.move_towards_player()
        self.check_bullet_collision() 
