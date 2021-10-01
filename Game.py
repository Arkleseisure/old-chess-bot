import Game_enders
import Bits_and_Pieces as BaP
from copy import deepcopy
import Pawn
import Bishop
import Knight
import Rook
import Queen
import King
from pygame import sprite
from numpy import zeros, ones, full
import random
import time


# class incorporating all aspects of a game
class Game:
    def __init__(self, piece_dict, piece_list, board, past_boards, castle_kingside, castle_queenside, player_colour,
                 king_loc, move_counter=0, history=None, image=True):
        self.history = deepcopy(history) or []
        self.board = deepcopy(board)
        # processing is faster without images, so this is used for the mcts for example
        if not image:
            self.piece_dict = {}
            self.piece_list = sprite.Group()
            for i in range(8):
                for j in range(8):
                    self.piece_dict[chr(i + 97) + str(j + 1)] = " "
            for p in piece_list:
                new_piece = " "
                if p.name[0] == "Q":
                    new_piece = Queen.Queen(p.x, p.y, p.name, player_colour, image=False)
                elif p.name[0] == "R":
                    new_piece = Rook.Rook(p.x, p.y, p.name, player_colour, image=False)
                elif p.name[0] == "N":
                    new_piece = Knight.Knight(p.x, p.y, p.name, player_colour, image=False)
                elif p.name[0] == "B":
                    new_piece = Bishop.Bishop(p.x, p.y, p.name, player_colour, image=False)
                elif p.name[0] == "P":
                    new_piece = Pawn.Pawn(p.x, p.y, p.name, player_colour, image=False)
                elif p.name[0] == "K":
                    new_piece = King.King(p.x, p.y, p.name, player_colour, image=False)
                self.piece_dict[chr(p.x + 97) + str(p.y + 1)] = new_piece
                self.piece_list.add(new_piece)
        else:
            self.piece_dict = piece_dict
            self.piece_list = piece_list.copy()
        self.move_counter = deepcopy(move_counter)
        self.past_boards = deepcopy(past_boards)
        if len(self.history) % 2 == 0:
            self.first_player = "w"
        else:
            self.first_player = "b"
        self.castle_kingside = deepcopy(castle_kingside)
        self.castle_queenside = deepcopy(castle_queenside)
        self.king_loc = deepcopy(king_loc)
        self.player_colour = player_colour
        self.image = image
        self.bitboard_indices = {
            'Pw': 0,
            'Nw': 1,
            'Bw': 2,
            'Rw': 3,
            'Qw': 4,
            'Kw': 5,
            'Pb': 6,
            'Nb': 7,
            'Bb': 8,
            'Rb': 9,
            'Qb': 10,
            'Kb': 11
        }
        random.seed(0.5)
        self.piece_hash_table = [[random.getrandbits(64) for i in range(64)] for j in range(12)]
        self.hash = 0
        for item in self.piece_list:
            self.hash ^= self.piece_hash_table[self.bitboard_indices[item.name]][item.x + 8*item.y]
        random.seed(time.time())

    # returns -1 if it's checkmate for black, 1 for white and 0 for a draw
    def terminal(self):
        moves = self.legal_moves()
        # checkmate and stalemate
        if len(moves) == 0:
            in_check, _ = BaP.in_check(self.to_play(), self.board, self.king_loc)
            if in_check:
                return -1 if self.to_play() == 'w' else 1
            return 0
        # draws other than stalemate
        elif self.move_counter >= 50 or Game_enders.draw_by_lack_of_material(self.piece_list) or\
                Game_enders.comp_past_boards(self.past_boards, self.board):
            return 0
        return None

    def clone(self, image):
        return Game(self.piece_dict, self.piece_list, self.board, self.past_boards, self.castle_kingside,
                    self.castle_queenside, self.player_colour, self.king_loc, self.move_counter, self.history, image)

    # function which returns all the legal moves in the position
    def legal_moves(self):
        legal_moves = []
        pawn_direction = 1 if self.to_play() == "w" else -1
        # gets the moves for each of the pieces
        for p in self.piece_list:
            if p.colour == self.to_play():
                for move in p.get_moves(self.board):
                    if p.name[0] == "P" and (move[3] == "1" or move[3] == "8"):
                        legal_moves.append(move + "Q")
                        legal_moves.append(move + "R")
                        legal_moves.append(move + "B")
                        legal_moves.append(move + "N")
                    else:
                        legal_moves.append(move)

        # gets possible castling options in the position
        y_pos = "1" if self.to_play() == "w" else "8"
        castling_legality = BaP.castling_legality(self)
        if castling_legality[1]:
            legal_moves.append("e" + y_pos + "g" + y_pos)
        if castling_legality[0]:
            legal_moves.append("e" + y_pos + "c" + y_pos)

        # adds possible en-passant moves
        if len(self.history) > 0 and abs(int(self.history[-1][1]) - int(self.history[-1][3])) == 2:
            last_move = [BaP.un_translate(self.history[-1][0]), int(self.history[-1][1]) - 1,
                         BaP.un_translate(self.history[-1][2]), int(self.history[-1][3]) - 1]
            # checks for possible en passant to the right
            if self.board[last_move[2]][last_move[3]][0] == "P" and last_move[2] != 7:
                if self.board[last_move[2] + 1][last_move[3]] == "P" + self.to_play():
                    legal_moves.append(BaP.translate_coordinates(last_move[2] + 1, last_move[3], last_move[2],
                                                                 last_move[3] + pawn_direction))
            # checks for possible en passant to the left
            if self.board[last_move[2]][last_move[3]][0] == "P" and last_move[2] != 0:
                if self.board[last_move[2] - 1][last_move[3]] == "P" + self.to_play():
                    legal_moves.append(BaP.translate_coordinates(last_move[2] - 1, last_move[3], last_move[2],
                                                                 last_move[3] + pawn_direction))

        previous_checks = []
        i = 0
        # loops through the moves found to check if after any of them the player is in check
        while i < len(legal_moves):
            p = self.piece_dict[legal_moves[i][:2]]
            move = [BaP.un_translate(legal_moves[i][0]), int(legal_moves[i][1]) - 1,
                    BaP.un_translate(legal_moves[i][2]), int(legal_moves[i][3]) - 1]
            if p != " ":
                in_check = False
                self.board[move[0]][move[1]] = " "

                # check has already been looked for in the castling_legality subroutine
                if p.name[0] == "K" and abs(move[2] - move[0]) == 2:
                    self.board[move[0]][move[1]] = p.name

                # accounts for en-passant
                elif p.name[0] == "P" and abs(move[2] - move[0]) == 1 and self.board[move[2]][move[3]] == " ":
                    # changes the board
                    self.board[move[2]][move[3]] = p.name
                    piece_taken = self.board[move[2]][move[1]]
                    self.board[move[2]][move[1]] = " "

                    # looks for check
                    if previous_checks:
                        in_check = BaP.still_in_check(previous_checks, self.board, self.to_play(), self.king_loc)

                    if not in_check:
                        in_check, checking_move = BaP.in_check(self.to_play(), self.board, self.king_loc)
                        if checking_move is not None:
                            previous_checks.append(checking_move)

                    # replaces the piece
                    self.board[move[2]][move[3]] = " "
                    self.board[move[2]][move[1]] = piece_taken
                    self.board[move[0]][move[1]] = p.name
                else:
                    piece_taken = self.board[move[2]][move[3]]
                    self.board[move[2]][move[3]] = p.name

                    # changes the king's location
                    if p.name[0] == "K":
                        self.king_loc[0 if self.to_play() == "w" else 1] = {0: move[2], 1: move[3]}

                    # checks if the king is in check
                    if previous_checks:
                        in_check = BaP.still_in_check(previous_checks, self.board, self.to_play(), self.king_loc)

                    if not in_check:
                        in_check, checking_move = BaP.in_check(self.to_play(), self.board, self.king_loc)
                        if checking_move is not None:
                            previous_checks.append(checking_move)
                            
                    # changes the king's location back
                    if p.name[0] == "K":
                        self.king_loc[0 if self.to_play() == "w" else 1] = {0: move[0], 1: move[1]}

                    self.board[move[2]][move[3]] = piece_taken
                    self.board[move[0]][move[1]] = p.name

                # removes the move if in check after it
                if in_check:
                    legal_moves.pop(i)
                    i -= 1
            else:
                legal_moves.pop(i)
                i -= 1
            i += 1

        return legal_moves

    # same as apply, but without the extra luggage of having to return any information for undoing or showing the move
    def apply_efficient(self, move):
        self.move_counter += 0.5
        captured = False
        castled = False
        int_move = [BaP.un_translate(move[0]), int(move[1]) - 1, BaP.un_translate(move[2]), int(move[3]) - 1]
        p = self.piece_dict[move[:2]]
        if p != " ":
            self.hash ^= self.piece_hash_table[self.bitboard_indices[p.name]][int_move[2] + 8*int_move[3]]
            # applies castling
            if p.name[0] == "K" and abs(int_move[2] - int_move[0]) == 2:
                castled = True
                self.board[3 if int_move[2] == 2 else 5][int_move[3]] = "R" + p.name[-1]
                self.board[0 if int_move[2] == 2 else 7][int_move[3]] = " "
                try:
                    if int_move[2] == 2:
                        p2 = self.piece_dict["a" + move[1]]
                        p2.x = 3
                        self.piece_dict["a" + move[1]] = " "
                        self.piece_dict["d" + move[1]] = p2
                    elif int_move[2] == 6:
                        p2 = self.piece_dict["h" + move[1]]
                        p2.x = 5
                        self.piece_dict["h" + move[1]] = " "
                        self.piece_dict["f" + move[1]] = p2

                except AttributeError:
                    print(self.board)
                    print(move)
                    print(self.history)
                    raise ValueError

            # applies en passant
            elif p.name[0] == "P" and abs(int_move[2] - int_move[0]) == 1 and \
                    self.board[int_move[2]][int_move[3]] == " ":
                captured = True
                self.board[int_move[2]][int_move[1]] = " "
                p2 = self.piece_dict[move[2] + move[1]]
                self.piece_list.remove(p2)
                self.piece_dict[move[2] + move[1]] = " "

            # applies pawn promotion
            elif p.name[0] == "P" and (int_move[3] == 7 or int_move[3] == 0):
                self.board[int_move[2]][int_move[3]] = move[4] + p.colour
                self.piece_list.remove(p)
                if move[4] == "B":
                    p = Bishop.Bishop(int_move[0], int_move[1], "B" + self.to_play(), self.player_colour,
                                      image=self.image)
                elif move[4] == "N":
                    p = Knight.Knight(int_move[0], int_move[1], "N" + self.to_play(), self.player_colour,
                                      image=self.image)
                elif move[4] == "R":
                    p = Rook.Rook(int_move[0], int_move[1], "R" + self.to_play(), self.player_colour,
                                  image=self.image)
                else:
                    p = Queen.Queen(int_move[0], int_move[1], "Q" + self.to_play(), self.player_colour,
                                    image=self.image)

                self.piece_list.add(p)

            # moves the piece object and removes the object of the piece taken
            self.board[int_move[2]][int_move[3]] = p.name
            self.board[p.x][p.y] = " "
            p.x = int_move[2]
            p.y = int_move[3]
            p2 = self.piece_dict[move[2:4]]
            if p2 != " ":
                captured = True
                self.piece_list.remove(p2)
            self.piece_dict[move[:2]] = " "
            self.piece_dict[move[2:4]] = p

            # stops the king from castling in the future if he or a rook has already moved,
            # as well as if a rook gets captured
            index = 0 if self.to_play() == "w" else 1
            if p.name[0] == "K":
                self.castle_queenside[index] = False
                self.castle_kingside[index] = False

                # updates the king's position
                self.king_loc[index] = {0: p.x, 1: p.y}
            elif p.name[0] == "R":
                if int_move[0] == 7:
                    self.castle_kingside[index] = False
                elif int_move[0] == 0:
                    self.castle_queenside[index] = False
            if p2 != ' ' and p2.name[0] == 'R':
                if (p2.y == 0 and p2.colour == 'w') or (p2.y == 7 and p2.colour == 'b'):
                    if p2.x == 7:
                        self.castle_kingside[1 - index] = False
                    elif p2.x == 0:
                        self.castle_queenside[1 - index] = False

            # sets the counter for moves with no progress to 0 if a pawn move has been moved or a piece has been
            # captured and updates the past boards list
            if p.name[0] == "P" or captured or castled:
                self.move_counter = 0
                self.past_boards = [deepcopy(self.board)]
            else:
                self.past_boards.append(deepcopy(self.board))
        else:
            print('uh oh')
            print(self.board)
            print(self.piece_dict)
            print(self.history)
            print(move)

        # updates the history
        self.history.append(move)

    # applies a given move to the game
    def apply(self, move):
        prev_counter = self.move_counter
        self.move_counter += 0.5
        captured = False
        castled = False
        en_passant = False
        captured_piece = " "
        castling_change = [[False, False], [False, False]]
        prev_past_boards = deepcopy(self.past_boards)
        promoted_pawn = ' '
        int_move = [BaP.un_translate(move[0]), int(move[1]) - 1, BaP.un_translate(move[2]), int(move[3]) - 1]
        p = self.piece_dict[move[:2]]
        if p != " ":
            self.hash ^= self.piece_hash_table[self.bitboard_indices[p.name]][int_move[2] + 8 * int_move[3]]
            # applies castling
            if p.name[0] == "K" and abs(int_move[2] - int_move[0]) == 2:
                castled = True
                self.board[3 if int_move[2] == 2 else 5][int_move[3]] = "R" + p.name[-1]
                self.board[0 if int_move[2] == 2 else 7][int_move[3]] = " "
                if int_move[2] == 2:
                    p2 = self.piece_dict["a" + move[1]]
                    p2.x = 3
                    self.piece_dict["a" + move[1]] = " "
                    self.piece_dict["d" + move[1]] = p2
                elif int_move[2] == 6:
                    p2 = self.piece_dict["h" + move[1]]
                    p2.x = 5
                    self.piece_dict["h" + move[1]] = " "
                    self.piece_dict["f" + move[1]] = p2

            # applies en passant
            elif p.name[0] == "P" and abs(int_move[2] - int_move[0]) == 1 and \
                    self.board[int_move[2]][int_move[3]] == " ":
                captured = True
                en_passant = True
                self.board[int_move[2]][int_move[1]] = " "
                p2 = self.piece_dict[move[2] + move[1]]
                self.piece_list.remove(p2)
                self.piece_dict[move[2] + move[1]] = " "
                captured_piece = p2

            # applies pawn promotion
            elif p.name[0] == "P" and (int_move[3] == 7 or int_move[3] == 0):
                self.board[int_move[2]][int_move[3]] = move[4] + p.colour
                promoted_pawn = p
                self.piece_list.remove(p)
                if move[4] == "B":
                    p = Bishop.Bishop(int_move[0], int_move[1], "B" + self.to_play(), self.player_colour,
                                      image=self.image)
                elif move[4] == "N":
                    p = Knight.Knight(int_move[0], int_move[1], "N" + self.to_play(), self.player_colour,
                                      image=self.image)
                elif move[4] == "R":
                    p = Rook.Rook(int_move[0], int_move[1], "R" + self.to_play(), self.player_colour,
                                  image=self.image)
                else:
                    p = Queen.Queen(int_move[0], int_move[1], "Q" + self.to_play(), self.player_colour,
                                    image=self.image)

                self.piece_list.add(p)

            # moves the piece object and removes the object of the piece taken
            self.board[int_move[2]][int_move[3]] = p.name
            self.board[p.x][p.y] = " "
            p.x = int_move[2]
            p.y = int_move[3]
            p2 = self.piece_dict[move[2:4]]
            if p2 != " ":
                captured = True
                self.piece_list.remove(p2)
                captured_piece = p2
            self.piece_dict[move[:2]] = " "
            self.piece_dict[move[2:4]] = p

            # stops the king from castling in the future if he or a rook has already moved
            index = 0 if self.to_play() == "w" else 1
            if p.name[0] == "K":
                if self.castle_queenside[index]:
                    self.castle_queenside[index] = False
                    castling_change[index][0] = True
                if self.castle_kingside[index]:
                    self.castle_kingside[index] = False
                    castling_change[index][1] = True

                # updates the king's position
                self.king_loc[index] = {0: p.x, 1: p.y}
            elif p.name[0] == "R":
                if self.castle_kingside[index] and int_move[0] == 7:
                    self.castle_kingside[index] = False
                    castling_change[index][1] = True
                elif self.castle_queenside[index] and int_move[0] == 0:
                    self.castle_queenside[index] = False
                    castling_change[index][0] = True
            if p2 != ' ' and p2.name[0] == 'R':
                if (p2.y == 0 and p2.colour == 'w') or (p2.y == 7 and p2.colour == 'b'):
                    if p2.x == 7 and self.castle_kingside[1 - index]:
                        self.castle_kingside[1 - index] = False
                        castling_change[1 - index][1] = True
                    elif p2.x == 0 and self.castle_queenside[1 - index]:
                        self.castle_queenside[1 - index] = False
                        castling_change[1 - index][0] = True

            # sets the counter for moves with no progress to 0 if a pawn move has been moved or a piece has been
            # captured and updates the past boards list
            if p.name[0] == "P" or captured or castled:
                self.move_counter = 0
                self.past_boards = [deepcopy(self.board)]
            else:
                self.past_boards.append(deepcopy(self.board))

        # updates the history
        self.history.append(move)
        return captured_piece, p, en_passant, castling_change, prev_counter, prev_past_boards, promoted_pawn

    # reverses the effect of the apply function
    def un_apply(self, move, piece_taken, en_passant, castling_change, prev_counter, prev_past_boards, promoted_pawn):
        # updates the history first so that the to_play function returns the correct value
        self.history = self.history[:-1]
        int_move = [BaP.un_translate(move[0]), int(move[1]) - 1, BaP.un_translate(move[2]), int(move[3]) - 1]

        p = self.piece_dict[move[2:4]]
        self.hash ^= self.piece_hash_table[self.bitboard_indices[p.name]][int_move[2] + 8*int_move[3]]
        if p != " ":
            # undoes castling
            if p.name[0] == "K" and abs(int_move[2] - int_move[0]) == 2:
                self.board[3 if int_move[2] == 2 else 5][int_move[3]] = " "
                self.board[0 if int_move[2] == 2 else 7][int_move[3]] = "R" + p.name[-1]
                if int_move[2] == 2:
                    p2 = self.piece_dict["d" + move[1]]
                    p2.x = 0
                    self.piece_dict["d" + move[1]] = " "
                    self.piece_dict["a" + move[1]] = p2
                elif int_move[2] == 6:
                    p2 = self.piece_dict["f" + move[1]]
                    p2.x = 7
                    self.piece_dict["f" + move[1]] = " "
                    self.piece_dict["h" + move[1]] = p2

            # undoes en passant
            elif en_passant:
                self.board[int_move[2]][int_move[1]] = piece_taken.name
                self.piece_dict[move[2] + move[1]] = piece_taken
                self.piece_list.add(piece_taken)
                piece_taken = ' '

            # undoes pawn promotion
            elif len(move) == 5:
                self.piece_list.remove(p)
                p = promoted_pawn
                try:
                    self.piece_list.add(p)
                except RecursionError:
                    print(p)
                    print(move)

            # moves the piece object and removes the object of the piece taken
            self.board[int_move[0]][int_move[1]] = p.name
            self.board[int_move[2]][int_move[3]] = piece_taken if piece_taken == " " else piece_taken.name
            p.x = int_move[0]
            p.y = int_move[1]
            if piece_taken != " ":
                self.piece_list.add(piece_taken)
            self.piece_dict[move[:2]] = p
            self.piece_dict[move[2:4]] = piece_taken

            # resets the legality of castling to what it was before
            for i in range(2):
                if castling_change[i][0]:
                    self.castle_queenside[i] = True
                if castling_change[i][1]:
                    self.castle_kingside[i] = True

            index = 0 if self.to_play() == "w" else 1
            if p.name[0] == "K":
                self.king_loc[index] = {0: p.x, 1: p.y}

            # resets the past boards and the counter
            self.past_boards = prev_past_boards
            self.move_counter = prev_counter

    # makes an image of the game which can be passed into the neural network
    def make_image(self):
        # creates a template full bitboard and the input planes for the number of moves with no progress and the total
        # number of moves in the game
        full_board = ones((8, 8))
        move_counter = full((8, 8), self.move_counter)
        total_moves = full((8, 8), len(self.history))

        # initialises the output image to all zeros
        output = zeros((21, 8, 8))

        # finds the locations of the pieces on the board and encodes them in the input image
        # the values dictionary holds the index of the input plane for each piece and what the piece is stored as
        piece_squares = BaP.find_pieces(self.board)
        values = {"Pw": 0, "Pb": 1, "Bw": 2, "Bb": 3, "Nw": 4, "Nb": 5, "Rw": 6,
                  "Rb": 7, "Qw": 8, "Qb": 9, "Kw": 10, "Kb": 11}
        for key in values.keys():
            for square in piece_squares[key]:
                output[values[key]][square[0]][square[1]] = 1

        # adds the repetition count of the position
        repetition_count = 0
        for board in self.past_boards:
            if board == self.board:
                repetition_count += 1
        if repetition_count == 1:
            output[12] = full_board
        else:
            output[13] = full_board

        # adds castling values
        if self.castle_kingside[0]:
            output[14] = full_board
        if self.castle_kingside[1]:
            output[15] = full_board
        if self.castle_queenside[0]:
            output[16] = full_board
        if self.castle_queenside[1]:
            output[17] = full_board

        # adds the colour of the current player
        if self.to_play() == "w":
            output[18] = full_board

        # adds values for the number of moves played so far and the number of moves without progress
        output[19] = move_counter
        output[20] = total_moves
        return output

    # function which returns the position of a particular move, as output by the neural network, used in make_move_dict
    # to convert neural network output to an actual move
    def move_pos(self, move):
        int_move = [BaP.un_translate(move[0]), int(move[1]) - 1, BaP.un_translate(move[2]), int(move[3]) - 1]

        x = int_move[2] - int_move[0]
        y = int_move[3] - int_move[1]
        x_dir = 0 if x == 0 else x // abs(x)
        y_dir = 0 if y == 0 else y // abs(y)
        if len(move) == 4 or move[-1] == 'Q':
            # loc gives the location of the piece on the board, which is flipped for black
            loc = []
            for item in int_move:
                loc.append(item if self.to_play() == 'w' else (7 - item))

            # adds queen moves
            if x == 0 or y == 0 or abs(x) == abs(y):
                directions = {'01': 0, '0-1': 1, '10': 2, '-10': 3, '11': 4, '-11': 5, '1-1': 6, '-1-1': 7}
                direction = directions[str(x_dir) + str(y_dir)]
                if x != 0:
                    pos = [direction * 7 + abs(x), loc[0], loc[1]]
                else:
                    pos = [direction * 7 + abs(y), loc[0], loc[1]]
            # adds knight moves
            elif abs(x)/abs(y) == 2 or abs(y)/abs(x) == 2:
                directions = {'21': 0, '12': 1, '-12': 2, '-21': 3, '-2-1': 4, '-1-2': 5, '1-2': 6, '2-1': 7}
                direction = directions[str(x) + str(y)]
                pos = [56 + direction, loc[0], loc[1]]
            # catches bad inputs
            else:
                pos = [1, 0, 0]  # impossible move
                print('Wrong input to move_pos')
                print('Move:', move)
                print('x:', x, 'y:', y)
                print('x_dir:', x_dir, 'y_dir', y_dir)

        # promoting moves
        else:
            index = 64
            if move[-1] == "B":
                index += 3
            elif move[-1] == "R":
                index += 6

            if x == 0:
                index += 1
            elif x == 1 != (self.to_play() == "b"):
                index += 2

            if self.to_play() == "w":
                pos = [index, int_move[0], int_move[1]]
            else:
                pos = [index, 7 - int_move[0], 7 - int_move[1]]
        return pos

    # returns the colour of the current player
    def to_play(self):
        if len(self.history) % 2 == 0:
            return "w"
        else:
            return "b"

    def fen(self):
        current_whitespace = 0
        fen = ''
        # encodes board
        for i in range(len(self.board)):
            for j in range(len(self.board)):
                piece = self.board[j][7 - i]
                if piece == ' ':
                    current_whitespace += 1
                else:
                    if current_whitespace > 0:
                        fen += str(current_whitespace)
                        current_whitespace = 0
                    if piece[-1] == 'w':
                        fen += piece[0]
                    else:
                        fen += piece[0].lower()
            if current_whitespace != 0:
                fen += str(current_whitespace)
                current_whitespace = 0
            if i != len(self.board) - 1:
                fen += '/'

        # encodes player to move
        fen += ' ' + self.to_play() + ' '

        # encodes castling
        if self.castle_kingside[0]:
            fen += 'K'
        if self.castle_queenside[0]:
            fen += 'Q'
        if not self.castle_kingside[0] and not self.castle_queenside[0]:
            fen += '-'
        if self.castle_kingside[1]:
            fen += 'k'
        if self.castle_queenside[1]:
            fen += 'q'
        if not self.castle_kingside[1] and not self.castle_queenside[1]:
            fen += '-'
        fen += ' '

        # encodes en-passant (the encoding is just the square to which the pawn could potentially take if there
        # is one there)
        try:
            if self.piece_dict[self.history[-1][2:4]].name[0] == 'P' and \
                    abs(int(self.history[-1][3]) - int(self.history[-1][1])) == 2:
                fen += self.history[-1][0] + str(int((int(self.history[-1][1]) + int(self.history[-1][3]))//2))
            else:
                fen += '-'
        except IndexError:
            fen += '-'

        # adds no progress counter
        fen += ' ' + str(int(self.move_counter * 2)) + ' '

        # adds number of full moves played
        fen += str(len(self.history)//2 + 1)

        return fen
