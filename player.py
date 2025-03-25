import pygame
from settings import *
from bullet import Bullet
import math

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, obstacle_sprites,bullet_sprites,enemy_sprites):
        super().__init__(groups)
        
        self.pos = pygame.math.Vector2(pos)
        self.image = pygame.image.load('assets/player.png').convert_alpha()
        self.base_player_image = self.image
        self.hitbox_rect = self.base_player_image.get_rect(center = self.pos)
        self.rect = self.hitbox_rect.copy()
        
        self.enemy_sprites = enemy_sprites
    
        self.health = PLAYER_HEALTH

        self.direction = pygame.math.Vector2()
        self.speed = 5

        self.obstacle_sprites = obstacle_sprites
        self.bullet_sprites = bullet_sprites
        self.visible_sprites = groups[0]
        
        self.shoot = False
        self.shoot_cooldown = 0
        self.gun_barrel_offset = pygame.math.Vector2(GUN_OFFSET_X,GUN_OFFSET_Y)
    

    def input(self):
        self.direction.x = 0
        self.direction.y = 0
        keys = pygame.key.get_pressed()
    

        if keys[pygame.K_UP]:
            self.direction.y = -self.speed
        if keys[pygame.K_DOWN]:
            self.direction.y = self.speed
    
        if keys[pygame.K_LEFT]:
            self.direction.x = -self.speed
        if keys[pygame.K_RIGHT]:
            self.direction.x = self.speed
        
        if self.direction.x != 0 and self.direction.y != 0:
            self.direction.x /= math.sqrt(2)
            self.direction.y /= math.sqrt(2)
            
        if pygame.mouse.get_pressed() == (1,0,0) or keys[pygame.K_SPACE]:
            self.shoot = True
            self.is_shooting()
        else:
            self.shoot = False

  
    def check_enemy_collision(self):
        """Check if enemy is hit by a bullet"""
        for enemy in self.enemy_sprites:
            if self.hitbox_rect.colliderect(enemy.rect):
                self.health -= 20  # Reduce enemy health
                enemy.kill()  # Remove the bullet

                if self.health <= 0:
                    self.kill()
                    exit()# Destroy the enemy if health is zero
            

    def collision (self, direction):
        if direction == 'horizontal':
            for sprite in self.obstacle_sprites:
                if sprite.hitbox.colliderect(self.hitbox_rect):
                    if self.direction.x > 0: # moving right
                        self.hitbox_rect.right = sprite.hitbox.left
                    if self.direction.x < 0: # moving left
                        self.hitbox_rect.left = sprite.hitbox.right

        if direction == 'vertical':
            for sprite in self.obstacle_sprites:
                if sprite.hitbox.colliderect(self.hitbox_rect):
                    if self.direction.y > 0: # moving down
                        self.hitbox_rect.bottom = sprite.hitbox.top
                    if self.direction.y < 0: # moving up
                        self.hitbox_rect.top = sprite.hitbox.bottom
    
    def is_shooting(self):
        self.mouse_coords = pygame.mouse.get_pos()
        self.x_change_mouse_player = self.mouse_coords[0] - WIDTH // 2
        self.y_change_mouse_player = self.mouse_coords[1] - HEIGHT // 2
        self.angle = math.degrees(math.atan2(self.y_change_mouse_player, self.x_change_mouse_player))
        
        if self.shoot_cooldown == 0:
            self.shoot_cooldown = SHOOT_COOLDOWN
            spawn_bullet_pos = self.pos + self.gun_barrel_offset.rotate(self.angle)
            print(self.angle)
            print(self.pos,spawn_bullet_pos[0],spawn_bullet_pos[1])
            self.bullet = Bullet(spawn_bullet_pos[0],spawn_bullet_pos[1],self.angle,self.obstacle_sprites)
            self.bullet_sprites.add(self.bullet)
            self.visible_sprites.add(self.bullet)      
     

    def move(self, speed):
        if self.direction.magnitude() != 0:
            self.direction = self.direction.normalize()

        self.hitbox_rect.x += self.direction.x * speed
        self.collision('horizontal')
        self.hitbox_rect.y += self.direction.y * speed
        self.collision('vertical')
        self.rect.center = self.hitbox_rect.center
        
        self.pos = pygame.math.Vector2(self.hitbox_rect.center)


    def update(self):
        self.input()
        self.move(self.speed)
        self.check_enemy_collision()
     
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
 
        
        