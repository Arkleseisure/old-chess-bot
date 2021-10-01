from Node import Node
import Neural_Network
import numpy
import Bits_and_Pieces as BaP
import pygame
from math import log, sqrt


# configuration for the mcts
class Configuration:
    def __init__(self):
        self.num_simulations = 800

        # UCB formula
        self.pb_c_base = 19652
        self.pb_c_init = 1.25

        # exploration noise
        self.root_dirichlet_alpha = 0.3
        self.root_exploration_fraction = 0.25


# runs the monte carlo tree search
def mcts(config, game, neural_net, return_buttons, noise=False):
    max_visits = config.num_simulations
    # initialises the root node
    policy_logits, value = neural_net.predict(numpy.array([game.make_image()]))
    legal_moves = game.legal_moves()
    policy_logits = Neural_Network.make_move_dict(policy_logits, game, legal_moves)
    root = Node(value, game.to_play())
    for move in game.legal_moves():
        root.children[move] = Node(policy_logits[move], BaP.opposite(game.to_play()))

    # if there is only one legal move there is no use in doing a search
    if len(root.children) == 1:
        for key in root.children.keys():
            return key, False

    if noise:
        add_exploration_noise(config, root)

    # runs the search
    for i in range(config.num_simulations):
        # checks if the user has quit the game
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONUP:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                for button in return_buttons:
                    if button.is_clicked(mouse_x, mouse_y):
                        return "----", True

        # creates a clone of the current game so that the parameters aren't affected
        exploration_game = game.clone(False)
        path = [root]
        node = root
        # searches until it reaches a leaf node (a node which hasn't been explored yet)
        while node.expanded():
            move, node = select_child(config, node)
            exploration_game.apply_efficient(move)
            path.append(node)

        # backpropagates the actual terminal state if that has been reached
        # otherwise, the predicted terminal value of the network is used and the node is expanded
        value = exploration_game.terminal()
        if value is not None:
            backpropagate(path, value, BaP.opposite(node.to_play))
        else:
            policy_logits, value = neural_net.predict(numpy.array([exploration_game.make_image()]))
            legal_moves = exploration_game.legal_moves()
            policy_logits = Neural_Network.make_move_dict(policy_logits, exploration_game, legal_moves)
            backpropagate(path, value[0][0], BaP.opposite(node.to_play))
            for move in legal_moves:
                node.children[move] = Node(policy_logits[move], BaP.opposite(node.to_play))

        # if one move is guaranteed to be chosen at any point, this is handled here to speed up move choice
        if i > config.num_simulations // 2 and max_visits > config.num_simulations - i:
            visit_count_list = list(sorted(((key, root.children[key].visit_count) for key in root.children),
                                           key=lambda x: x[1]))
            max_visits = visit_count_list[-1][1]
            if max_visits - visit_count_list[-2][1] > config.num_simulations - i:
                # for item in visit_count_list:
                #     print(item[0], item[1], root.children[item[0]].prior, root.children[item[0]].value())
                return visit_count_list[-1][0], False
    return select_move(root), False


# returns the move that the raw neural network would play, used to speed up the analysis bot as running the full mcts
# over all the moves would take too long.
def get_neural_net_move(game, neural_net):
    policy_logits = neural_net.network.predict(numpy.array([game.make_image()]))
    if len(policy_logits) == 2:
        policy_logits = policy_logits[0]
    legal_moves = game.legal_moves()
    policy_logits = Neural_Network.make_move_dict(policy_logits, game, legal_moves)
    logits = [(probability, move) for move, probability in policy_logits.items()]
    _, move = max(logits)
    return move


# propagates the result of one simulation back to the root node
def backpropagate(search_path, value, to_play):
    for node in search_path:
        node.value_sum += (value if node.to_play == to_play else -value)
        node.visit_count += 1


# selects the move chosen at the end of the simulation
def select_move(root):
    visit_counts = [(child.visit_count, move) for move, child in root.children.items()]
    _, move = max(visit_counts)
    return move


# selects which child to choose for each move in each simulation based on ucb score
def select_child(config, node):
    from random import randint
    _ = -1
    possible_moves = [["----", None]]
    for action, child in node.children.items():
        if ucb_score(config, node, child) > _:
            _ = ucb_score(config, node, child)
            possible_moves = [[action, child]]
        elif ucb_score(config, node, child) == _:
            possible_moves.append([action, child])
    random_number = randint(0, len(possible_moves) - 1)
    move = possible_moves[random_number][0]
    next_node = possible_moves[random_number][1]
    return move, next_node


# calculates the ucb score for the a child node
def ucb_score(config, parent, child):
    pb_c = log((parent.visit_count + config.pb_c_base + 1) / config.pb_c_base) + config.pb_c_init
    pb_c *= sqrt(parent.visit_count) / (child.visit_count + 1)

    prior_score = pb_c * child.prior_with_noise
    value_score = child.value()
    return prior_score + value_score


def add_exploration_noise(config, node):
    actions = node.children.keys()
    noise = numpy.random.gamma(config.root_dirichlet_alpha, 1, len(actions))
    frac = config.root_exploration_fraction
    for a, n in zip(actions, noise):
        node.children[a].prior_with_noise = node.children[a].prior * (1 - frac) + n * frac
