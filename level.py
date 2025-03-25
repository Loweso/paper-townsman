import pygame
from settings import *
from tile import Tile
from player import Player
from enemy import Enemy

class Level:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()
        self.world_map = WORLD_MAP
        self.visible_sprites = YSortCameraGroup()
        self.obstacle_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()
        self.bullet_sprites = pygame.sprite.Group()
        self.door_sprites = pygame.sprite.Group()
        self.create_map()

    def create_map(self):
        for row_index, row in enumerate(self.world_map):
            for col_index, col in enumerate(row):
                x = col_index * TILESIZE
                y = row_index * TILESIZE
                
                if col == 'x':
                    Tile((x, y), [self.visible_sprites, self.obstacle_sprites],"assets/rock (Small).png")
                if col == 'p':
                    self.player = Player((x, y), [self.visible_sprites], self.obstacle_sprites,self.bullet_sprites,self.enemy_sprites)
                if col == 'e':
                    Enemy((x, y), [self.visible_sprites,self.enemy_sprites], self.obstacle_sprites, self.player,self.bullet_sprites)
                if col == 'd':
                    Tile((x, y), [self.visible_sprites, self.door_sprites],"assets/rock (Small).png")
    
    def load_new_world(self):
        self.visible_sprites.empty()
        self.obstacle_sprites.empty()
        self.enemy_sprites.empty()
        self.door_sprites.empty()

        if self.world == "outside":
            self.world_map = WORLD_MAP_2
            self.create_map()
    
    def check_door_transition(self):
        if pygame.sprite.spritecollide(self.player, self.door_sprites, False):
            self.world = "outside"
            self.load_new_world()
               
    def run(self):
        self.visible_sprites.custom_draw(self.player)
        self.visible_sprites.update()
        self.check_door_transition()

class YSortCameraGroup(pygame.sprite.Group):
    def __init__(self):

        # general setup
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.half_width = self.display_surface.get_size()[0] // 2
        self.half_height = self.display_surface.get_size()[1] // 2
        self.offset = pygame.math.Vector2()

    def custom_draw(self, player):

        # getting the offset
        self.offset.x = player.rect.centerx - self.half_width
        self.offset.y = player.rect.centery - self.half_height

        for sprite in sorted(self.sprites(), key = lambda sprite: sprite.rect.centery):
            offset_rect = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image, offset_rect)