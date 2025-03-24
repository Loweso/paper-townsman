import pygame
from settings import *
from tile import Tile
from player import Player
from npc import NPC

import pytmx
from pytmx.util_pygame import load_pygame
from enemy import Enemy

class Level:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()
        self.world_map = WORLD_MAP
        self.visible_sprites = YSortCameraGroup()
        self.obstacle_sprites = pygame.sprite.Group()
        self.camera_group = self.visible_sprites
        self.dialogue_active = False
        self.enemies = pygame.sprite.Group()
        self.door_sprites = pygame.sprite.Group()
        self.tmx_data = load_pygame('assets/home.tmx')
        self.create_map()

    def create_map(self):
        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    tile_image = self.tmx_data.get_tile_image_by_gid(gid)
                    if tile_image:
                        pos = (x * self.tmx_data.tilewidth, y * self.tmx_data.tileheight)
                        Tile(pos, [self.visible_sprites])
                        
                        tile_props = self.tmx_data.get_tile_properties_by_gid(gid)
                        if tile_props and tile_props.get('collision') == True:
                            Tile(pos, [self.visible_sprites, self.obstacle_sprites])

        for obj in self.tmx_data.objects:
            pos = (obj.x, obj.y)

            if obj.properties.get('collision') == True:
                Tile(pos, [self.visible_sprites, self.obstacle_sprites])

            if obj.name == 'Player':
                self.player = Player(pos, [self.visible_sprites], self.obstacle_sprites)
            elif obj.name == 'NPC':
                dialogue = obj.properties.get('dialogue', "bitch im a cube lmao")
                dialogue_lines = dialogue.split('|')
                NPC(pos, [self.visible_sprites, self.obstacle_sprites], name=obj.name, color='pink', dialogue=dialogue_lines)

        if not hasattr(self, 'player'):
            print("[WARNING] Player object not found in map! Adding default at (0,0)")
            self.player = Player((0, 0), [self.visible_sprites], self.obstacle_sprites)


    def run(self):
        if not hasattr(self, 'player'):
            print("[ERROR] Player not initialized!")
            print("Check your .tmx object layer - is the Player object there?")
            return

        self.visible_sprites.custom_draw(self.player, self.tmx_data)

        for sprite in self.visible_sprites:
            if hasattr(sprite, 'update'):
                if isinstance(sprite, Player):
                    sprite.update(dialogue_mode=self.dialogue_active)
                else:
                    sprite.update()

        self.check_npc_interaction()
        self.display_dialogue()

    def check_npc_interaction(self):
        for sprite in self.visible_sprites:
            if isinstance(sprite, NPC):
                if self.player.rect.colliderect(sprite.rect):
                    sprite.can_talk = True
                else:
                    sprite.can_talk = False
                    sprite.is_talking = False


    def display_dialogue(self):
        font = pygame.font.SysFont(None, 24)
        padding = 6
        max_width = 250

        for sprite in self.visible_sprites:
            if isinstance(sprite, NPC) and sprite.is_talking:
                text = sprite.dialogue[sprite.dialogue_index]
                words = text.split(' ')
                lines = []
                current_line = ''

                for word in words:
                    test_line = current_line + word + ' '
                    test_surface = font.render(test_line, True, 'black')
                    if test_surface.get_width() <= max_width - padding * 2:
                        current_line = test_line
                    else:
                        lines.append(current_line)
                        current_line = word + ' '
                lines.append(current_line)

                line_surfaces = [font.render(line, True, 'black') for line in lines]
                box_width = max(surface.get_width() for surface in line_surfaces) + padding * 2
                box_height = sum(surface.get_height() for surface in line_surfaces) + padding * (len(lines) + 1)

                offset_x = sprite.rect.centerx - self.camera_group.offset.x
                offset_y = sprite.rect.top - self.camera_group.offset.y

                box_x = offset_x - box_width // 2
                box_y = offset_y - box_height - 10

                dialogue_rect = pygame.Rect(box_x, box_y, box_width, box_height)
                pygame.draw.rect(self.display_surface, 'white', dialogue_rect, border_radius=5)
                pygame.draw.rect(self.display_surface, 'black', dialogue_rect, width=2, border_radius=5)

                y_offset = box_y + padding
                for surface in line_surfaces:
                    self.display_surface.blit(surface, (box_x + padding, y_offset))
                    y_offset += surface.get_height() + padding // 2

    def check_dialogue_trigger(self):
        for sprite in self.visible_sprites:
            if isinstance(sprite, NPC) and sprite.can_talk:
                if not sprite.is_talking:
                    sprite.is_talking = True
                    sprite.dialogue_index = 0
                    self.dialogue_active = True 
                else:
                    sprite.dialogue_index += 1
                    if sprite.dialogue_index >= len(sprite.dialogue):
                        sprite.is_talking = False
                        self.dialogue_active = False
        self.check_door_transition()

class YSortCameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.half_width = self.display_surface.get_size()[0] // 2
        self.half_height = self.display_surface.get_size()[1] // 2
        self.offset = pygame.math.Vector2()

    def custom_draw(self, player, tmx_data=None):
        for layer in tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    tile_image = tmx_data.get_tile_image_by_gid(gid)
                    if tile_image:
                        pos = (x * tmx_data.tilewidth, y * tmx_data.tileheight)
                        offset_pos = pygame.Vector2(pos) - self.offset
                        self.display_surface.blit(tile_image, offset_pos)

            elif isinstance(layer, pytmx.TiledImageLayer):
                image = layer.image
                if image:
                    offset_pos = pygame.Vector2(0, 0) - self.offset  # Adjust if needed
                    self.display_surface.blit(image, offset_pos)


        self.offset.x = player.rect.centerx - self.half_width
        self.offset.y = player.rect.centery - self.half_height

        if tmx_data:
            for layer in tmx_data.visible_layers:
                if isinstance(layer, pytmx.TiledTileLayer):
                    for x, y, gid in layer:
                        tile_image = tmx_data.get_tile_image_by_gid(gid)
                        if tile_image:
                            pos = (x * tmx_data.tilewidth, y * tmx_data.tileheight)
                            offset_pos = pygame.Vector2(pos) - self.offset
                            self.display_surface.blit(tile_image, offset_pos)

        for sprite in sorted(self.sprites(), key=lambda sprite: sprite.rect.centery):
            offset_rect = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image, offset_rect)
