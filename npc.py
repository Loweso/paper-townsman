import pygame
from settings import *

class NPC(pygame.sprite.Sprite):
    def __init__(self, pos, groups, name="NPC", image_path="", dialogue=None):
        super().__init__(groups)
        self.name = name
        self.image_path = image_path
        self.dialogue = dialogue or ["Hello there!"]
        self.dialogue_index = 0

        # Load and scale NPC image
        self.image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, (TILESIZE, TILESIZE))  # Ensure it fits tile size
        
        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox = self.rect.inflate(-10, -10)  # Adjust hitbox for better collision

        self.can_talk = False
        self.is_talking = False 

    def update(self):
        pass
