from settings import *
from enemy import Enemy
import pygame

class FastEnemy(Enemy):
    def __init__(self, pos, groups, obstacle_sprites, player, bullet_sprites, enemyID):
        super().__init__(pos, groups, obstacle_sprites, player, bullet_sprites, enemyID)
        
        self.base_speed = 4  
        self.speed = self.base_speed
        self.health = ENEMY_HEALTH + 20
        self.load_images("assets/enemy/fast/")  

    def check_bullet_collision(self):
        for bullet in self.bullet_sprites:
            if self.hitbox.colliderect(bullet.rect):
                self.health -= BULLET_DAMAGE 
                self.speed += 0.5
                bullet.kill()

                if self.health <= 0:
                    if hasattr(self.player, "level"): 
                        self.player.level.register_enemy_death(self.enemyID)
                    self.kill()
