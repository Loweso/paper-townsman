import pygame
from settings import *
from tile import Tile
from player import Player
from npc import NPC
from obstacle import Obstacle

import pytmx
from pytmx.util_pygame import load_pygame
from enemy import Enemy
from fastenemy import FastEnemy
from npc_details import NPC_DETAILS

class Level:
    def __init__(self,player_health=100, map_path='assets/map_data/home.tmx'):
        self.display_surface = pygame.display.get_surface()
        self.visible_sprites = YSortCameraGroup()
        self.obstacle_sprites = pygame.sprite.Group()
        self.camera_group = self.visible_sprites
        self.dialogue_active = False
        self.enemy_sprites = pygame.sprite.Group()
        self.bullet_sprites = pygame.sprite.Group()
        self.door_sprites = pygame.sprite.Group()
        
        self.player_health = player_health  # Store health

        self.map_path = map_path
        self.tmx_data = load_pygame(self.map_path)

        self.x_min, self.y_min, self.x_max, self.y_max = 13, 106, 499, 486

        # For plot progression purposes
        self.npc_dialogue_states = {}
        self.enemy_states = {}

        self.create_map()

    def create_map(self):
        self.visible_sprites.empty()
        self.obstacle_sprites.empty()
        self.enemy_sprites.empty()
        self.door_sprites.empty()
        self.bullet_sprites.empty()

        for layer in self.tmx_data.objectgroups:
            if layer.name == "Obstacles":
                for obj in layer:
                    pos = (obj.x, obj.y)
                    Obstacle(pos, [self.visible_sprites, self.obstacle_sprites], name=obj.name)

        for obj in self.tmx_data.objects:
            pos = (obj.x, obj.y)
            if obj.name == 'Door':
                destination = obj.properties.get('destination')
                door_sprite = Tile(pos, [self.visible_sprites, self.door_sprites], "assets/obstacles/Entrance Exit.png")
                door_sprite.image.fill((0, 0, 0, 0))
                door_sprite.destination = destination

                door_sprite.x_min = int(obj.properties.get('x_min', self.x_min))
                door_sprite.y_min = int(obj.properties.get('y_min', self.y_min))
                door_sprite.x_max = int(obj.properties.get('x_max', self.x_max))
                door_sprite.y_max = int(obj.properties.get('y_max', self.y_max))

            elif obj.name == 'Player':
                self.player = Player(pos, [self.visible_sprites], self.obstacle_sprites,self.bullet_sprites,self.enemy_sprites)
                self.player.health = self.player_health
                self.player.level = self
                
            elif obj.name == 'NPC':
                character = obj.properties.get('character')
                npc_data = NPC_DETAILS.get(character, {"asset": "", "dialogue": ["Hello there!"]})

                npc = NPC(pos, [self.visible_sprites, self.obstacle_sprites], 
                        name=obj.name, image_path=npc_data["asset"], 
                        dialogue=npc_data["dialogue"])

                # Restore modified dialogue if previously changed
                if character in self.npc_dialogue_states:
                    npc.dialogue = self.npc_dialogue_states[character]

            elif obj.name == 'Enemy':
                enemyID = obj.properties.get('enemyID')
                Enemy(pos, [self.visible_sprites, self.enemy_sprites], self.obstacle_sprites, self.player, self.bullet_sprites, enemyID=enemyID)

            elif obj.name == 'Enemy2':
                enemyID = obj.properties.get('enemyID')
                FastEnemy(pos, [self.visible_sprites, self.enemy_sprites], self.obstacle_sprites, self.player, self.bullet_sprites, enemyID=enemyID)
        
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
                    sprite.update(dialogue_mode=self.dialogue_active, x_min=self.x_min, x_max=self.x_max, y_min=self.y_min, y_max=self.y_max)
                else:
                    sprite.update()

        self.check_npc_interaction()
        self.display_dialogue()

    def check_npc_interaction(self):
        for sprite in self.visible_sprites:
            if isinstance(sprite, NPC):
                if self.player.rect.colliderect(sprite.rect):
                    sprite.can_talk = True
                    if (
                        len(self.enemy_sprites) == 0
                        and self.map_path == "assets/map_data/outside.tmx"
                        and getattr(sprite, "image_path", None) in ["assets/npcs/mother.png", "assets/npcs/old-man.png"]
                    ):
                        self.npc_dialogue_states["mother"] = [
                                "What were you doing outside? Our meal is done.",
                                "Your... father...?",
                                "Are you okay, dear?",
                                "I don't know who your father is, but I don't wanna know, ok?",
                                "So let's just eat. My cooking's getting cold."
                            ]
                        sprite.dialogue = self.npc_dialogue_states["mother"]

                        if sprite.image_path == "assets/npcs/old-man.png":
                            self.npc_dialogue_states["old-man"] = [
                                "Well, good job cleaning those things up, kiddo.",
                                "...Hm? Have I seen your father?",
                                "Never heard of your father before today.",
                                "Did he visit?",
                                "Ask your mom. Maybe she knows.",
                            ]
                            sprite.dialogue = self.npc_dialogue_states["old-man"]

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

    def check_door_transition(self):
        collided_doors = pygame.sprite.spritecollide(self.player, self.door_sprites, False)
        for door in collided_doors:
            if hasattr(door, 'destination') and door.destination:
                print(f"Transitioning to {door.destination}")

                self.load_new_world(door.destination)

                self.x_min, self.y_min = door.x_min, door.y_min
                self.x_max, self.y_max = door.x_max, door.y_max

    def register_enemy_death(self, enemyID):
        self.enemy_states[enemyID] = True

    def load_new_world(self, map_path):
        self.map_path = map_path
        self.tmx_data = load_pygame(self.map_path)
        
        # Save player health
        previous_health = self.player.health if hasattr(self, 'player') else 100  

        # Save modified NPC dialogues
        for sprite in self.visible_sprites:
            if isinstance(sprite, NPC):
                self.npc_dialogue_states[sprite.name] = sprite.dialogue  # Save dialogue state

        self.create_map()  # Reload map and recreate objects

        if hasattr(self, 'player'):
            self.player.health = previous_health  # Restore health

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
