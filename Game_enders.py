import Bits_and_Pieces as BaP


# checks for checkmate
def checkmate(game, colour):
    in_check, checking_move = BaP.in_check(colour, game.board, game.king_loc)
    previous_checks = [checking_move]
    if in_check:
        # loops through pieces of the same colour
        for p in game.piece_list:
            if p.name[-1] == colour:

                moves = p.get_moves(game.board)

                # loops through the possible moves of the piece to check if after any of them it is still in check
                for move in moves:
                    int_move = [BaP.un_translate(move[0]), int(move[1]) - 1, BaP.un_translate(move[2]),
                                int(move[3]) - 1]
                    # moves piece
                    game.board[int_move[0]][int_move[1]] = " "
                    piece_taken = game.board[int_move[2]][int_move[3]]
                    game.board[int_move[2]][int_move[3]] = p.name
                    if p.name[0] == "K":
                        game.king_loc[0 if p.name[-1] == "w" else 1] = {0: int_move[2], 1: int_move[3]}

                    # looks for check
                    in_check = BaP.still_in_check(previous_checks, game.board, colour, game.king_loc)

                    if not in_check:
                        in_check, checking_move = BaP.in_check(colour, game.board, game.king_loc)
                        previous_checks.append(checking_move)

                    # returns the board position to the original
                    game.board[int_move[2]][int_move[3]] = piece_taken
                    game.board[int_move[0]][int_move[1]] = p.name
                    if p.name[0] == "K":
                        game.king_loc[0 if p.name[-1] == "w" else 1] = {0: int_move[0], 1: int_move[1]}

                    if not in_check:
                        return False
        return True
    return False


# checks for a draw by stalemate
def stalemate(game, colour):
    in_check, checking_move = BaP.in_check(colour, game.board, game.king_loc)
    previous_checks = []
    if in_check:
        return False

    # loops through pieces of the same colour
    for p in game.piece_list:
        if p.name[-1] == colour:
            moves = p.get_moves(game.board)

            # loops through the possible moves of the piece to check if after any of them it is in check
            for move in moves:
                int_move = [BaP.un_translate(move[0]), int(move[1]) - 1, BaP.un_translate(move[2]),
                            int(move[3]) - 1]
                # moves piece
                game.board[int_move[0]][int_move[1]] = " "
                piece_taken = game.board[int_move[2]][int_move[3]]
                game.board[int_move[2]][int_move[3]] = p.name
                if p.name[0] == "K":
                    game.king_loc[0 if p.name[-1] == "w" else 1] = {0: int_move[2], 1: int_move[3]}

                # looks for check
                if previous_checks:
                    in_check = BaP.still_in_check(previous_checks, game.board, colour, game.king_loc)

                if not in_check:
                    in_check, checking_move = BaP.in_check(colour, game.board, game.king_loc)
                    previous_checks.append(checking_move)

                # returns the board position to the original
                game.board[int_move[2]][int_move[3]] = piece_taken
                game.board[int_move[0]][int_move[1]] = p.name
                if p.name[0] == "K":
                    game.king_loc[0 if p.name[-1] == "w" else 1] = {0: p.x, 1: p.y}

                # if a move can be made without being in check, then it isn't stalemate
                if not in_check:
                    return False
    return True


# checks for a draw by lack of material
def draw_by_lack_of_material(piece_list):
    if len(piece_list) >= 5:
        return False

    minor_pieces = [0, 0]

    for p in piece_list:
        # it is possible to checkmate with at least one queen, at least one rook or at least one pawn
        if p.name[0] == 'Q' or p.name[0] == 'R' or p.name[0] == 'P':
            return False
        # it is possible to checkmate with at least two minor pieces
        elif p.name[0] == 'B' or p.name[0] == 'N':
            minor_pieces[0 if p.name[-1] == 'w' else 1] += 1
            if minor_pieces[0] == 2 or minor_pieces[1] == 2:
                return False
    return True


# compares past boards in order to detect draw by repetition
def comp_past_boards(past_boards, board):
    same_boards = 0

    # loops through all the past boards, comparing them to the current one
    for past_board in past_boards:
        if past_board == board:
            same_boards += 1

    if same_boards > 2:
        return True
    else:
        return False
