import Piece
import Bits_and_Pieces as BaP


# class for the pawn piece
class Pawn(Piece.Piece):
    def __init__(self, x, y, name, player_colour, image=True):
        super().__init__(x, y, name, player_colour, image=image)
        # pawns move down the board if black and up if white
        self.direction = -1 if self.colour == "b" else 1

    # gets the pawn's moves
    def get_moves(self, board):
        self.possible_moves = []

        # moving forward one or two squares
        if board[self.x][self.y + self.direction] == " ":
            self.possible_moves.append(self.translate_coordinates(self.x, self.y + self.direction))

            # 3.5 - 2.5*self.direction gives 6 if black and 1 if white... The pawn's starting rank (when counted from 0)
            if self.y == 3.5 - 2.5*self.direction and board[self.x][self.y + 2 * self.direction] == " ":
                self.possible_moves.append(self.translate_coordinates(self.x, self.y + 2 * self.direction))

        # capture to the right
        if self.x < 7 and board[self.x + 1][self.y + self.direction][-1] == BaP.opposite(self.colour):
            self.possible_moves.append(self.translate_coordinates(self.x + 1, self.y + self.direction))

        # capture to the left
        if self.x > 0 and board[self.x - 1][self.y + self.direction][-1] == BaP.opposite(self.colour):
            self.possible_moves.append(self.translate_coordinates(self.x - 1, self.y + self.direction))
        return self.possible_moves
