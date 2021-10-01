import Piece

moves = [[1, 2], [2, 1], [2, -1], [1, -2], [-1, -2], [-2, -1], [-2, 1], [-1, 2]]


class Knight(Piece.Piece):
    def __init__(self, x, y, name, player_colour, image=True):
        super().__init__(x, y, name, player_colour, image=image)

    def get_moves(self, board):
        self.possible_moves = []
        for move in moves:
            x = self.x + move[0]
            y = self.y + move[1]
            if -1 < x < 8 and -1 < y < 8 and board[x][y][-1] != self.colour:
                self.possible_moves.append(self.translate_coordinates(x, y))
        return self.possible_moves
