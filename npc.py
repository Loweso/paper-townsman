import pygame
from settings import *

class NPC(pygame.sprite.Sprite):
    def __init__(self, pos, groups, name="NPC", color='blue', dialogue=None):
        super().__init__(groups)
        self.name = name
        self.dialogue = dialogue or ["Hello there!"]
        self.dialogue_index = 0

        self.image = pygame.Surface((TILESIZE, TILESIZE))
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox = self.rect.inflate(-10, -10)

        self.can_talk = False
        self.is_talking = False 

    def update(self):
        pass 
