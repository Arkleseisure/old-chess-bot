import Bits_and_Pieces as BaP
import pygame
from queue import PriorityQueue
import time
import math
from numpy.random import normal


class Node:
    def __init__(self, to_play):
        self.to_play = to_play
        self.children = {}
        self.value = -1e6 if to_play == "w" else 1e6


def minimax(game, depth, return_button_group, config, start_time, search_time, node=None, current_depth=1,
            total_nodes=0, alpha=-1e6, beta=1e6, transposition_table=None):
    if transposition_table is None:
        transposition_table = {}
    values = {' ': 0, 'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 10}
    total_nodes += 1
    multiplier = 1 if game.to_play() == 'w' else -1
    evaluated = False

    if not node:
        node = Node(game.to_play())
        game = game.clone(False)

    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            for button in return_button_group:
                if button.is_clicked(mouse_x, mouse_y):
                    return node, "----", True, total_nodes, False

    moves = game.legal_moves()

    if depth == 0 and BaP.in_check(game.to_play(), game.board, game.king_loc)[0]:
        depth = 1

    # the transposition table holds information about positions which have already been searched.
    # If that position is hit again through a different move order, this should find it and
    # prevent it being searched again
    if game.hash in transposition_table.keys() and current_depth != 1 and\
                current_depth + depth <= transposition_table[game.hash]['depth']:
            node.value = transposition_table[game.hash]['value']
            depth = 0
            evaluated = True

    if depth == 0:
        if not evaluated:
            value = evaluate(game, depth, None, config)
            node.value = value
            evaluated = True
        else:
            value = node.value
        '''
        Alpha-Beta pruning... This part assumes that the best move if it is not quiet will improve the position of the 
        player and the evaluation after the move will therefore be better for the current player. 
        This can be taken advantage of to improve the efficiency of the search.
        '''
        if (value < alpha and node.to_play == "b") or (value > beta and node.to_play == "w"):
            node.value = value
            return node, [], False, total_nodes, True

        # quiescence search
        new_moves = []
        for move in moves:
            int_move = [BaP.un_translate(move[0]), int(move[1]) - 1, BaP.un_translate(move[2]), int(move[3]) - 1]
            # expands the tree if the move takes a piece of greater value or is overloading an opposition piece
            if values[game.board[int_move[0]][int_move[1]][0]] < values[game.board[int_move[2]][int_move[3]][0]] or \
                    is_overloaded(game.board, [int_move[2], int_move[3]]):
                depth = 1
                new_moves.append(move)
        moves = new_moves

    value = game.terminal()
    if depth > 0 and value is None:
        # move ordering
        move_queue = PriorityQueue()
        for move in moves:
            if move in node.children.keys():
                move_queue.put((-node.children[move].value * multiplier, move))
            else:
                node.children[move] = Node(BaP.opposite(node.to_play))
                taken = game.piece_dict[move[2:4]]
                moved = game.piece_dict[move[:2]]
                if taken == " ":
                    move_queue.put((20, move))
                else:
                    move_queue.put((10 - (values[taken.name[0]] - values[moved.name[0]]), move))

        move = None
        search_path = []
        while not move_queue.empty():
            child = move_queue.get()[1]
            # applies the moves, searches the child node then undoes the move
            piece_taken, _, en_passant, castling_change, prev_counter, prev_past_boards, promoted_pawn = game.apply(child)
            child_node, node_search_path, quit_code, total_nodes, fully_searched = \
                minimax(game, depth - 1, return_button_group, config, start_time,
                        search_time, node=node.children[child], current_depth=current_depth + 1,
                        total_nodes=total_nodes, alpha=alpha, beta=beta, transposition_table=transposition_table)
            value = child_node.value
            transposition_table[game.hash] = {'depth': current_depth + depth, 'value': child_node.value}
            if quit_code:
                return node, "----", True, total_nodes, False
            game.un_apply(child, piece_taken, en_passant, castling_change, prev_counter, prev_past_boards,
                          promoted_pawn)
            # applies minimax
            if ((node.to_play == "w" and value > node.value) or (node.to_play == "b" and value < node.value) or
                move is None) and fully_searched:

                node.value = value
                # alpha beta pruning
                if (value < alpha and node.to_play == "b") or (value > beta and node.to_play == "w"):
                    return node, [], False, total_nodes, True
                move = child
                search_path = node_search_path
                if node.to_play == 'w':
                    alpha = value
                else:
                    beta = value

            if time.time() > start_time + search_time:
                search_path.insert(0, move)
                return node, search_path, False, total_nodes, False

        search_path.insert(0, move)
        return node, search_path, False, total_nodes, True
    else:
        if not evaluated:
            node.value = evaluate(game, depth, value, config)
        if current_depth == 1:
            print('wtf')
        return node, [], False, total_nodes, True


def evaluate(game, depth, value, config):
    # looks for a terminal state... the depth factor is included to encourage it to go for a mate
    # in the smallest number of moves it can
    if value is not None:
        return 1000 * value * (depth + 1)

    # evaluates material difference
    white_value = 0
    black_value = 0
    bishops = [0, 0]
    pawns = 0
    value = 0
    max_material = config['values']['P'] * 16 + config['values']['N'] * 4 + config['values']['B'] * 4 + \
                   config['values']['R'] * 4 + config['values']['Q'] * 2 + config['values']['K'] * 2
    total_material = sum(config['values'][p.name[0]] for p in game.piece_list)
    material_frac = total_material/max_material
    endgame = len(game.piece_list) <= 12
    loc = 1 if endgame else 0
    for p in game.piece_list:
        other_pawn = 'P' + BaP.opposite(p.name[-1])
        if p.name[-1] == 'w':
            multiplier = 1
            white_value += config['values'][p.name[0]]
        else:
            multiplier = -1
            black_value += config['values'][p.name[0]]

        if p.name[0] == 'B':
            bishops[multiplier] += 1

        # stops the engine from bringing out the queen at the beginning of the game.
        elif p.name[0] == 'Q' and len(game.history) <= 20:
            if p.x != 3 or p.y != 3.5 - 3.5 * multiplier:
                value -= (21 - len(game.history)) * multiplier * config['qbg']

        # factor for king protection
        elif p.name[0] == 'K' and not endgame:
            pawn_shield = 0
            attacker_proximity = 0
            for i in range(3):
                x = p.x + i - 1
                if -1 < x < 8:
                    # adds value for having a pawn shield
                    if -1 < p.y + multiplier < 8 and game.board[x][p.y + multiplier] == 'P' + p.colour:
                        pawn_shield += 1

                    # takes away for opposing pieces attacking the king
                    y = p.y
                    blocked = False
                    while 0 < y < 7:
                        if game.board[x][y] == other_pawn:
                            attacker_proximity += 8 - abs(y - p.y)
                            blocked = True
                        elif game.board[x][y] == 'R' + BaP.opposite(p.name[-1]) or \
                                game.board[x][y][0] == 'Q' + BaP.opposite(p.name[-1]):
                            if blocked:
                                attacker_proximity += 4
                            else:
                                attacker_proximity += 8

                        y += multiplier

            value += pawn_shield * config['king_protec'] * multiplier
            value -= attacker_proximity * config['king_attack'] * multiplier

        # adds a factor for the pawn structure
        elif p.name[0] == "P":
            pawns += 1

            # isolated pawns
            isolated = True
            for i in range(3):
                if (p.x > 0 and game.board[p.x - 1][p.y + i - 1][0] == p.name) or \
                        (p.x < 7 and game.board[p.x + 1][p.y + i - 1][0] == p.name):
                    isolated = False

            # doubled and passed pawns
            passed = True
            doubled = False
            y = p.y + multiplier
            while 0 < y < 7:
                if (p.x > 0 and game.board[p.x - 1][y] == other_pawn) or game.board[p.x][y] == other_pawn or \
                        (p.x < 7 and game.board[p.x + 1][y] == other_pawn):
                    passed = False
                if game.board[p.x][y] == p.name:
                    doubled = True
                y += multiplier

            if doubled:
                value -= config['doubled'][0] * multiplier * material_frac
                value -= config['doubled'][1] * multiplier * (1 - material_frac)
            if isolated:
                value -= config['isolated'][0] * multiplier * material_frac
                value -= config['isolated'][1] * multiplier * (1 - material_frac)
            if passed:
                value += config['passed'][0] * multiplier * material_frac
                value += config['passed'][1] * multiplier * (1 - material_frac)

            # blocked pawns
            if game.board[p.x][p.y + multiplier] != " ":
                value -= config['blocked'][0] * multiplier * material_frac
                value -= config['blocked'][1] * multiplier * (1 - material_frac)

        # adds a factor for the location of the pieces, with the advantageous locations for each piece encoded
        # in the piece-square tables. There are two piece-square tables, one for the middlegame and one for the endgame.
        # These are interpolated between as a function of the quantity of material on the board
        if p.name[-1] == 'w':
            value += material_frac * config['mgpst'][p.name[0]][p.y][p.x] / 100
            value += (1 - material_frac) * config['egpst'][p.name[0]][p.y][p.x] / 100
        else:
            value -= material_frac * config['mgpst'][p.name[0]][7 - p.y][p.x] / 100
            value -= (1 - material_frac) * config['egpst'][p.name[0]][7 - p.y][p.x] / 100

    value += (white_value - black_value) * \
             ((white_value / black_value) if white_value > black_value else (black_value / white_value))

    # adds an advantage for the side with the bishop pair
    if bishops[0] == 2:
        value += config['bishop_pair'][0] * material_frac
        value += config['bishop_pair'][1] * (1 - material_frac)
    if bishops[1] == 2:
        value -= config['bishop_pair'][0] * material_frac
        value -= config['bishop_pair'][1] * (1 - material_frac)

    # encourages the player with more pieces to get the other player's king to the corner
    # and to get their king as close as possible
    if pawns == 0:
        if white_value > black_value:
            value += math.sqrt((game.king_loc[1][0] - 3.5) ** 2 + (game.king_loc[1][1] - 3.5) ** 2)
            value += 8 - math.sqrt((game.king_loc[1][0] - game.king_loc[0][0]) ** 2 +
                                   (game.king_loc[1][1] - game.king_loc[0][1]) ** 2)
        elif black_value > white_value:
            value -= math.sqrt((game.king_loc[0][0] - 3.5) ** 2 + (game.king_loc[0][1] - 3.5) ** 2)
            value -= 8 - math.sqrt((game.king_loc[1][0] - game.king_loc[0][0]) ** 2 +
                                   (game.king_loc[1][1] - game.king_loc[0][1]) ** 2)

    # adds a factor for the mobility of the pieces
    cp_moves = len(game.legal_moves())
    # changes the length of the history, meaning that the legal_moves function returns the moves for the other player
    game.history.append("a0a0")
    np_moves = len(game.legal_moves())
    game.history = game.history[:-1]
    if game.to_play() == "w":
        value += config['mobility'][0] * (cp_moves - np_moves) * material_frac
        value += config['mobility'][1] * (cp_moves - np_moves) * (1 - material_frac)
    else:
        value -= config['mobility'][0] * (cp_moves - np_moves) * material_frac
        value -= config['mobility'][1] * (cp_moves - np_moves) * (1 - material_frac)

    value += normal(0, 0.05)
    return value


# looks for an overload at a particular location, which is where there are more attackers than defenders
def is_overloaded(board, loc):
    if board[loc[0]][loc[1]] == ' ':
        return False
    directions = [{0: 1, 1: 1}, {0: 1, 1: 0}, {0: 1, 1: -1}, {0: 0, 1: 1}, {0: 0, 1: -1}, {0: -1, 1: 1}, {0: -1, 1: 0},
                  {0: -1, 1: -1}]

    white_attackers = 0
    black_attackers = 0

    # all directions are from white's perspective
    for direction in directions:
        i = 1
        looping = True
        x = loc[0] + direction[0]
        y = loc[1] + direction[1]
        while 8 > x > -1 and 8 > y > -1 and looping:
            if board[x][y] != " ":
                looping = False
                piece = board[x][y][0]
                if piece == "Q" or (piece == "B" and direction[0] != 0 and direction[1] != 0) \
                        or (piece == "R" and (direction[0] == 0 or direction[1] == 0)) \
                        or (piece == "K" and i == 1) \
                        or (piece == "P" and i == 1 and direction[0] != 0 and
                            direction[1] == (1 if board[x][y][-1] == "b" else -1)):
                    if board[x][y][-1] == 'w':
                        white_attackers += 1
                    else:
                        black_attackers += 1
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
        piece = board[loc[0] + square[0]][loc[1] + square[1]]
        if piece[0] == "N":
            if piece[1] == 'w':
                white_attackers += 1
            else:
                black_attackers += 1

    if (board[loc[0]][loc[1]][-1] == 'w' and black_attackers > white_attackers) or \
            (board[loc[0]][loc[1]][-1] == 'b' and black_attackers < white_attackers):
        return True
    else:
        return False


# previous version of the minimax function
def old_minimax(game, depth, return_button_group, config, start_time, search_time, node=None, current_depth=1,
                total_nodes=0, alpha=-1e6, beta=1e6, transposition_table=None):
    if transposition_table is None:
        transposition_table = {}
    total_nodes += 1
    values = {' ': 0, 'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 10}
    multiplier = 1 if game.to_play() == 'w' else -1
    hash = game.hash
    evaluated = False

    if not node:
        node = Node(game.to_play())
        game = game.clone(False)

    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            for button in return_button_group:
                if button.is_clicked(mouse_x, mouse_y):
                    return node, "----", True, total_nodes, False

    moves = game.legal_moves()

    if depth == 0 and BaP.in_check(game.to_play(), game.board, game.king_loc)[0]:
        depth = 1

    # the transposition table holds information about positions which have already been searched.
    # If that position is hit again through a different move order, this should find it and
    # prevent it being searched again
    if hash in transposition_table.keys() and current_depth != 1 and \
            current_depth + depth <= transposition_table[hash]['depth']:
        node.value = transposition_table[hash]['value']
        depth = 0
        evaluated = True

    if depth == 0:
        if not evaluated:
            value = old_evaluate(game, depth, None, config)
            node.value = value
            evaluated = True
        else:
            value = node.value
        '''
        Alpha-Beta pruning... This part assumes that the best move if it is not quiet will improve the position of the 
        player and the evaluation after the move will therefore be better for the current player. 
        This can be taken advantage of to improve the efficiency of the search.
        '''
        if (value < alpha and node.to_play == "b") or (value > beta and node.to_play == "w"):
            node.value = value
            return node, [], False, total_nodes, True

        # quiescence search
        new_moves = []
        for move in moves:
            int_move = [BaP.un_translate(move[0]), int(move[1]) - 1, BaP.un_translate(move[2]), int(move[3]) - 1]
            # expands the tree if the move takes a piece of greater value or is overloading an opposition piece
            if values[game.board[int_move[0]][int_move[1]][0]] < values[game.board[int_move[2]][int_move[3]][0]] or \
                    is_overloaded(game.board, [int_move[2], int_move[3]]):
                depth = 1
                new_moves.append(move)
        moves = new_moves

    value = game.terminal()
    if depth > 0 and value is None:
        # move ordering
        move_queue = PriorityQueue()
        for move in moves:
            if move in node.children.keys():
                move_queue.put((-node.children[move].value * multiplier, move))
            else:
                node.children[move] = Node(BaP.opposite(node.to_play))
                taken = game.piece_dict[move[2:4]]
                moved = game.piece_dict[move[:2]]
                if taken == " ":
                    move_queue.put((20, move))
                else:
                    move_queue.put((10 - (values[taken.name[0]] - values[moved.name[0]]), move))

        move = None
        search_path = []
        while not move_queue.empty():
            child = move_queue.get()[1]
            # applies the moves, searches the child node then undoes the move
            piece_taken, _, en_passant, castling_change, prev_counter, prev_past_boards, promoted_pawn = \
                game.apply(child)
            child_node, node_search_path, quit_code, total_nodes, fully_searched = \
                old_minimax(game, depth - 1, return_button_group, config, start_time,
                            search_time, node=node.children[child], current_depth=current_depth + 1,
                            total_nodes=total_nodes, alpha=alpha, beta=beta, transposition_table=transposition_table)
            value = child_node.value
            transposition_table[game.hash] = {'depth': current_depth + depth, 'value': child_node.value}
            if quit_code:
                return node, "----", True, total_nodes, False
            game.un_apply(child, piece_taken, en_passant, castling_change, prev_counter, prev_past_boards,
                          promoted_pawn)
            # applies minimax
            if ((node.to_play == "w" and value > node.value) or (node.to_play == "b" and value < node.value) or
                    move is None) and fully_searched:

                node.value = value
                # alpha beta pruning
                if (value < alpha and node.to_play == "b") or (value > beta and node.to_play == "w"):
                    return node, [], False, total_nodes, True
                move = child
                search_path = node_search_path
                if node.to_play == 'w':
                    alpha = value
                else:
                    beta = value

            if time.time() > start_time + search_time:
                search_path.insert(0, move)
                return node, search_path, False, total_nodes, False

        search_path.insert(0, move)
        return node, search_path, False, total_nodes, True
    else:
        if not evaluated:
            node.value = old_evaluate(game, depth, value, config)
        if current_depth == 1:
            print('wtf')
        return node, [], False, total_nodes, True


# previous version of the evaluate function
def old_evaluate(game, depth, value, config):
    # looks for a terminal state... the depth factor is included to encourage it to go for a mate
    # in the smallest number of moves it can
    if value is not None:
        return 1000 * value * (depth + 1)

    # evaluates material difference
    white_value = 0
    black_value = 0
    bishops = [0, 0]
    pawns = 0
    value = 0

    # material_frac is the fraction of the total possible material on the board,
    # used to interpolate between the opening and endgame
    max_material = config['values']['P'] * 16 + config['values']['N'] * 4 + config['values']['B'] * 4 + \
                   config['values']['R'] * 4 + config['values']['Q'] * 2 + config['values']['K'] * 2
    total_material = sum(config['values'][p.name[0]] for p in game.piece_list)
    material_frac = total_material/max_material
    endgame = len(game.piece_list) <= 12
    loc = 1 if endgame else 0
    for p in game.piece_list:
        other_pawn = 'P' + BaP.opposite(p.name[-1])
        if p.name[-1] == 'w':
            multiplier = 1
            white_value += config['values'][p.name[0]]
        else:
            multiplier = -1
            black_value += config['values'][p.name[0]]

        if p.name[0] == 'B':
            bishops[multiplier] += 1

        # stops the engine from bringing out the queen at the beginning of the game.
        elif p.name[0] == 'Q' and len(game.history) <= 20:
            if p.x != 3 or p.y != 3.5 - 3.5 * multiplier:
                value -= (21 - len(game.history)) * multiplier * config['qbg']

        # factor for king protection
        elif p.name[0] == 'K' and not endgame:
            pawn_shield = 0
            attacker_proximity = 0
            for i in range(3):
                x = p.x + i - 1
                if -1 < x < 8:
                    # adds value for having a pawn shield
                    if -1 < p.y + multiplier < 8 and game.board[x][p.y + multiplier] == 'P' + p.colour:
                        pawn_shield += 1

                    # takes away for opposing pieces attacking the king
                    y = p.y
                    blocked = False
                    while 0 < y < 7:
                        if game.board[x][y] == other_pawn:
                            attacker_proximity += 8 - abs(y - p.y)
                            blocked = True
                        elif game.board[x][y] == 'R' + BaP.opposite(p.name[-1]) or \
                                game.board[x][y][0] == 'Q' + BaP.opposite(p.name[-1]):
                            if blocked:
                                attacker_proximity += 4
                            else:
                                attacker_proximity += 8

                        y += multiplier

            value += pawn_shield * config['king_protec'] * multiplier
            value -= attacker_proximity * config['king_attack'] * multiplier

        # adds a factor for the pawn structure
        elif p.name[0] == "P":
            pawns += 1

            # isolated pawns
            isolated = True
            for i in range(3):
                if (p.x > 0 and game.board[p.x - 1][p.y + i - 1][0] == p.name) or \
                        (p.x < 7 and game.board[p.x + 1][p.y + i - 1][0] == p.name):
                    isolated = False

            # doubled and passed pawns
            passed = True
            doubled = False
            y = p.y + multiplier
            while 0 < y < 7:
                if (p.x > 0 and game.board[p.x - 1][y] == other_pawn) or game.board[p.x][y] == other_pawn or \
                        (p.x < 7 and game.board[p.x + 1][y] == other_pawn):
                    passed = False
                if game.board[p.x][y] == p.name:
                    doubled = True
                y += multiplier

            if doubled:
                value -= config['doubled'][0] * multiplier * material_frac
                value -= config['doubled'][1] * multiplier * (1 - material_frac)
            if isolated:
                value -= config['isolated'][0] * multiplier * material_frac
                value -= config['isolated'][1] * multiplier * (1 - material_frac)
            if passed:
                value += config['passed'][0] * multiplier * material_frac
                value += config['passed'][1] * multiplier * (1 - material_frac)

            # blocked pawns
            if game.board[p.x][p.y + multiplier] != " ":
                value -= config['blocked'][0] * multiplier * material_frac
                value -= config['blocked'][1] * multiplier * (1 - material_frac)

        # adds a factor for the location of the pieces, with the advantageous locations for each piece encoded
        # in the piece-square tables. There are two piece-square tables, one for the middlegame and one for the endgame.
        # These are interpolated between as a function of the quantity of material on the board
        if p.name[-1] == 'w':
            value += material_frac * config['mgpst'][p.name[0]][p.y][p.x] / 100
            value += (1 - material_frac) * config['egpst'][p.name[0]][p.y][p.x] / 100
        else:
            value -= material_frac * config['mgpst'][p.name[0]][7 - p.y][p.x] / 100
            value -= (1 - material_frac) * config['egpst'][p.name[0]][7 - p.y][p.x] / 100

    value += (white_value - black_value) * \
             ((white_value / black_value) if white_value > black_value else (black_value / white_value))

    # adds an advantage for the side with the bishop pair
    if bishops[0] == 2:
        value += config['bishop_pair'][0] * material_frac
        value += config['bishop_pair'][1] * (1 - material_frac)
    if bishops[1] == 2:
        value -= config['bishop_pair'][0] * material_frac
        value -= config['bishop_pair'][1] * (1 - material_frac)

    # encourages the player with more pieces to get the other player's king to the corner
    # and to get their king as close as possible
    if pawns == 0:
        if white_value > black_value:
            value += math.sqrt((game.king_loc[1][0] - 3.5) ** 2 + (game.king_loc[1][1] - 3.5) ** 2)
            value += 8 - math.sqrt((game.king_loc[1][0] - game.king_loc[0][0]) ** 2 +
                                   (game.king_loc[1][1] - game.king_loc[0][1]) ** 2)
        elif black_value > white_value:
            value -= math.sqrt((game.king_loc[0][0] - 3.5) ** 2 + (game.king_loc[0][1] - 3.5) ** 2)
            value -= 8 - math.sqrt((game.king_loc[1][0] - game.king_loc[0][0]) ** 2 +
                                   (game.king_loc[1][1] - game.king_loc[0][1]) ** 2)

    # adds a factor for the mobility of the pieces
    cp_moves = len(game.legal_moves())
    # changes the length of the history, meaning that the legal_moves function returns the moves for the other player
    game.history.append("a0a0")
    np_moves = len(game.legal_moves())
    game.history = game.history[:-1]
    if game.to_play() == "w":
        value += config['mobility'][0] * (cp_moves - np_moves) * material_frac
        value += config['mobility'][1] * (cp_moves - np_moves) * (1 - material_frac)
    else:
        value -= config['mobility'][0] * (cp_moves - np_moves) * material_frac
        value -= config['mobility'][1] * (cp_moves - np_moves) * (1 - material_frac)

    value += normal(0, 0.05)
    return value


# original version of the minimax function from the A-level project
def original_minimax(game, depth, return_button_group, config, start_time, search_time, node=None, current_depth=1,
                     total_nodes=0, alpha=-1e6, beta=1e6):
    total_nodes += 1
    values = {' ': 0, 'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 10}
    multiplier = 1 if game.to_play() == 'w' else -1

    if not node:
        node = Node(game.to_play())
        game = game.clone(False)

    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            for button in return_button_group:
                if button.is_clicked(mouse_x, mouse_y):
                    return node, "----", True, total_nodes, False

    moves = game.legal_moves()

    if depth == 0 and BaP.in_check(game.to_play(), game.board, game.king_loc)[0]:
        depth = 1

    if depth == 0:
        value = original_evaluate(game, depth, None, config)
        '''
        Alpha-Beta pruning... This part assumes that the best move if it is not quiet will improve the position of the 
        player and the evaluation after the move will therefore be better for the current player. 
        This can be taken advantage of to improve the efficiency of the search.
        '''
        if (value < alpha and node.to_play == "b") or (value > beta and node.to_play == "w"):
            node.value = value
            return node, [], False, total_nodes, True

        # quiescence search
        new_moves = []
        for move in moves:
            int_move = [BaP.un_translate(move[0]), int(move[1]) - 1, BaP.un_translate(move[2]), int(move[3]) - 1]
            # expands the tree if the move takes a piece of greater value or is overloading an opposition piece
            if values[game.board[int_move[0]][int_move[1]][0]] < values[game.board[int_move[2]][int_move[3]][0]] or \
                    is_overloaded(game.board, [int_move[2], int_move[3]]):
                depth = 1
                new_moves.append(move)
        moves = new_moves

    value = game.terminal()
    if depth > 0 and value is None:
        # move ordering
        move_queue = PriorityQueue()
        for move in moves:
            if move in node.children.keys():
                move_queue.put((-node.children[move].value * multiplier, move))
            else:
                node.children[move] = Node(BaP.opposite(node.to_play))
                taken = game.piece_dict[move[2:4]]
                moved = game.piece_dict[move[:2]]
                if taken == " ":
                    move_queue.put((20, move))
                else:
                    move_queue.put((10 - (values[taken.name[0]] - values[moved.name[0]]), move))

        move = None
        search_path = []
        while not move_queue.empty():
            child = move_queue.get()[1]
            # applies the moves, searches the child node then undoes the move
            piece_taken, _, en_passant, castling_change, prev_counter, prev_past_boards, promoted_pawn = \
                game.apply(child)
            child_node, node_search_path, quit_code, \
                total_nodes, fully_searched = original_minimax(game, depth - 1, return_button_group, config, start_time,
                                                               search_time, node=node.children[child],
                                                               current_depth=current_depth + 1,
                                                               total_nodes=total_nodes, alpha=alpha, beta=beta)
            value = child_node.value
            if quit_code:
                return node, "----", True, total_nodes, False
            game.un_apply(child, piece_taken, en_passant, castling_change, prev_counter, prev_past_boards,
                          promoted_pawn)
            # applies minimax
            if ((node.to_play == "w" and value > node.value) or (node.to_play == "b" and value < node.value) or
                    move is None) and fully_searched:
                # alpha beta pruning
                if (value < alpha and node.to_play == "b") or (value > beta and node.to_play == "w"):
                    node.value = value
                    return node, [], False, total_nodes, True
                node.value = value
                move = child
                search_path = node_search_path
                if node.to_play == 'w':
                    alpha = value
                else:
                    beta = value

            if time.time() > start_time + search_time:
                search_path.insert(0, move)
                return node, search_path, False, total_nodes, False

        search_path.insert(0, move)
        return node, search_path, False, total_nodes, True
    else:
        node.value = original_evaluate(game, depth, value, config)
        return node, [], False, total_nodes, True


# evaluate function from the original A-level project
def original_evaluate(game, depth, value, config):
    # looks for a terminal state... the depth factor is included to encourage it to go for a mate
    # in the smallest number of moves it can
    if value is not None:
        return 1000 * value * (depth + 1)

    # evaluates material difference
    white_value = 0
    black_value = 0
    bishops = [0, 0]
    pawns = 0
    value = 0
    endgame = len(game.piece_list) <= 12
    loc = 1 if endgame else 0
    for p in game.piece_list:
        other_pawn = 'P' + BaP.opposite(p.name[-1])
        if p.name[-1] == 'w':
            multiplier = 1
            white_value += config['values'][p.name[0]]
        else:
            multiplier = -1
            black_value += config['values'][p.name[0]]

        if p.name[0] == 'B':
            bishops[multiplier] += 1

        # stops the engine from bringing out the queen at the beginning of the game.
        elif p.name[0] == 'Q' and len(game.history) <= 20:
            if p.x != 3 or p.y != 3.5 - 3.5 * multiplier:
                value -= (21 - len(game.history)) * multiplier * config['qbg']

        # factor for king protection
        elif p.name[0] == 'K' and not endgame:
            pawn_shield = 0
            attacker_proximity = 0
            for i in range(3):
                x = p.x + i - 1
                if -1 < x < 8:
                    # adds value for having a pawn shield
                    if -1 < p.y + multiplier < 8 and game.board[x][p.y + multiplier] == 'P' + p.colour:
                        pawn_shield += 1

                    # takes away for opposing pieces attacking the king
                    y = p.y
                    blocked = False
                    while 0 < y < 7:
                        if game.board[x][y] == other_pawn:
                            attacker_proximity += 8 - abs(y - p.y)
                            blocked = True
                        elif game.board[x][y] == 'R' + BaP.opposite(p.name[-1]) or \
                                game.board[x][y][0] == 'Q' + BaP.opposite(p.name[-1]):
                            if blocked:
                                attacker_proximity += 4
                            else:
                                attacker_proximity += 8

                        y += multiplier

            value += pawn_shield * config['king_protec'] * multiplier
            value -= attacker_proximity * config['king_attack'] * multiplier

        # adds a factor for the pawn structure
        elif p.name[0] == "P":
            pawns += 1

            # isolated pawns
            isolated = True
            for i in range(3):
                if (p.x > 0 and game.board[p.x - 1][p.y + i - 1][0] == p.name) or \
                        (p.x < 7 and game.board[p.x + 1][p.y + i - 1][0] == p.name):
                    isolated = False

            # doubled and passed pawns
            passed = True
            doubled = False
            y = p.y + multiplier
            while 0 < y < 7:
                if (p.x > 0 and game.board[p.x - 1][y] == other_pawn) or game.board[p.x][y] == other_pawn or \
                        (p.x < 7 and game.board[p.x + 1][y] == other_pawn):
                    passed = False
                if game.board[p.x][y] == p.name:
                    doubled = True
                y += multiplier

            if doubled:
                value -= config['doubled'][loc] * multiplier
            if isolated:
                value -= config['isolated'][loc] * multiplier
            if passed:
                value += config['passed'][loc] * multiplier

            # blocked pawns
            if game.board[p.x][p.y + multiplier] != " ":
                value -= config['blocked'][loc] * multiplier

        # adds a factor for the location of the pieces, with the advantageous locations for each piece encoded
        # in the piece-square tables
        if endgame:
            value += multiplier * config['egpst'][p.name[0]][p.y if p.name[-1] == 'w' else 7 - p.y][p.x] / 100
        else:
            # in the middle game it is advantageous for the pieces to be in different positions from the endgame
            # p.x stays the same for black as increasing it moves the value more towards the kingside for black as well.
            value += multiplier * config['mgpst'][p.name[0]][p.y if p.name[-1] == 'w' else 7 - p.y][p.x] / 100

    value += (white_value - black_value) * \
             ((white_value / black_value) if white_value > black_value else (black_value / white_value))

    # adds an advantage for the side with the bishop pair
    if bishops[0] == 2:
        value += config['bishop_pair'][loc]
    if bishops[1] == 2:
        value -= config['bishop_pair'][loc]

    # encourages the player with more pieces to get the other player's king to the corner
    # and to get their king as close as possible
    if pawns == 0:
        if white_value > black_value:
            value += math.sqrt((game.king_loc[1][0] - 3.5)**2 + (game.king_loc[1][1] - 3.5)**2)
            value += 8 - math.sqrt((game.king_loc[1][0] - game.king_loc[0][0])**2 +
                                   (game.king_loc[1][1] - game.king_loc[0][1])**2)
        elif black_value > white_value:
            value -= math.sqrt((game.king_loc[0][0] - 3.5) ** 2 + (game.king_loc[0][1] - 3.5) ** 2)
            value -= 8 - math.sqrt((game.king_loc[1][0] - game.king_loc[0][0]) ** 2 +
                                   (game.king_loc[1][1] - game.king_loc[0][1]) ** 2)

    # adds a factor for the mobility of the pieces
    cp_moves = len(game.legal_moves())
    game.history.append("a0a0")
    np_moves = len(game.legal_moves())
    game.history = game.history[:-1]
    if game.to_play() == "w":
        value += config['mobility'][loc] * (cp_moves - np_moves)
    else:
        value -= config['mobility'][loc] * (cp_moves - np_moves)
    value += normal(0, 0.05)
    return round(value, 2)
