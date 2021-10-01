import random
import Monte_Carlo_Tree_Search as mcts
import Minimax as mm
import time
import math


def get_neural_ai_move(game, neural_network, return_button_group):
    config = mcts.Configuration()
    return mcts.mcts(config, game, neural_network.network, return_button_group, True)


def get_opening_book():
    f = open('Opening book', 'r')
    book = {}
    last_move = None
    for item in f.readlines():
        a = item.split()
        try:
            key = int(a[0])
        except ValueError:
            print(a)
            key = ''
        book[key] = {}
        if 'FEN' in a:
            fen_tags = 0
        else:
            fen_tags = 2
        fen = ''
        item = 0
        for i in range(len(a)):
            if fen_tags == 2:
                if last_move is not None:
                    try:
                        if item == 0:
                            book[key][last_move] = [int(a[i])]
                        else:
                            book[key][last_move].append(float(a[i]))
                        item += 1
                        if item == 2:
                            last_move = None
                    except ValueError:
                        print(a[i])
                        print(a)
                elif len(a[i]) <= 5:
                    last_move = a[i]
                    item = 0

            # there are fen tags in the file showing the fen position for the
            if a[i] == 'FEN':
                fen_tags += 1

            if fen_tags == 1 and a[i] != 'FEN':
                fen += a[i] + ' '

        if book[key] == {}:
            print(item)
        if fen != '':
            # adds the fen to the book... the -1 removes the space at the end of the fen string
            book[key]['FEN'] = fen[:-1]
    return book


def get_minimax_ai_move(game, return_button_group, search_time, node, config, book=None):
    transposition_table = {}
    '''
    if book is None:
        book = {}
    create_opening_book(game, node, config, return_button_group, 3, book=book)
    f = open('Opening book', 'w')
    for key in book:
        f.write(key + ' ' + book[key][0] + ' ' + str(round(book[key][1], 2)) + '\n')
    f.close()

    print('Finished opening book')
    if book != {}:
        return '    ', True, node
    '''

    legal_moves = game.legal_moves()
    if len(legal_moves) == 1:
        return legal_moves[0], False, node

    i = 1
    total_nodes = 0
    search_path = [None]
    current_search_path = []
    quit_code = False
    node_found = False
    if node is None or len(game.history) < 2:
        node = mm.Node(game.to_play())
    # looks to see if it has already searched the node
    elif game.history[-2] in node.children.keys():
        if game.history[-1] in node.children[game.history[-2]].children.keys():
            node = node.children[game.history[-2]].children[game.history[-1]]
            node_found = True

    if not node_found:
        node = mm.Node(game.to_play())

    while True:
        start_time = time.time()
        while not time.time() > start_time + search_time:
            depth_start_time = time.time()
            if config['version'] == 'new':
                '''
                if game.hash in book.keys():
                    # forcing first move
                    if game.hash == 12114566704304161054:
                        return 'd2d4', False, node
                    data = book[game.hash]
                    try:
                        # the score of a move is the fractional score times the root of the number of times it appeared
                        # in the dataset... Rewarding good moves but equally rewarding moves which have been played a
                        # lot and have more certainty associated with their results.
                        total_score = sum((data[key][1]/math.sqrt(data[key][0]) if key != 'FEN' else 0)
                                          for key in book[game.hash].keys())
                        move = random.random()
                    except ValueError:
                        print(total_score)
                        print(book[game.hash])
                    except TypeError:
                        print(book[game.hash])
                    total = 0
                    # moves from the opening book are selected with a probability proportional to the number of times
                    # that move was made in the database
                    for key in book[game.hash].keys():
                        if key != 'FEN':
                            total += data[key][1]/math.sqrt(data[key][0])
                            if total/total_score >= move:
                                move_made = key
                                break
                    else:
                        move_made = '----'
                    return move_made, False, node
                '''
                node, search_path, quit_code, num_nodes, _ = mm.minimax(game, i, return_button_group, config,
                                                                        search_time=search_time,
                                                                        start_time=start_time, node=node,
                                                                        transposition_table=transposition_table)
            elif config['version'] == 'old':
                node, search_path, quit_code, num_nodes, _ = mm.old_minimax(game, i, return_button_group, config,
                                                                            search_time=search_time,
                                                                            start_time=start_time, node=node)
            else:
                node, search_path, quit_code, num_nodes, _ = mm.original_minimax(game, i, return_button_group, config,
                                                                                 search_time=search_time,
                                                                                 start_time=start_time, node=node)

            total_nodes += num_nodes
            i += 1
            if search_path[0] is not None:
                current_search_path = search_path
            else:
                search_path = current_search_path

            def get_value(item):
                return -node.children[item].value

            '''
            print(time.ctime(time.time()))
            print('Depth:', i - 1, 'Time:', round(time.time() - depth_start_time, 3))
            print('Nodes per second:', num_nodes/(time.time() - depth_start_time))
            print('Overall average nodes per second:', num_nodes/(time.time() - start_time))
            for item in sorted(node.children, key=get_value):
                print(item, round(node.children[item].value, 2))
            print(current_search_path)
            print()
            '''
        try:
            '''
            current_node = node
            for move in search_path:
                for child in sorted(current_node.children, key=lambda x:current_node.children[x].value):
                    print(child, round(current_node.children[child].value, 2))
                current_node = current_node.children[move]
                print('Plays', move)
                print()
                print()
            '''

            # resigns if the advantage is too big
            print(round(node.value, 2), search_path[0], i - 1)
            if (node.value > 10 and game.to_play() == 'b') or (node.value < -10 and game.to_play() == 'w'):
                return 'resign', quit_code, node
            return search_path[0], quit_code, node
        except IndexError:
            search_time += 0.2
            print('Search time error')
            i = 1


