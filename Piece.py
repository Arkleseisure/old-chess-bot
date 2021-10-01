import pygame
import Bits_and_Pieces as BaP
import Global_variables as Gv


# superclass for all pieces
class Piece(pygame.sprite.Sprite):
    x = 0
    y = 0
    possible_moves = []
    colour = "w"

    def __init__(self, x, y, name, player_colour, size=Gv.square_size, image=True):
        super().__init__()
        self.x = x
        self.y = y

        # having an image can slow down many processes where the piece is not being visualised
        if image:
            self.image = BaP.load_image(name)
            self.image = pygame.transform.scale(self.image, (size, size))
            self.image.set_colorkey(Gv.absolute_white)
            self.rect = self.image.get_rect()
            self.move(player_colour)
        self.has_image = image
        self.colour = name[1]
        self.name = name
        self.hierarchy = 0

    def get_moves(self, board):
        return self.possible_moves

    # turns the destination location of a piece into a move
    def translate_coordinates(self, x, y):
        return chr(self.x + 97) + str(self.y + 1) + chr(x + 97) + str(y + 1)

    # moves the piece to the position on the screen determined by its current x and y coordinates
    def move(self, player_colour):
        if player_colour == "black":
            self.rect.x = (7 - self.x) * Gv.square_size + Gv.board_top_left_x
            self.rect.y = self.y * Gv.square_size + Gv.board_top_left_y
        else:
            self.rect.x = self.x * Gv.square_size + Gv.board_top_left_x
            self.rect.y = (7 - self.y) * Gv.square_size + Gv.board_top_left_y


# class for the number on the side of the board giving the extra material held by one person in the position.
# subclass of piece for convenience as its position depends on a bunch of pieces in front of it and treating it as one
# is easier
class ExtraMaterial(Piece):
    def __init__(self, x, y, name, player_colour, size, text):
        super().__init__(x, y, name, player_colour, size, False)
        self.image = pygame.Surface([size, size])
        self.image.fill(Gv.border_colour)
        BaP.print_screen(self.image, text, size//2, size//2, size//2, Gv.text_colour, False)
        self.rect = self.image.get_rect()
        self.move(player_colour)
