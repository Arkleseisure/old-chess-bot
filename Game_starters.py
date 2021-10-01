from copy import deepcopy
import pygame
import Global_variables as Gv
import Square
import Pawn
import Bishop
import Knight
import Rook
import Queen
import King


def set_up(player_colour):
    col = Gv.dark_square_colour
    squares = pygame.sprite.Group()
    # sets up squares
    for i in range(8):
        for j in range(8):
            if col == Gv.dark_square_colour:
                col = Gv.light_square_colour
            else:
                col = Gv.dark_square_colour
            s = Square.Square(col, i, j)
            squares.add(s)
        if col == Gv.dark_square_colour:
            col = Gv.light_square_colour
        else:
            col = Gv.dark_square_colour

    past_board_list = []
    board = set_up_board()
    past_board_list.append(deepcopy(board))
    piece_dict, piece_list, king_loc = set_up_pieces(player_colour, board)
    return board, past_board_list, piece_dict, piece_list, king_loc, squares


# sets up the board at the start of the game
def set_up_board():
    board = {}
    for i in range(8):
        a = {}
        # Adds blank spaces to the board
        for j in range(8):
            a[j] = " "
        board[i] = a

    # adds the pieces
    board_order = "RNBQKBNR"
    for i in range(8):
        board[i][0] = board_order[i] + "w"
        board[i][1] = "Pw"
        board[i][6] = "Pb"
        board[i][7] = board_order[i] + "b"
    return board


# fills the piece list and piece dict with the pieces at the start of the game
def set_up_pieces(player_colour, board, with_image=True):
    piece_dict = {}
    piece_list = pygame.sprite.Group()
    king_loc = {}
    for i in range(8):
        for j in range(8):
            p = " "
            if board[i][j][0] == "P":
                p = Pawn.Pawn(i, j, board[i][j], player_colour, image=with_image)
            elif board[i][j][0] == "B":
                p = Bishop.Bishop(i, j, board[i][j], player_colour, image=with_image)
            elif board[i][j][0] == "N":
                p = Knight.Knight(i, j, board[i][j], player_colour, image=with_image)
            elif board[i][j][0] == "R":
                p = Rook.Rook(i, j, board[i][j], player_colour, image=with_image)
            elif board[i][j][0] == "Q":
                p = Queen.Queen(i, j, board[i][j], player_colour, image=with_image)
            elif board[i][j][0] == "K":
                p = King.King(i, j, board[i][j], player_colour, image=with_image)
                king_loc[0 if p.colour == "w" else 1] = {0: i, 1: j}
            piece_dict[chr(i + 97) + str(j + 1)] = p
            if p != " ":
                piece_list.add(p)
    return piece_dict, piece_list, king_loc
