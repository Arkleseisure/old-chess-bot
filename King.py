import Piece

moves = [[i - 1, j - 1] for i in range(3) for j in range(3)]
moves.pop(4)  # removes the illegal [0, 0] move


class King(Piece.Piece):
    def __init__(self, x, y, name, player_colour, image=True):
        super().__init__(x, y, name, player_colour, image=image)

    # gets all the moves the king can do in a certain board position
    def get_moves(self, board):
        self.possible_moves = []
        for move in moves:
            x = self.x + move[0]
            y = self.y + move[1]
            if -1 < x < 8 and -1 < y < 8 and (board[x][y] == " " or board[x][y][-1] != self.colour):
                self.possible_moves.append(self.translate_coordinates(x, y))
        return self.possible_moves
