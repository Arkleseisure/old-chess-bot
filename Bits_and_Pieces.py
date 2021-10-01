import time
import Global_variables as Gv
from Button import Button
import pygame
import pygame.freetype

pygame.freetype.init()


# loads an image
def load_image(name):
    f = pygame.image.load(name + ".png")
    return f


# turns a letter coordinate into a numerical x coordinate on the board
def un_translate(letter):
    return ord(letter) - 97


# changes white to black and black to white
def opposite(col):
    if col == "w":
        return "b"
    else:
        return "w"


# prints to the screen
def print_screen(surface, text, x, y, size, colour, left_align=True, font_type="Calibri"):
    # turns the text into a pygame surface
    font = pygame.freetype.SysFont(font_type, size, True)
    print_image, rect = font.render(text, colour)

    # blits the new text surface onto the given surface and updates the screen
    if not left_align:
        text_width, text_height = print_image.get_size()
        surface.blit(print_image, (x - text_width//2, y - text_height//2))
    else:
        surface.blit(print_image, (x, y))
    return print_image.get_size()


# returns a list of the locations of the pieces with the given name on the board.
def find_piece(name, board):
    squares = []
    for col in range(len(board)):
        for row in range(len(board)):
            if name == board[col][row]:
                squares.append([col, row])
    return squares


# returns a list of the locations of all the pieces on the board
def find_pieces(board):
    squares = {"Pw": [], "Pb": [], "Bw": [], "Bb": [], "Nw": [], "Nb": [], "Rw": [], "Rb": [], "Qw": [], "Qb": [],
               "Kw": [], "Kb": []}
    for col in range(len(board)):
        for row in range(len(board)):
            if board[col][row] != " ":
                squares[board[col][row]].append([col, row])
    return squares


# Waits for the user to click then returns the location of the click.
def wait_for_click(clocks=None):
    start_time = time.time()
    i = 1
    time_group = pygame.sprite.Group()
    lost_on_time = False
    while True:
        # clocks[0] is mins, clocks[1] is secs
        # clocks[2] is the location of the clock ("top" or "bottom") and clocks[3] is the screen
        if clocks is not None:
            # updates the clock's value
            if time.time() - start_time > i:
                i += 1
                if clocks[1] != 0:
                    clocks[1] = clocks[1] - 1
                elif clocks[0] != 0:
                    clocks[1] = 59
                    clocks[0] -= 1
                else:
                    return 0, 0, True, 0, 0

                # draws the ticking clock to the screen
                x = Gv.board_top_left_x - Gv.square_size*1.1
                y = 0.5*(Gv.board_top_left_y - Gv.square_size*0.4)
                width = Gv.square_size
                height = Gv.square_size * 0.4
                text = str(clocks[0]) + ":" + ("0" if clocks[1] < 10 else "") + str(clocks[1])
                font_size = Gv.square_size//4
                if clocks[2] == "top":
                    clock = Button(x, y, width, height, text=text, font_size=font_size)
                else:
                    clock = Button(x, Gv.screen_height - y - height, width, height, text=text, font_size=font_size)
                for item in time_group:
                    time_group.remove(item)
                time_group.add(clock)
                # the screen is passed into the function via the clocks list
                time_group.draw(clocks[3])
                pygame.display.flip()

        # checks if the user has clicked
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONUP:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if clocks is None:
                    clocks = [0, 0]
                return mouse_x, mouse_y, lost_on_time, clocks[0], clocks[1]


def castling_legality(game):
    if game.to_play() == 'w':
        colour_key = 0
        y = 0
    else:
        colour_key = 1
        y = 7

    castling = [game.castle_queenside[colour_key], game.castle_kingside[colour_key]]

    if in_check(game.to_play(), game.board, [[4, y], [4, y]])[0] or castling == [False, False]:
        return [False, False]

    # checks kingside castling
    if castling[1] and game.board[5][y] == game.board[6][y] == ' ':
        if in_check(game.to_play(), game.board, [[5, y], [5, y]])[0] or \
                in_check(game.to_play(), game.board, [[6, y], [6, y]])[0]:
            castling[1] = False
    else:
        castling[1] = False

    # checks queenside castling
    if castling[0] and game.board[1][y] == game.board[2][y] == game.board[3][y] == ' ':
        if in_check(game.to_play(), game.board, [[2, y], [2, y]])[0] or \
                in_check(game.to_play(), game.board, [[3, y], [3, y]])[0]:
            castling[0] = False
    else:
        castling[0] = False

    return castling


# turns a move from the form "original square destination square" (e.g e2e4) to the more widely recognised
# "piece destination square" (e.g Qe4) which is easier for humans
def proper_notation(move, game, piece_captured, prom, game_over):
    notation_move = ""
    int_move = [un_translate(move[0]), int(move[1]) - 1, un_translate(move[2]), int(move[3]) - 1]

    # checks for castling
    if game.board[int_move[2]][int_move[3]][0] == "K" and abs(int_move[2] - int_move[0]) == 2:
        if int_move[2] - int_move[0] == 2:
            return "O-O"
        elif int_move[0] - int_move[2] == 2:
            return "O-O-O"

    # accounts for all other non-pawn moves
    elif game.board[int_move[2]][int_move[3]][0] != "P" and prom == "":
        notation_move += game.board[int_move[2]][int_move[3]][0]

    # for if a pawn has captured a piece
    elif piece_captured is True:
        notation_move += move[0] + "x" + move[2] + move[3]
        if prom != "":
            notation_move += "=" + prom
        return notation_move

    # any other pawn scenario
    else:
        notation_move += move[2] + move[3]
        if prom != "":
            notation_move += "=" + prom
        return notation_move

    '''
    Finds other pieces which have the same name. 
    If another piece of the same type and colour can move to the same destination square, 
    then a coordinate to specify the moving piece is added
    '''
    p = game.piece_dict[move[2:4]]
    game.board[int_move[2]][int_move[3]] = " "
    for p2 in game.piece_list:
        if p2.name == p.name and (p.x != p2.x or p.y != p2.y):
            for action in p2.get_moves(game.board):
                if action[2] == move[2] and action[3] == move[3]:
                    if un_translate(action[0]) != un_translate(move[0]):
                        notation_move += move[0]
                    else:
                        notation_move += move[1]
    game.board[int_move[2]][int_move[3]] = p.name

    # "x" signifies that the move was a capturing move
    if piece_captured is True:
        notation_move += "x"

    # adds the destination square
    notation_move += move[2] + move[3]

    # "+" signifies that the opponent is now in check, "#" signifies that the move checkmated the opponent
    is_in_check, checking_piece = in_check(game.to_play(), game.board, game.king_loc)
    if is_in_check:
        if game_over:
            notation_move += "#"
        else:
            notation_move += "+"

    return notation_move


# verifies whether one colour is in check
def in_check(colour, board, king_loc):
    loc = king_loc[0 if colour == "w" else 1]
    directions = [{0: 1, 1: 1}, {0: 1, 1: 0}, {0: 1, 1: -1}, {0: 0, 1: 1}, {0: 0, 1: -1}, {0: -1, 1: 1}, {0: -1, 1: 0},
                  {0: -1, 1: -1}]

    # all directions are from white's perspective
    for direction in directions:
        i = 1
        looping = True
        x = loc[0] + direction[0]
        y = loc[1] + direction[1]
        while 8 > x > -1 and 8 > y > -1 and looping:
            if board[x][y] != " ":
                looping = False
                if board[x][y][-1] == opposite(colour):
                    piece = board[x][y][0]
                    if piece == "Q" or (piece == "B" and direction[0] != 0 and direction[1] != 0) \
                            or (piece == "R" and (direction[0] == 0 or direction[1] == 0)) \
                            or (piece == "K" and i == 1) \
                            or (piece == "P" and i == 1 and direction[0] != 0 and
                                direction[1] == (1 if colour == "w" else -1)):
                        return True, translate_coordinates(x, y, loc[0], loc[1])
            i += 1
            x += direction[0]
            y += direction[1]

    # looks for knight moves
    squares = [{0: 2, 1: 1}, {0: 2, 1: -1}, {0: 1, 1: 2}, {0: 1, 1: -2}, {0: -1, 1: 2}, {0: -1, 1: -2}, {0: -2, 1: 1},
               {0: -2, 1: -1}]
    # removes knight moves which would end up off the board
    i = 0
    while i < len(squares):
        if not 8 > loc[0] + squares[i][0] > -1 or not 8 > loc[1] + squares[i][1] > -1:
            squares.pop(i)
        else:
            i += 1

    # does the actual checking of moves
    for square in squares:
        if board[loc[0] + square[0]][loc[1] + square[1]] == "N" + opposite(colour):
            return True, translate_coordinates(loc[0] + square[0], loc[1] + square[1], loc[0], loc[1])
    return False, None


# function used to improve efficiency when finding legal moves.
# It checks whether any checks which have been given in the past are still check
def still_in_check(previous_checks, board, current_player, king_loc):
    # gives the location of the king
    loc = king_loc[0 if current_player == "w" else 1]

    # loops through previous moves that have given check.
    for move in previous_checks:
        int_move = [un_translate(move[0]), int(move[1]) - 1, un_translate(move[2]), int(move[3]) - 1]
        vertical = 1 if int_move[3] > int_move[1] else -1
        horizontal = 1 if int_move[2] > int_move[0] else -1
        move_is_check = True
        if board[int_move[0]][int_move[1]][-1] == opposite(current_player) and \
                loc[0] == int_move[2] and loc[1] == int_move[3]:

            # checks for vertical blocking
            if move[0] == move[2]:
                for i in range(int_move[1] + vertical, int_move[3], vertical):
                    if board[int_move[2]][i] != " ":
                        move_is_check = False

            # checks for horizontal blocking
            elif move[1] == move[3]:
                for i in range(int_move[0] + horizontal, int_move[2], horizontal):
                    if board[i][int_move[3]] != " ":
                        move_is_check = False

            # checks for blocking along the diagonals
            elif abs(int_move[2] - int_move[0]) == abs(int_move[3] - int_move[1]):
                for i in range(abs(int_move[3] - int_move[1]) - 1):
                    if board[int_move[0] + horizontal * (i + 1)][int_move[1] + vertical * (i + 1)] != " ":
                        move_is_check = False
        else:
            move_is_check = False

        if move_is_check:
            return True
    return False


# given two sets of coordinates, starting and finishing positions, returns a move
def translate_coordinates(x1, y1, x2, y2):
    return chr(x1 + 97) + str(y1 + 1) + chr(x2 + 97) + str(y2 + 1)


# returns the coordinates of a given square of the form a3, b4, ...
def translate(x, y):
    return chr(x + 97) + str(y + 1)


def to_time(secs):
    secs = round(secs)  # ensures that 59.6s doesn't get displayed as 60s for instance
    return '{0}h {1}min {2}s'.format(int(secs//3600), int((secs % 3600)//60), int(secs % 60))
