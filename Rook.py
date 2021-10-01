import Piece


directions = [[0, 1], [1, 0], [0, -1], [-1, 0]]


# class for the rook
class Rook(Piece.Piece):
    def __init__(self, x, y, name, player_colour, image=True):
        super().__init__(x, y, name, player_colour, image=image)

    # gets the rook's moves for any given board position
    def get_moves(self, board):
        self.possible_moves = []

        # gets the moves for each possible direction
        for direction in directions:
            checker = True
            x = self.x + direction[0]
            y = self.y + direction[1]

            # loops until it either reaches the edge of the board or reaches another piece (given by the bool checker)
            while -1 < x < 8 and -1 < y < 8 and checker:
                if board[x][y][-1] != self.colour:
                    self.possible_moves.append(self.translate_coordinates(x, y))

                if board[x][y] != " ":
                    checker = False
                else:
                    x += direction[0]
                    y += direction[1]
        return self.possible_moves
