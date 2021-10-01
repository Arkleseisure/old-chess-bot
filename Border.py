import pygame
import Global_variables as Gv


# class for the sprite for the borders on the side of the board
class Border(pygame.sprite.Sprite):
    def __init__(self, y):
        super().__init__()
        self.image = pygame.Surface([Gv.square_size * 8, Gv.square_size])
        self.image.fill(Gv.border_colour)
        self.rect = self.image.get_rect()
        self.rect.x = Gv.board_top_left_x
        self.rect.y = y
