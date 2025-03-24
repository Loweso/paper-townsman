import pygame
import os
from settings import *
from bullet import Bullet

class Player(pygame.sprite.Sprite):
    import os

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, obstacle_sprites):
        super().__init__(groups)

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
        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox = self.rect.inflate(0, -26)

        self.direction = pygame.math.Vector2()
        self.speed = 5

        self.obstacle_sprites = obstacle_sprites
        
        self.shoot = False
        self.shoot_cooldown = 0
        self.gun_barrel_offset = pygame.math.Vector2(GUN_OFFSET_X,GUN_OFFSET_Y)
        self.last_direction = 'down'  # for idle animation

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


    def input(self):
        keys = pygame.key.get_pressed()
    

        if keys[pygame.K_UP]:
            self.direction.y = -1
            self.status = 'up'
        elif keys[pygame.K_DOWN]:
            self.direction.y = 1
            self.status = 'down'
        else:
            self.direction.y = 0

        if keys[pygame.K_LEFT]:
            self.direction.x = -1
            self.status = 'left'
        elif keys[pygame.K_RIGHT]:
            self.direction.x = 1
            self.status = 'right'
        else:
            self.direction.x = 0

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
        if self.shoot_cooldown == 0:
            self.shoot_cooldown = SHOOT_COOLDOWN
            spawn_bullet_pos = self.pos + self.gun_barrel_offset.rotate(self.angle)
            self.bullet = Bullet(spawn_bullet_pos[0],spawn_bullet_pos[1],self.angle)

    def move(self, speed):
        if self.direction.magnitude() != 0:
            self.direction = self.direction.normalize()

        self.hitbox.x += self.direction.x * speed
        self.collision('horizontal')
        self.hitbox.y += self.direction.y * speed
        self.collision('vertical')
        self.rect.center = self.hitbox.center



    def update(self, *args, **kwargs):
        dialogue_mode = kwargs.get('dialogue_mode', False)

        if not dialogue_mode:
            self.input()
            self.move(self.speed)
        else:
            # Stop movement during dialogue
            self.direction.x = 0
            self.direction.y = 0
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
 
        

        self.animate()