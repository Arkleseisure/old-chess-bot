import Piece

directions = [[-1, -1], [-1, 1], [1, -1], [1, 1]]


class Bishop(Piece.Piece):
    def __init__(self, x, y, name, player_colour, image=True):
        super().__init__(x, y, name, player_colour, image=image)

    # returns the moves the piece can play
    def get_moves(self, board):
        self.possible_moves = []

        # gets the move for each possible direction
        for direction in directions:
            checker = True
            x = self.x + direction[0]
            y = self.y + direction[1]

            # loops through the possible moves until it has either moved off the board or it encounters another piece
            while checker and -1 < x < 8 and -1 < y < 8:
                if board[x][y][-1] != self.colour:
                    self.possible_moves.append(self.translate_coordinates(x, y))

                if board[x][y][-1] != ' ':
                    checker = False
                else:
                    x += direction[0]
                    y += direction[1]
        return self.possible_moves
