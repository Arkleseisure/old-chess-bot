from keras.models import Model, load_model
from tensorflow import nn
import math


# class for the neural network
class NeuralNetwork:
    def __init__(self, file):
        self.network = Model()
        self.network = load_model(file, custom_objects={'softmax_cross_entropy_with_logits_v2':
                                                            nn.softmax_cross_entropy_with_logits})
        self.num_blocks = 20


# makes a dictionary with each legal move as a key and its probability according to the neural network as the value
def make_move_dict(policy_logits, game, legal_moves):
    move_dict = {}
    # makes a dictionary with the values output by the network
    for move in legal_moves:
        move_array = game.move_pos(move)
        move_dict[move] = math.exp(policy_logits[0][move_array[0]][move_array[1]][move_array[2]])

    # finds the sum of the values
    value_sum = 0
    for key in move_dict:
        value_sum += move_dict[key]

    # divides each on by the sum so that they add to 1
    for key in move_dict:
        move_dict[key] /= value_sum
    return move_dict
