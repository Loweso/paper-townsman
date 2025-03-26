import pygame

class Obstacle(pygame.sprite.Sprite):
    def __init__(self, pos, groups, name=None, size=(32, 32)):  
        super().__init__(groups)

        obstacle_images = {
            "KitchenCounter": "assets/obstacles/Kitchen Counter.png",
            "Refrigerator": "assets/obstacles/Refrigerator.png",
            "TV": "assets/obstacles/TV.png",
            "Stove": "assets/obstacles/Stove.png",
            "Sala Set": "assets/obstacles/Sala Set.png",
            "Book Shelf": "assets/obstacles/Book Shelf.png",
            "Garbage 1": "assets/obstacles/1Garbage.png",
            "Garbage 2": "assets/obstacles/2Garbage.png",
            "Garbage Pile": "assets/obstacles/Garbage Pile (Custom).png",
            "Garbage Pile 2": "assets/obstacles/Garbage Pile 2.png",
            "Banana Peel": "assets/obstacles/Banana Peel.png",
            "Crumpled Paper": "assets/obstacles/Crumpled Paper.png",
            "House": "assets/obstacles/house (Custom).png",
        }

        image_path = obstacle_images.get(name)
        if image_path:
            self.image = pygame.image.load(image_path).convert_alpha()
        else:
            self.image = pygame.Surface(size)
            self.image.fill((255, 0, 0))

        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox = self.rect.inflate(0, -10)
