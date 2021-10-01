import Piece

directions = [[i - 1, j - 1] for j in range(3) for i in range(3)]
directions.pop(4)  # removes the direction [0, 0], which is not a possibility


# class for the queen
class Queen(Piece.Piece):
    def __init__(self, x, y, name, player_colour, image=True):
        super().__init__(x, y, name, player_colour, image=image)

    # gets the queen's moves given a board position
    def get_moves(self, board):
        self.possible_moves = []

        # loops through each direction the queen can move in
        for direction in directions:
            checker = True
            x = self.x + direction[0]
            y = self.y + direction[1]

            # loops until it either reaches the edges of the board or another piece
            while -1 < x < 8 and -1 < y < 8 and checker:
                if board[x][y][-1] != self.colour:
                    self.possible_moves.append(self.translate_coordinates(x, y))

                if board[x][y] != " ":
                    checker = False
                else:
                    x += direction[0]
                    y += direction[1]
        return self.possible_moves
