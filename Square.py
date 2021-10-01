import pygame
import Global_variables as Gv
import Bits_and_Pieces as BaP


# class for the squares of the board
class Square(pygame.sprite.Sprite):
    def __init__(self, colour, x, y, size=Gv.square_size):
        super().__init__()
        self.colour = colour
        self.x = x
        self.y = y
        self.image = pygame.Surface([size, size])
        self.rect = self.image.get_rect()
        self.sync()
        pygame.draw.rect(self.image, colour, [0, 0, size, size])

    # makes sure the square is in the correct position on the board
    def sync(self):
        self.rect.x = self.x * Gv.square_size + Gv.board_top_left_x
        self.rect.y = self.y * Gv.square_size + Gv.board_top_left_y

    def part_of_move(self, move, player_colour):
        int_move = [BaP.un_translate(move[0]), int(move[1]) - 1, BaP.un_translate(move[2]), int(move[3]) - 1]
        if player_colour == 'white':
            if (self.x == int_move[0] and 7 - self.y == int_move[1]) or \
                    (self.x == int_move[2] and 7 - self.y == int_move[3]):
                return True
            else:
                return False
        else:
            if (7 - self.x == int_move[0] and self.y == int_move[1]) or \
                    (7 - self.x == int_move[2] and self.y == int_move[3]):
                return True
            else:
                return False