def get_random_ai_move(game):
    moves = game.legal_moves()
    return moves[random.randint(0, len(moves) - 1)], False


'''
def create_opening_book(game, node, config, return_button_group, depth, prev_moves=[], book={}):
    expansion_range = 0.1

    search_path = []
    quit_code = False
    # searches the position to depth 5
    for i in range(5):
        node, search_path, quit_code, num_nodes, _ = mm.minimax(game, i + 1, return_button_group, config,
                                                                search_time=10000,
                                                                start_time=time.time(), node=node)
        if quit_code:
            break

    def get_value(item):
        return -node.children[item].value

    if not quit_code:
        # adds the best move to the book
        best_value = node.children[search_path[0]].value
        book[game.hash] = [search_path[0], best_value]

        print(time.ctime(time.time()))
        print('Previous moves:', prev_moves, 'Best move:', search_path[0], 'Eval:', round(best_value, 2))
        print('Moves expanded:', end=' ')
        for child in node.children:
            if (node.children[child].value > best_value - expansion_range and node.to_play == 'w') or \
                    (node.children[child].value < best_value + expansion_range and node.to_play == 'b'):
                print(child, "({0})".format(round(node.children[child].value, 2)), end=' ')
        print('\n')
    else:
        return True

    if depth == 0:
        return False

    for move in sorted(node.children, key=get_value):
        if (node.children[move].value > best_value - expansion_range and node.to_play == 'w') or \
                (node.children[move].value < best_value + expansion_range and node.to_play == 'b'):
            prev_moves.append(move)
            captured_piece, p, en_passant, castling_change, prev_counter, \
                prev_past_boards, promoted_pawn = game.apply(move)
            quit_code = create_opening_book(game, node.children[move], config, return_button_group, depth - 1, prev_moves, book)
            game.un_apply(move, captured_piece, en_passant, castling_change, prev_counter, prev_past_boards,
                          promoted_pawn)
            prev_moves.pop(-1)
            if quit_code:
                break

    if node.to_play == 'w':
        max_value = max(node.children[child].value for child in node.children)
        for child in node.children:
            if node.children[child].value == max_value:
                book[game.hash] = [child, max_value]
        node.value = max_value
    else:
        min_value = min(node.children[child].value for child in node.children)
        for child in node.children:
            if node.children[child].value == min_value:
                book[game.hash] = [child, min_value]
        node.value = min_value

    return quit_code
'''
