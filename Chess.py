if __name__ == "__main__":
    import Global_variables as Gv
    import Piece
    import Square
    import Button
    import Menu
    import Border
    import Game
    import Game_starters
    import AI
    import Neural_Network
    import Bits_and_Pieces as BaP
    import Minimax as mm
    import os
    import pygame
    import pygame.freetype
    import queue
    import time
    import random
    import math
    import numpy as np

    # creates a pygame window in the center of the screen
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pygame.init()
    screen = pygame.display.set_mode([Gv.screen_width, Gv.screen_height])
    pygame.display.set_caption("Chess")

# draws the board
def draw_board(piece_list, squares, highlights, pieces_taken, player_colour, borders):
    borders.draw(screen)
    for i in range(8):
        BaP.print_screen(screen, (str(8 - i) if player_colour == "white" else str(i + 1)),
                         Gv.board_top_left_x - Gv.square_size // 3,
                         Gv.board_top_left_y + Gv.square_size * (3 * i + 1) // 3,
                         Gv.square_size // 2, Gv.text_colour)
        BaP.print_screen(screen, (chr(65 + i) if player_colour == "white" else chr(72 - i)),
                         Gv.board_top_left_x + Gv.square_size * (3 * i + 1) // 3,
                         Gv.board_top_left_y + 8 * Gv.square_size + Gv.square_size // 10, Gv.square_size // 2,
                         Gv.text_colour)
    squares.draw(screen)
    highlights.draw(screen)
    piece_list.draw(screen)
    pieces_taken.draw(screen)
    pygame.display.flip()


# adds a taken piece to the side of the board
def add_to_pieces_taken(player_to_move, pieces_captured, pieces_taken, piece_name, player_colour, piece_list):
    # constant which determines how spaced apart the pieces are
    shift = 3 / 7
    # the place variable is used to determine where along the border the piece is put
    place = 0
    # the hierarchy variable is used to compare this piece to the others in that have been taken in order to order them
    hierarchy = 0
    if piece_name[0] == "P":
        hierarchy = 1
    elif piece_name[0] == "N":
        hierarchy = 2
    elif piece_name[0] == "B":
        hierarchy = 3
    elif piece_name[0] == "R":
        hierarchy = 4
    elif piece_name[0] == "Q":
        hierarchy = 5

    # shifts the piece's place according to its value
    for piece in (pieces_captured[0] if player_to_move == "w" else pieces_captured[1]):
        if piece <= hierarchy:
            place += 1
    if player_colour == "white":
        piece_taken = Piece.Piece(place * shift, (- 1.5 if player_to_move == "b" else 7.6), piece_name, player_colour,
                                  Gv.square_size // 2)
    else:
        piece_taken = Piece.Piece(7 - place * shift, (8.5 if player_to_move == "w" else -0.6), piece_name,
                                  player_colour,
                                  Gv.square_size // 2)
    piece_taken.hierarchy = hierarchy
    (pieces_captured[0] if player_to_move == "w" else pieces_captured[1]).append(hierarchy)

    # shifts the other pieces so that the new piece doesn't end up being displayed on top of them
    for piece in pieces_taken:
        if piece.hierarchy > hierarchy and piece.name[-1] == piece_taken.name[-1]:
            piece.x += shift if player_colour == "white" else -shift
            piece.move(player_colour)
    pieces_taken.add(piece_taken)
    calculate_extra_material(pieces_taken, pieces_captured, piece_list, player_colour)
    return pieces_taken, pieces_captured


# calculates the material advantage one side has over the other
def calculate_extra_material(pieces_taken, pieces_captured, piece_list, player_colour):
    shift = 3 / 7
    size = Gv.square_size // 2
    # recalculates the values of the pieces on the board for each side
    white_value = 0
    black_value = 0
    for piece in piece_list:
        value = 0
        if piece.name[0] == "P":
            value = 1
        elif piece.name[0] == "B":
            value = 3
        elif piece.name[0] == "N":
            value = 3
        elif piece.name[0] == "R":
            value = 5
        elif piece.name[0] == "Q":
            value = 9

        if piece.name[-1] == "w":
            white_value += value
        else:
            black_value += value

    # removes the previously displayed difference in value
    for piece in pieces_taken:
        if piece.name == "extra material":
            pieces_taken.remove(piece)

    extra_material = ""
    # adds the new image displaying the material advantage for one side
    if white_value > black_value:
        extra_material = Piece.ExtraMaterial(len(pieces_captured[1]) * shift, -1.5, "extra material", player_colour,
                                             size, "+" + str(white_value - black_value))
    elif black_value > white_value:
        extra_material = Piece.ExtraMaterial(len(pieces_captured[0]) * shift, 7.6, "extra material", player_colour,
                                             size, "+" + str(black_value - white_value))

    # handles the case where the screen is oriented from black's perspective
    if player_colour == "black" and not black_value == white_value:
        extra_material.x = 7 - extra_material.x
        extra_material.y += 0.9
        extra_material.move(player_colour)

    if not black_value == white_value:
        pieces_taken.add(extra_material)


# removes the displayed image of a captured piece when a piece is taken back
def remove_from_pieces_taken(pieces_captured, pieces_taken, piece_name, player_colour, piece_list):
    # constant which determines how spaced apart the pieces are
    shift = 3 / 7

    # the hierarchy variable is used to compare this piece to the others in that have been taken in order to order them
    hierarchy = 0
    if piece_name[0] == "P":
        hierarchy = 1
    elif piece_name[0] == "N":
        hierarchy = 2
    elif piece_name[0] == "B":
        hierarchy = 3
    elif piece_name[0] == "R":
        hierarchy = 4
    elif piece_name[0] == "Q":
        hierarchy = 5

    (pieces_captured[0] if piece_name[-1] == "w" else pieces_captured[1]).remove(hierarchy)

    # shifts the pieces back so that there isn't a gap added when the piece is removed
    piece_removed = False
    for piece in pieces_taken:
        if piece.hierarchy >= hierarchy and piece.name[-1] == piece_name[-1]:
            piece.x -= shift

        if piece.name == piece_name and not piece_removed:
            pieces_taken.remove(piece)
            piece_removed = True
        piece.move("white")
    calculate_extra_material(pieces_taken, pieces_captured, piece_list, player_colour)


# saves the game to a text file so that it can be retrieved
def save_game(moves, notation_moves, wins):
    # makes the button to save the game
    end_of_game_buttons = pygame.sprite.Group()
    save_game_button = Button.Button(Gv.board_top_left_x + 8.1 * Gv.square_size,
                                     Gv.board_top_left_y + 8.2 * Gv.square_size,
                                     3 * Gv.square_size // 2, Gv.square_size * 2 // 3, "Save Game", 17)
    end_of_game_buttons.add(save_game_button)
    end_of_game_buttons.draw(screen)
    pygame.display.flip()

    # checks for the button being clicked
    mouse_x, mouse_y, _, __, ___ = BaP.wait_for_click()
    if save_game_button.is_clicked(mouse_x, mouse_y):
        # reads the previous games from the file so they don't get deleted
        saved_games = open("Saved games", "r")
        previous_games = saved_games.readlines()
        saved_games.close()
        saved_games = open("Saved games", "w")

        # games are labelled by timestamp
        saved_games.write(time.ctime(time.time()) + "\n")

        # adds all the moves in the game in the format generally used in the program, like e2e4
        for move in moves:
            saved_games.write(move + " ")

        # adds all the moves in algebraic notation (e.g Qe4) so that they can be displayed beside the board
        saved_games.write("\n")
        for move in notation_moves:
            saved_games.write(move + " ")

        # writes down the result of the game at the end of the moves
        saved_games.write("1-0" if wins[0] == 1 else ("0-1" if wins[1] == 1 else "1/2-1/2"))

        # writes down the previous games
        saved_games.write("\n")
        for item in previous_games:
            saved_games.write(item)
        saved_games.close()


# replays a saved game
def replay_saved_game(return_button_group):
    player_colour = "white"
    button_height = 40
    next_ply = 0

    # draws the buttons to choose which game to replay
    screen.fill(Gv.background_colour)
    saved_games = open("Saved games", "r")
    games = saved_games.readlines()
    saved_games.close()
    saved_game_buttons = pygame.sprite.Group()
    for i in range(len(games) // 3):
        new_button = Button.Button(0, i * (button_height + 2), Gv.screen_width, button_height, games[i * 3][:-1], 15)
        saved_game_buttons.add(new_button)
    saved_game_buttons.draw(screen)
    pygame.display.flip()

    # gets the user's choice of game to replay
    mouse_x, mouse_y, _, __, ___ = BaP.wait_for_click()
    screen.fill(Gv.background_colour)

    # sets up arrays of moves, one for displaying them on the side, the other for actually moving the pieces.
    try:
        game_moves = games[3 * (mouse_y // (button_height + 2)) + 1].split()
    except IndexError:
        return
    game_display_moves = games[3 * (mouse_y // (button_height + 2)) + 2].split()

    # asks the user whether they want analysis
    BaP.print_screen(screen, "Do you want analysis?", Gv.screen_width // 2, Gv.screen_height // 4, Gv.square_size,
                     Gv.text_colour, left_align=False)
    yes_button = Button.Button(Gv.screen_width // 4, Gv.screen_height // 2, Gv.screen_width // 4, Gv.screen_height // 4,
                               "Yes",
                               Gv.square_size, left_align=False)
    no_button = Button.Button(Gv.screen_width * 3 // 4, Gv.screen_height // 2, Gv.screen_width // 4,
                              Gv.screen_height // 4, "No", Gv.square_size, left_align=False)
    yes_no_buttons = pygame.sprite.Group()
    yes_no_buttons.add(yes_button, no_button)
    yes_no_buttons.draw(screen)
    return_button_group.draw(screen)
    pygame.display.flip()

    # gets the user's reply and analyses the game if wanted
    chosen = False
    analysis = False
    board, past_board_list, piece_dict, piece_list, king_loc, squares = Game_starters.set_up(player_colour)
    game = Game.Game(piece_dict, piece_list, board, past_board_list, [True, True],
                     [True, True], "white", king_loc)
    analysis_game = game.clone(False)
    move_analysis = []
    opening_quality = [0, 0]
    endgame_quality = [0, 0]
    middlegame_quality = [0, 0]
    opening_length = 0
    middlegame_length = 0
    while not chosen:
        mouse_x, mouse_y, _, __, ___ = BaP.wait_for_click()
        if yes_button.is_clicked(mouse_x, mouse_y):
            screen.fill(Gv.background_colour)
            BaP.print_screen(screen, "Do you want full analysis (" + str(5*len(game_moves)) + 'sec)',
                             Gv.screen_width // 2, Gv.screen_height // 4, Gv.square_size,
                             Gv.text_colour, left_align=False)
            BaP.print_screen(screen, 'or quick analysis (' + str(len(game_moves)) + 'sec)',
                             Gv.screen_width // 2, Gv.screen_height // 4 + Gv.square_size, Gv.square_size,
                             Gv.text_colour, left_align=False)
            full_button = Button.Button(Gv.screen_width // 4, Gv.screen_height // 2, Gv.screen_width // 4,
                                        Gv.screen_height // 4, "Full", Gv.square_size, left_align=False)
            quick_button = Button.Button(Gv.screen_width * 3 // 4, Gv.screen_height // 2, Gv.screen_width // 4,
                                         Gv.screen_height // 4, "Quick", Gv.square_size, left_align=False)
            yes_no_buttons = pygame.sprite.Group()
            yes_no_buttons.add(full_button, quick_button)
            yes_no_buttons.draw(screen)
            return_button_group.draw(screen)
            pygame.display.flip()

            mouse_x, mouse_y, _, __, ___ = BaP.wait_for_click()
            if full_button.is_clicked(mouse_x, mouse_y):
                Gv.minimax_time = 5
            else:
                Gv.minimax_time = 1

            analysis = True
            chosen = True
            middlegame = False
            endgame = False
            for move in game_moves:
                screen.fill(Gv.background_colour)
                BaP.print_screen(screen, "Analysing game... " +
                                 str(Gv.minimax_time * (len(game_moves) - len(analysis_game.history))) +
                                 ' seconds left',
                                 Gv.screen_width // 2, Gv.screen_height // 2, Gv.square_size,
                                 Gv.text_colour, left_align=False)
                pygame.display.flip()

                # calculates the average move score of the middlegame when it ends
                if len(analysis_game.piece_list) == 16 and not endgame:
                    endgame = True
                    middlegame_length = len(move_analysis) - opening_length
                    middlegame_quality[0] = round(middlegame_quality[0] /
                                                  (middlegame_length // 2 +
                                                  (middlegame_length % 2 if opening_length % 2 == 0 else 0)), 1)
                    middlegame_quality[1] = round(middlegame_quality[1] /
                                                  (middlegame_length // 2 +
                                                  (middlegame_length % 2 if opening_length % 2 == 1 else 0)), 1)
                # calculates the average move score of the opening when it ends
                elif len(analysis_game.piece_list) == 28 and not middlegame:
                    middlegame = True
                    opening_length = len(move_analysis)
                    opening_quality[0] = round(opening_quality[0] / (opening_length // 2 + (opening_length % 2)), 1)
                    opening_quality[1] = round(opening_quality[1] / (opening_length // 2), 1)

                # gets the minimax search's prediction to get the value and the move score.
                start_time = time.time()
                i = 1
                node = mm.Node(analysis_game.to_play())
                search_path = []
                best_move = '----'
                while time.time() < start_time + Gv.minimax_time:
                    node, search_path, quit_code, total_nodes, \
                        fully_searched = mm.minimax(analysis_game, i, return_button_group, Gv.config,
                                                    search_time=Gv.minimax_time, start_time=start_time, node=node)
                    if len(search_path) > 0 and search_path[0] is not None:
                        best_move = search_path[0]

                value = node.value
                if node.children:
                    max_move_score = max(node.children[key].value for key in node.children)
                    min_move_score = min(node.children[key].value for key in node.children)
                    if min_move_score == max_move_score:
                        move_score = 10
                    elif analysis_game.to_play() == 'w':
                        move_score = round(10 * (node.children[move].value - min_move_score) /
                                          (max_move_score - min_move_score))
                    else:
                        move_score = round(10 * (node.children[move].value - max_move_score) /
                                           (min_move_score - max_move_score))

                # adds the move score to the analysis and to the quality arrays
                move_analysis.append([value, move_score, best_move])
                if endgame:
                    endgame_quality[0 if analysis_game.to_play() == "w" else 1] += move_score
                elif middlegame:
                    middlegame_quality[0 if analysis_game.to_play() == "w" else 1] += move_score
                else:
                    opening_quality[0 if analysis_game.to_play() == "w" else 1] += move_score

                analysis_game.apply(move)

            # after the game has been analysed, this gives the average move score for the endgame.
            if endgame:
                endgame_length = len(move_analysis) - middlegame_length - opening_length
                endgame_quality[0] = round(endgame_quality[0] / (endgame_length // 2 +
                                                                 (endgame_length % 2 if
                                                                  (middlegame_length + opening_length) % 2 == 0
                                                                  else 0)), 1)
                endgame_quality[1] = round(endgame_quality[1] / (endgame_length // 2 +
                                                                 (endgame_length % 2 if
                                                                  (middlegame_length + opening_length) % 2 == 1
                                                                  else 0)), 1)
            elif middlegame:
                middlegame_length = len(move_analysis) - opening_length
                middlegame_quality[0] = round(middlegame_quality[0] /
                                              (middlegame_length // 2 +
                                               (middlegame_length % 2 if opening_length % 2 == 0 else 0)), 1)
                middlegame_quality[1] = round(middlegame_quality[1] /
                                              (middlegame_length // 2 +
                                               (middlegame_length % 2 if opening_length % 2 == 1 else 0)), 1)
            else:
                opening_length = len(move_analysis)
                opening_quality[0] = round(opening_quality[0] / (opening_length // 2 + (opening_length % 2)), 1)
                opening_quality[1] = round(opening_quality[1] / (opening_length // 2), 1)

        elif no_button.is_clicked(mouse_x, mouse_y):
            chosen = True
        else:
            for button in return_button_group:
                if button.is_clicked(mouse_x, mouse_y):
                    return

    screen.fill(Gv.background_colour)

    # sets up buttons for navigating game
    moving_buttons = pygame.sprite.Group()
    forward_button = Button.ImageButton(Gv.board_top_left_x + 9 * Gv.square_size,
                                        Gv.board_top_left_y + 8.2 * Gv.square_size, Gv.square_size // 2,
                                        Gv.square_size // 2,
                                        "forward_arrow")
    backward_button = Button.ImageButton(Gv.board_top_left_x + 8.2 * Gv.square_size,
                                         Gv.board_top_left_y + 8.2 * Gv.square_size, Gv.square_size // 2,
                                         Gv.square_size // 2, "backward_arrow")
    forward_button.image.set_colorkey(Gv.absolute_white)
    backward_button.image.set_colorkey(Gv.absolute_white)
    moving_buttons.add(forward_button, backward_button)
    moving_buttons.draw(screen)

    # adds the visuals and the data structures handling pieces which have been taken
    # as these have to be stored in order to undo moves
    # the cover prevents the move highlight from staying there once the next move has been moved onto
    highlights = pygame.sprite.Group()
    pieces_taken = pygame.sprite.Group()
    exited = False
    pieces_taken_stack = queue.LifoQueue()
    pieces_captured = [[], []]
    cover = pygame.Surface([Gv.screen_width - Gv.board_top_left_x - 8 * Gv.square_size,
                            Gv.board_top_left_y + 8.15 * Gv.square_size])
    cover.fill(Gv.background_colour)
    move_highlight = Button.Button(Gv.board_top_left_x + 8.1 * Gv.square_size,
                                   Gv.board_top_left_y - 0.05 * Gv.square_size,
                                   5 * Gv.square_size // 4, Gv.square_size * 0.3, colour=Gv.location_highlight_colour)
    highlights.add(move_highlight)
    borders = pygame.sprite.Group()
    border = Border.Border(0)
    borders.add(border)
    border = Border.Border(Gv.board_top_left_y + 8 * Gv.square_size)
    borders.add(border)
    ep_stack = queue.LifoQueue()
    promoted_pawn_stack = queue.LifoQueue()
    prev_counter = 0
    prev_past_boards = [game.board]
    castling_change = [[False, False], [False, False]]

    # main loop
    while not exited:
        screen.fill(Gv.background_colour)

        # prints out the analysis for the previous move
        if analysis:
            top = Gv.board_top_left_y
            writing_size = Gv.square_size // 4
            spacing = Gv.square_size // 3
            center_of_writing = Gv.board_top_left_x // 2 - Gv.square_size // 10
            extra_spacing = 0
            print_out = [["Opening" if next_ply <= opening_length else
                          ("Middlegame" if next_ply <= opening_length + middlegame_length else "Endgame"), 0],
                         ["Average move", 3], ["scores:", 1], ["Opening:", 1],
                         ["White: " + str(opening_quality[0]), 1], ["Black: " + str(opening_quality[1]), 1],
                         ["Middlegame:", 2],
                         ["White: " + str(middlegame_quality[0]), 1], ["Black: " + str(middlegame_quality[1]), 1],
                         ["Endgame:", 2],
                         ["White: " + str(endgame_quality[0]), 1], ["Black: " + str(endgame_quality[1]), 1]]
            for item in print_out:
                extra_spacing += item[1]
                BaP.print_screen(screen, item[0], center_of_writing, top + extra_spacing * spacing, writing_size,
                                 Gv.text_colour, left_align=False)
            if next_ply != 0 and next_ply < len(move_analysis):
                print_out = [["Move score:", 3], [str(move_analysis[next_ply - 1][1]), 1], ["Value", 2],
                             ["of position:", 1], [str(move_analysis[next_ply][0]), 1], ["Best move:", 2],
                             [move_analysis[next_ply - 1][2], 1]]
                for item in print_out:
                    extra_spacing += item[1]
                    BaP.print_screen(screen, item[0], center_of_writing, top + extra_spacing * spacing, writing_size,
                                     Gv.text_colour, left_align=False)
            pygame.display.flip()

        # draws the board and other visuals
        x = Gv.board_top_left_x + 8.2 * Gv.square_size
        x_shift = 5 * Gv.square_size // 2
        y = Gv.board_top_left_y
        y_shift = Gv.square_size // 3
        text_size = Gv.square_size // 7 * 2
        return_button_group.draw(screen)
        screen.blit(cover, [Gv.board_top_left_x + 8 * Gv.square_size, 0])
        moving_buttons.draw(screen)
        draw_board(game.piece_list, squares, highlights, pieces_taken, player_colour, borders)
        end_of_game = ["1-0", "1/2-1/2", "0-1"]
        for i in range(len(game_display_moves) if len(game_display_moves) <= 200 else 200):
            if game_display_moves[i] in end_of_game:
                BaP.print_screen(screen, game_display_moves[i], x + 0.6 * Gv.square_size + x_shift * (i // 50),
                                 y + y_shift * (((i + 2) // 2) % 25), text_size, Gv.text_colour)
            elif i % 2 == 0:
                BaP.print_screen(screen, str(i // 2 + 1) + ". " + game_display_moves[i], x + x_shift * (i // 50),
                                 y + y_shift * ((i // 2) % 25), text_size, Gv.text_colour)
            else:
                BaP.print_screen(screen, game_display_moves[i], x + 1.3 * Gv.square_size + x_shift * (i // 50),
                                 y + y_shift * ((i // 2) % 25), text_size, Gv.text_colour)
        pygame.display.flip()

        # waits for the user to do something
        mouse_x, mouse_y, _, __, ___ = BaP.wait_for_click()
        # applies the next move
        if forward_button.is_clicked(mouse_x, mouse_y) and next_ply < len(game_moves):
            move = game_moves[next_ply]
            next_ply += 1
            p_taken, p, ep, castling_change, prev_counter, prev_past_boards, promoted_pawn = game.apply(move)
            calculate_extra_material(pieces_taken, pieces_captured, piece_list, player_colour)

            promoted_pawn_stack.put(promoted_pawn)
            # moves the rook object if castling
            if p.name[0] == "K" and abs(BaP.un_translate(move[0]) - BaP.un_translate(move[2])) == 2:
                p2 = game.piece_dict[("d" if (ord(move[0]) - ord(move[2])) == 2 else "f") + move[3]]
                p2.move(game.player_colour)

            # removes the piece taken
            if p_taken != " ":
                pieces_taken, pieces_captured = add_to_pieces_taken("w" if next_ply % 2 == 0 else "b",
                                                                    pieces_captured, pieces_taken, p_taken.name,
                                                                    player_colour, piece_list)
                pieces_taken_stack.put(p_taken)
            elif not ep:
                pieces_taken_stack.put(item=" ")

            ep_stack.put(ep)
            piece_dict[move[2:4]].move(game.player_colour)

        # undoes previous move
        elif backward_button.is_clicked(mouse_x, mouse_y) and next_ply > 0:
            next_ply -= 1
            move = game_moves[next_ply]
            piece_taken = pieces_taken_stack.get_nowait()
            ep = ep_stack.get_nowait()
            game.un_apply(move, piece_taken, ep, castling_change, prev_counter, prev_past_boards,
                          promoted_pawn_stack.get())

            # moves the rook object if castling
            if game.piece_dict[move[:2]].name[0] == "K" and \
                    abs(BaP.un_translate(move[0]) - BaP.un_translate(move[2])) == 2:
                p2 = game.piece_dict[("a" if (ord(move[0]) - ord(move[2])) == 2 else "h") + move[3]]
                p2.move(game.player_colour)

            # removes the image of the piece from the side of the board
            if piece_taken != " ":
                remove_from_pieces_taken(pieces_captured, pieces_taken, piece_taken.name, player_colour, piece_list)
                piece_taken.move(game.player_colour)

            piece_dict[move[:2]].move(game.player_colour)

        # returns to the main menu if the return button is clicked
        else:
            for button in return_button_group:
                if button.is_clicked(mouse_x, mouse_y):
                    return

        # changes the position of the move highlight
        if next_ply != 0:
            move_highlight.rect.x = Gv.board_top_left_x + 8.1 * Gv.square_size + (5 * Gv.square_size // 2) * \
                                    ((next_ply - 1) // 50) + ((next_ply - 1) % 2) * 1.3 * Gv.square_size
            move_highlight.rect.y = Gv.board_top_left_y + (((next_ply - 1) // 2) % 25) * (Gv.square_size // 3) - \
                                    0.05 * Gv.square_size


# prints the instructions for use of the program out
def instructions(return_button_group):
    screen.fill(Gv.background_colour)
    return_button_group.draw(screen)

    # sets up constants which make the code shorter to write and easier to maintain
    left_margin = Gv.board_top_left_x // 2
    text_size = Gv.square_size * 3 // 10
    line_spacing = text_size
    top = 2 * Gv.square_size

    # prints out the instructions to the screen
    sprites = pygame.sprite.Group()
    BaP.print_screen(screen, "Instructions", Gv.screen_width // 2, Gv.square_size, 100, Gv.text_colour,
                     left_align=False)
    print_out = [["1. Click on the piece that you want to move. "
                  "The square behind it should change colour to this: ", 0],
                 ["2. Click on the square that you want to move to. If the move is legal, then the piece will move "
                  "and the square it lands on will turn this colour: ", 1.5],
                 ["    -If you wish to castle, click on the king first, "
                  "then the square the king lands on, 2 squares away.", 1],
                 ["    -If you wish to promote a pawn, play your move as normal."
                  " Images of the pieces you can promote to will come up like the following: ", 1],
                 ["     Click on one of them to select it as your promotion option.", 1],
                 ["3. You can resign or offer a draw in game by clicking on the 'Options' button, "
                  "followed by the relevant option.", 1.5],
                 ["4. When the game ends, you can save the game "
                  "by clicking on the 'Save game' button.", 1.5],
                 ["5. You can replay any games you've saved from the home screen"
                  " with the 'Saved games' button. They will come up ordered by date.", 1.5],
                 ["    You can then choose whether you want game analysis. This will score "
                  "each of your moves out of 10, and give you your average score for the opening,", 1],
                 ["    middlegame and endgame on the side of the board.", 1],
                 ["    It will also give a value score between for each position, "
                  "giving the value in terms of pawns.", 1],
                 ["   1 is an advantage of 1 pawn for white, "
                  "while -1 is an advantage equivalent to 1 pawn for black.", 1],
                 ["    The best move in the position and the current state of the game (opening, middlegame, endgame)"
                  " is also shown.", 1],
                 ["    Navigate through the game by pressing the yellow arrows on the side of the board.", 1],
                 ["6. You can edit various features according to your preferences from the 'Settings' option"
                  " from the main menu.", 1.5],
                 ["    Change the values by clicking on the up/down buttons next to them.", 1],
                 ["7. Click on the yellow arrow in the top left hand corner "
                  "at any moment to return to the menu page.", 1.5],
                 ["    -Note that if you do this during a game, it will be lost forever.", 1],
                 ["8. From the menu page you can access single player games via the 'Computer' option and 2 player "
                  "via the '2 player' option.", 1.5],
                 ["     There are five levels of bot labelled by elo, the neural engine may take a while to load."
                  " You can choose to play as white, black or random.", 1],
                 ["9. You probably don't need to be told as you're already here, but you can access these instructions "
                  "from the 'Instructions' button in the main menu.", 1.5]]
    added_lines = 0
    for item in print_out:
        added_lines += item[1]
        BaP.print_screen(screen, item[0], left_margin, top + added_lines * line_spacing, text_size, Gv.text_colour)

    # adds two small sprites showing the colour of the highlights for the location and destination
    square = Square.Square(Gv.location_highlight_colour, 10.8, 0.9, Gv.square_size // 3)
    square2 = Square.Square(Gv.destination_highlight_colour, 16.5, 1.4, Gv.square_size // 3)

    # sets up the sprites showing the images of the pieces which will come up when a promotion occurs
    piece_size = Gv.square_size * 2 // 5
    piece_x = 17.7 * Gv.square_size
    piece_y = top + 3.3 * line_spacing
    piece_sep = piece_size + 2
    bishop = Button.ImageButton(piece_x, piece_y, piece_size, piece_size, "Bw")
    knight = Button.ImageButton(piece_x + piece_sep, piece_y, piece_size, piece_size, "Nb")
    rook = Button.ImageButton(piece_x + 2 * piece_sep, piece_y, piece_size, piece_size, "Rw")
    queen = Button.ImageButton(piece_x + 3 * piece_sep, piece_y, piece_size, piece_size, "Qb")

    # adds the sprites to a group so that they can be drawn to the screen
    sprites.add(square)
    sprites.add(square2)
    sprites.add(bishop)
    sprites.add(knight)
    sprites.add(rook)
    sprites.add(queen)
    sprites.draw(screen)
    pygame.display.flip()

    # waits for the user to exit
    exited = False
    while not exited:
        mouse_x, mouse_y, _, __, ___ = BaP.wait_for_click()
        for button in return_button_group:
            if button.is_clicked(mouse_x, mouse_y):
                exited = True


# function allowing the user to change some of the settings of the program
def settings(all_sprites):
    return_button = " "
    button_up = True

    # names the return arrow "return_button" so that it can be called directly
    for button in all_sprites:
        return_button = button

    # sets constants so that the text is evenly spaced
    x_space = 1.3 * Gv.square_size
    text_size = Gv.square_size // 3
    line_spacing = text_size * 1.5
    left_margin = Gv.board_top_left_x
    arrow_width = Gv.square_size // 3
    arrow_height = Gv.square_size // 3
    arrow_x_space = Gv.square_size * 1.3
    arrow_left_margin = left_margin + 0.9 * Gv.square_size
    arrow_top_margin = Gv.board_top_left_y + 0.3 * Gv.square_size
    colour_changes = [Gv.light_square_colour, Gv.dark_square_colour, Gv.background_colour,
                      Gv.location_highlight_colour, Gv.destination_highlight_colour]

    # creates the arrows that can change the settings
    # colour arrows
    up_arrow_list = []
    down_arrow_list = []
    for i in range(3 * len(colour_changes)):
        up_arrow = Button.ImageButton(arrow_left_margin + arrow_x_space * (i % 3),
                                      arrow_top_margin + line_spacing * 3 * (i // 3), arrow_width,
                                      arrow_height, "up_arrow")
        down_arrow = Button.ImageButton(arrow_left_margin + arrow_x_space * (i % 3),
                                        arrow_top_margin + arrow_height + line_spacing * 3 * (i // 3),
                                        arrow_width, arrow_height, "down_arrow")
        up_arrow.image.set_colorkey(Gv.absolute_white)
        down_arrow.image.set_colorkey(Gv.absolute_white)
        up_arrow_list.append(up_arrow)
        down_arrow_list.append(down_arrow)
        all_sprites.add(up_arrow)
        all_sprites.add(down_arrow)

    # time control arrows
    time_up_arrow = Button.ImageButton(left_margin + 3 * Gv.square_size, arrow_top_margin + 14 * line_spacing,
                                       arrow_width, arrow_height, "up_arrow")
    time_down_arrow = Button.ImageButton(left_margin + 3 * Gv.square_size,
                                         arrow_top_margin + 14 * line_spacing + arrow_height,
                                         arrow_width, arrow_height, "down_arrow")
    increment_up_arrow = Button.ImageButton(left_margin + 2.7 * Gv.square_size,
                                            arrow_top_margin + 16 * line_spacing, arrow_width, arrow_height,
                                            "up_arrow")
    increment_down_arrow = Button.ImageButton(left_margin + 2.7 * Gv.square_size,
                                              arrow_top_margin + 16 * line_spacing + arrow_height,
                                              arrow_width, arrow_height, "down_arrow")
    time_up_arrow.image.set_colorkey(Gv.absolute_white)
    time_down_arrow.image.set_colorkey(Gv.absolute_white)
    increment_up_arrow.image.set_colorkey(Gv.absolute_white)
    increment_down_arrow.image.set_colorkey(Gv.absolute_white)
    all_sprites.add(time_up_arrow, time_down_arrow, increment_up_arrow, increment_down_arrow)

    # main loop
    exited = False
    while not exited:
        # draws the sprites showing the colours that are currently set for various parameters
        light_square = Square.Square(Gv.light_square_colour, 2.8, 0, Gv.square_size // 3)
        dark_square = Square.Square(Gv.dark_square_colour, 2.7, 1.4, Gv.square_size // 3)
        location_highlight = Square.Square(Gv.location_highlight_colour, 3.5, 4.35, Gv.square_size // 3)
        destination_highlight = Square.Square(Gv.destination_highlight_colour, 3.9, 5.85, Gv.square_size // 3)
        all_sprites.add(light_square, dark_square, location_highlight, destination_highlight)

        # draws the buttons and the text to the screen
        screen.fill(Gv.background_colour)
        all_sprites.draw(screen)
        print_out = [["Light square colour: ", 0, 0],
                     ["R: " + str(Gv.light_square_colour[0]), 0, 1],
                     ["G: " + str(Gv.light_square_colour[1]), 1, 0],
                     ["B: " + str(Gv.light_square_colour[2]), 2, 0],
                     ["Dark square colour: ", 0, 2],
                     ["R: " + str(Gv.dark_square_colour[0]), 0, 1],
                     ["G: " + str(Gv.dark_square_colour[1]), 1, 0],
                     ["B: " + str(Gv.dark_square_colour[2]), 2, 0],
                     ["Background colour: ", 0, 2],
                     ["R: " + str(Gv.background_colour[0]), 0, 1],
                     ["G: " + str(Gv.background_colour[1]), 1, 0],
                     ["B: " + str(Gv.background_colour[2]), 2, 0],
                     ["Location highlight colour: ", 0, 2],
                     ["R: " + str(Gv.location_highlight_colour[0]), 0, 1],
                     ["G: " + str(Gv.location_highlight_colour[1]), 1, 0],
                     ["B: " + str(Gv.location_highlight_colour[2]), 2, 0],
                     ["Destination highlight colour: ", 0, 2],
                     ["R: " + str(Gv.destination_highlight_colour[0]), 0, 1],
                     ["G: " + str(Gv.destination_highlight_colour[1]), 1, 0],
                     ["B: " + str(Gv.destination_highlight_colour[2]), 2, 0],
                     ["Time control: " + (str(Gv.time_control) + "min" if Gv.time_control != 0 else "None"), 0, 2],
                     ["Increment: " +
                      (str(Gv.increment) + "secs" if (Gv.increment != 0 and Gv.time_control != 0) else "None"), 0, 2]]

        y = Gv.board_top_left_y
        for item in print_out:
            y += line_spacing * item[2]
            BaP.print_screen(screen, item[0], left_margin + x_space * item[1], y, text_size, Gv.text_colour)

        pygame.display.flip()

        # waits for a click
        mouse_x, mouse_y = pygame.mouse.get_pos()
        chosen = False
        while not chosen:
            time.sleep(0.02)
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    chosen = True
                    button_up = False
                elif event.type == pygame.MOUSEBUTTONUP:
                    button_up = True
            if not button_up:
                chosen = True

        # checks for the click's effect
        if return_button.is_clicked(mouse_x, mouse_y):
            exited = True

        # changes the values if a button has been clicked
        for i in range(len(up_arrow_list)):
            if up_arrow_list[i].is_clicked(mouse_x, mouse_y) and colour_changes[i // 3][i % 3] < 255:
                colour_changes[i // 3][i % 3] += 1
            elif down_arrow_list[i].is_clicked(mouse_x, mouse_y) and colour_changes[i // 3][i % 3] > 0:
                colour_changes[i // 3][i % 3] -= 1

        Gv.light_square_colour, Gv.dark_square_colour, Gv.background_colour, \
            Gv.location_highlight_colour, Gv.destination_highlight_colour = colour_changes

        if time_up_arrow.is_clicked(mouse_x, mouse_y):
            Gv.time_control += 1
        if time_down_arrow.is_clicked(mouse_x, mouse_y) and Gv.time_control > 0:
            Gv.time_control -= 1
            if Gv.time_control == 0:
                Gv.increment = 0
        if increment_up_arrow.is_clicked(mouse_x, mouse_y) and Gv.time_control > 0:
            Gv.increment += 1
        if increment_down_arrow.is_clicked(mouse_x, mouse_y) and Gv.increment > 0:
            Gv.increment -= 1

    for sprite in all_sprites:
        if sprite is not return_button:
            all_sprites.remove(sprite)


# main function where the games are played
def play_game(other_player, return_button_group, config_1, config_2):
    total_time = 0
    num_moves = 0
    # sets up most of the variables
    wins = [0, 0, 0]
    highlights = pygame.sprite.Group()
    pieces_taken = pygame.sprite.Group()
    game_over = False
    castle_kingside = {}
    castle_queenside = {}
    book = {}
    answered = False
    total_move_count = 0
    piece_captured = False
    pieces_captured = [[], []]
    notation_moves = []
    quit_code = False
    neural_network = None
    node = None
    for i in range(2):
        castle_queenside[i] = True
        castle_kingside[i] = True

    player_colour = "white"
    move_made = False
    ai = ''
    # allows the user to choose their opponent and their colour if they're playing against the computer
    if other_player == "computer":
        chosen = False
        button_group = pygame.sprite.Group()

        # puts the options on screen
        BaP.print_screen(screen, "Pick your colour", Gv.screen_width // 2, Gv.square_size, 100, Gv.text_colour,
                         False)

        spacing = 15 * Gv.square_size // 4
        x = Gv.screen_width // 2 - spacing
        y = Gv.screen_height // 2 - 2 * Gv.square_size
        width = 5 * Gv.square_size // 2
        height = 3 * Gv.square_size // 2
        text_size = 3 * Gv.square_size // 4

        choices = ["White", "Random", "Black"]
        colour_buttons = []
        for i in range(len(choices)):
            button = Button.Button(x + i * spacing, y, width, height, choices[i], text_size, text_colour=Gv.text_colour,
                                   colour=Gv.background_colour, left_align=False)
            button_group.add(button)
            colour_buttons.append(button)
        button_group.draw(screen)
        return_button_group.draw(screen)
        pygame.display.flip()

        # waits for the user to choose their colour
        while not chosen:
            mouse_x, mouse_y, _, __, ___ = BaP.wait_for_click()
            if colour_buttons[0].is_clicked(mouse_x, mouse_y):
                chosen = True
            elif colour_buttons[1].is_clicked(mouse_x, mouse_y):
                chosen = True
                a = random.randint(0, 1)
                if a == 1:
                    player_colour = "black"
            elif colour_buttons[2].is_clicked(mouse_x, mouse_y):
                chosen = True
                player_colour = "black"
            else:
                for button in return_button_group:
                    if button.is_clicked(mouse_x, mouse_y):
                        return [], [], wins, True

        screen.fill(Gv.background_colour)

        # gives the user their choice of opponent
        chosen = False
        button_group = pygame.sprite.Group()

        BaP.print_screen(screen, "Pick your opponent", Gv.screen_width // 2, Gv.square_size, 100, Gv.text_colour,
                         False)

        options = ["Random (~-200 elo)", "Neural Net (~0 elo)"]
        minimax_options = ['Minimax lvl 1 (~1600 elo)', 'Minimax lvl 2 (~1700 elo)', 'Minimax lvl 3 (~1800 elo)']
        buttons = []
        x = Gv.screen_width//(len(options) * 2)
        y = Gv.screen_height // 2 - 2 * Gv.square_size
        width = Gv.screen_width // len(options)
        height = Gv.square_size
        text_size = height // 2
        minimax_x = Gv.screen_width // (len(minimax_options) * 2)
        minimax_y = y + height * 2
        minimax_width = Gv.screen_width // len(minimax_options)
        minimax_height = height
        minimax_text_size = minimax_height // 2
        for i in range(len(options)):
            button = Button.Button(x, y, width, height, options[i], text_size, text_colour=Gv.text_colour,
                                   colour=Gv.background_colour, left_align=False)
            buttons.append(button)
            button_group.add(button)
            x += width

        for i in range(len(minimax_options)):
            minimax_button = Button.Button(minimax_x, minimax_y, minimax_width, minimax_height, minimax_options[i],
                                           minimax_text_size, text_colour=Gv.text_colour,
                                           colour=Gv.background_colour, left_align=False)
            buttons.append(minimax_button)
            button_group.add(minimax_button)
            minimax_x += minimax_width
        return_button_group.draw(screen)
        button_group.draw(screen)
        pygame.display.flip()

        # waits for the user to choose their opponent
        while not chosen:
            mouse_x, mouse_y, _, __, ___ = BaP.wait_for_click()
            if buttons[0].is_clicked(mouse_x, mouse_y):
                chosen = True
                ai = 'rand'
            elif buttons[1].is_clicked(mouse_x, mouse_y):
                chosen = True
                ai = 'mcts'
                screen.fill(Gv.background_colour)
                BaP.print_screen(screen, "Loading engine...", Gv.screen_width // 2,
                                 Gv.screen_height // 2, Gv.square_size, Gv.text_colour, left_align=False)
                pygame.display.flip()
                neural_network = Neural_Network.NeuralNetwork("Neural Net Attempt 13")
            elif buttons[2].is_clicked(mouse_x, mouse_y):
                chosen = True
                ai = 'mm'
                Gv.minimax_time = 0.5
            elif buttons[3].is_clicked(mouse_x, mouse_y):
                chosen = True
                ai = 'mm'
                Gv.minimax_time = 1
            elif buttons[4].is_clicked(mouse_x, mouse_y):
                chosen = True
                ai = 'mm'
                Gv.minimax_time = 10
            else:
                for button in return_button_group:
                    if button.is_clicked(mouse_x, mouse_y):
                        return [], [], wins, True
        screen.fill(Gv.background_colour)

    if other_player == 'double_ai':
        ai = 'mm'

    if ai == 'mm':
        # book = AI.get_opening_book()
        book = {}

    # adds the options and return buttons
    options_button = Button.Button(0.5 * (Gv.board_top_left_x - 1.2 * Gv.square_size),
                                   Gv.board_top_left_y + 3 * Gv.square_size + 5 * Gv.square_size // 8,
                                   Gv.square_size * 1.2,
                                   Gv.square_size * 3 // 4, text="Options", font_size=20)
    all_buttons = pygame.sprite.Group()
    all_buttons.add(options_button)
    all_buttons.add(button for button in return_button_group)

    # sets up the board, the squares and the pieces
    screen.fill(Gv.background_colour)
    all_buttons.draw(screen)
    board, past_board_list, piece_dict, piece_list, king_loc, squares = Game_starters.set_up(player_colour)
    borders = pygame.sprite.Group()
    border = Border.Border(0)
    borders.add(border)
    border = Border.Border(Gv.board_top_left_y + 8 * Gv.square_size)
    borders.add(border)
    draw_board(piece_list, squares, highlights, pieces_taken, player_colour, borders)
    board_drawn = True
    ans = ""
    game = Game.Game(piece_dict, piece_list, board, past_board_list, castle_kingside, castle_queenside, player_colour,
                     king_loc)

    # adds the time control variables and clock images
    mins = [Gv.time_control, Gv.time_control]
    secs = [0, 0]
    time_group = pygame.sprite.Group()
    loc = 0 if game.player_colour == "black" else 1
    x_pos = Gv.board_top_left_x - Gv.square_size * 1.1
    y_pos = 0.5 * (Gv.board_top_left_y - Gv.square_size * 0.4)
    width = Gv.square_size
    height = Gv.square_size * 0.4
    clock1 = Button.Button(x_pos, y_pos, width, height,
                           text=str(mins[loc]) + ":" + ("0" if secs[loc] < 10 else "") + str(secs[loc]),
                           font_size=Gv.square_size // 4)
    clock2 = Button.Button(x_pos, Gv.screen_height - y_pos - height, width, height,
                           text=str(mins[1 - loc]) + ":" + ("0" if secs[1 - loc] < 10 else "") + str(secs[1 - loc]),
                           font_size=Gv.square_size // 4)
    time_group.add(clock1, clock2)
    time_group.draw(screen)
    pygame.display.flip()
    out_of_time = False

    # main game loop
    while game_over is False:
        prom = ""
        quit_code = False
        # gets the human's move
        if other_player == "human" or (other_player == 'computer' and game.player_colour[0] == game.to_play()):
            index = 0 if game.to_play() == "w" else 1
            # gets the player's clicks
            if mins != [0, 0] or secs != [0, 0]:
                mouse_x, mouse_y, out_of_time, mins[index], secs[index] = \
                    BaP.wait_for_click([mins[index], secs[index], "top" if game.to_play() != game.player_colour[0] else
                    "bottom", screen])
            else:
                mouse_x, mouse_y, _, __, ___ = BaP.wait_for_click()

            # adds the position of the click to the move so long as it is on the board
            if Gv.board_top_left_x < mouse_x < Gv.board_top_left_x + 8 * Gv.square_size and \
                    Gv.board_top_left_y < mouse_y < Gv.board_top_left_y + 8 * Gv.square_size:
                if player_colour == "white":
                    ans += BaP.translate((mouse_x - Gv.board_top_left_x) // Gv.square_size,
                                         7 - (mouse_y - Gv.board_top_left_y) // Gv.square_size)
                else:
                    ans += BaP.translate(7 - (mouse_x - Gv.board_top_left_x) // Gv.square_size,
                                         (mouse_y - Gv.board_top_left_y) // Gv.square_size)

                for a in ans:
                    if a not in Gv.coordinate_letters and a not in Gv.coordinate_numbers:
                        ans = ""

                # adds and removes the relevant square highlights
                if len(ans) == 2:
                    h = Square.Square(Gv.location_highlight_colour,
                                      BaP.un_translate(ans[0]) if game.player_colour == 'white' else
                                      7 - BaP.un_translate(ans[0]),
                                      8 - int(ans[1]) if game.player_colour == 'white' else int(ans[1]) - 1)

                    highlights.add(h)
                    board_drawn = False
                elif len(ans) == 4:
                    answered = True
                    h = Square.Square(Gv.destination_highlight_colour,
                                      BaP.un_translate(ans[2]) if game.player_colour == 'white' else
                                      7 - BaP.un_translate(ans[2]),
                                      8 - int(ans[3]) if game.player_colour == 'white' else int(ans[3]) - 1)

                    # removes unnecessary highlights
                    for highlight in highlights:
                        if not highlight.part_of_move(ans, game.player_colour):
                            highlight.kill()
                    highlights.add(h)
                    board_drawn = False

            # handles the options button
            elif options_button.is_clicked(mouse_x, mouse_y):
                # prints the options on screen
                background = Button.Button(Gv.board_top_left_x + 1.5 * Gv.square_size,
                                           Gv.board_top_left_y + 1.5 * Gv.square_size, 5 * Gv.square_size,
                                           6 * Gv.square_size,
                                           colour=(50, 50, 50))
                resign = Button.Button(Gv.board_top_left_x + 2.5 * Gv.square_size,
                                       Gv.board_top_left_y + 2.5 * Gv.square_size,
                                       3 * Gv.square_size, 1.75 * Gv.square_size, text="Resign", font_size=40)
                offer_draw = Button.Button(Gv.board_top_left_x + 2.5 * Gv.square_size,
                                           Gv.board_top_left_y + 4.75 * Gv.square_size, 3 * Gv.square_size,
                                           1.75 * Gv.square_size, text="Offer draw", font_size=40)
                option_buttons = pygame.sprite.Group()
                option_buttons.add(background, resign, offer_draw)
                option_buttons.draw(screen)
                pygame.display.flip()

                # gets the user's click position
                mouse_x, mouse_y, _, __, ___ = BaP.wait_for_click()

                # handles the resignation option
                if resign.is_clicked(mouse_x, mouse_y):
                    game_over = True
                    ans = "resign"
                    answered = True
                    draw_board(game.piece_list, squares, highlights, pieces_taken, player_colour, borders)

                # if the user wants to offer a draw
                elif offer_draw.is_clicked(mouse_x, mouse_y):
                    draw_board(game.piece_list, squares, highlights, pieces_taken, player_colour, borders)
                    if other_player == "human":
                        accept_draw = Button.Button(Gv.board_top_left_x + 2.5 * Gv.square_size,
                                                    Gv.board_top_left_y + 2.5 * Gv.square_size, 3 * Gv.square_size,
                                                    1.75 * Gv.square_size, text="Accept draw", font_size=40)
                        reject_draw = Button.Button(Gv.board_top_left_x + 2.5 * Gv.square_size,
                                                    Gv.board_top_left_y + 4.75 * Gv.square_size, 3 * Gv.square_size,
                                                    1.75 * Gv.square_size, text="Reject draw", font_size=40)
                        accept_draw_group = pygame.sprite.Group()
                        accept_draw_group.add(accept_draw, reject_draw)
                        accept_draw_group.draw(screen)
                        pygame.display.flip()
                        reply = False
                        while not reply:
                            mouse_x, mouse_y, _, __, ___ = BaP.wait_for_click()
                            if accept_draw.is_clicked(mouse_x, mouse_y):
                                game_over = True
                                ans = "draw"
                                answered = True
                                reply = True
                            elif reject_draw.is_clicked(mouse_x, mouse_y):
                                reply = True
                    else:
                        ans = "draw offer"
                draw_board(game.piece_list, squares, highlights, pieces_taken, player_colour, borders)

            # checks for returning to the main menu
            else:
                for button in return_button_group:
                    if button.is_clicked(mouse_x, mouse_y):
                        game_over = True
                        board_drawn = True
                        quit_code = True

            # handles the option that the player has lost on time
            if out_of_time:
                board_drawn = True
                game_over = True
                ans = "drawn on time"
                for piece in game.piece_list:
                    if piece.name[-1] != game.to_play() and piece.name[0] != "K":
                        ans = "lost on time"

        # gets the computer's move
        elif ai == 'rand':
            ans, quit_code = AI.get_random_ai_move(game)
        elif ai == 'mcts':
            start_time = time.time()
            ans, quit_code = AI.get_neural_ai_move(game, neural_network, return_button_group)
            total_time += time.time() - start_time
            print(time.time() - start_time)
            num_moves += 1
        else:
            ans, quit_code, node = AI.get_minimax_ai_move(game, return_button_group, Gv.minimax_time, node,
                                                          config_1 if game.to_play() == 'w' else config_2,
                                                          book=book)

        if not quit_code and ans != 'resign' and ai != "" and \
                ((game.to_play() != game.player_colour[0] and other_player == 'computer')
                 or other_player == 'double_ai'):
            h = Square.Square(Gv.location_highlight_colour,
                              BaP.un_translate(ans[0]) if game.player_colour == 'white' else
                              7 - BaP.un_translate(ans[0]),
                              8 - int(ans[1]) if game.player_colour == 'white' else int(ans[1]) - 1)

            highlights.add(h)
            h = Square.Square(Gv.destination_highlight_colour,
                              BaP.un_translate(ans[2]) if game.player_colour == 'white' else
                              7 - BaP.un_translate(ans[2]),
                              8 - int(ans[3]) if game.player_colour == 'white' else int(ans[3]) - 1)

            # removes unnecessary highlights
            for highlight in highlights:
                if not highlight.part_of_move(ans, game.player_colour):
                    highlight.kill()
            highlights.add(h)
            answered = True
        elif quit_code:
            game_over = True
        elif ans == 'resign':
            answered = True

        if board_drawn is False:
            draw_board(game.piece_list, squares, highlights, pieces_taken, game.player_colour, borders)
            board_drawn = True

        # if a move has been chosen, it will now be checked
        if answered is True:
            # handles resignation
            if ans == "resign":
                game_over = True
                move_made = True
                if game.to_play() == "w":
                    BaP.print_screen(screen, "Black wins by resignation", Gv.board_top_left_x + Gv.square_size // 4,
                                     Gv.board_top_left_y + 3.2 * Gv.square_size, Gv.square_size * 72 // 100,
                                     Gv.absolute_black)
                    wins[1] = 1
                else:
                    BaP.print_screen(screen, "White wins by resignation", Gv.board_top_left_x + Gv.square_size // 4,
                                     Gv.board_top_left_y + 3.2 * Gv.square_size, Gv.square_size * 72 // 100,
                                     Gv.absolute_black)
                    wins[0] = 1
                pygame.display.flip()

            # handles all moves
            elif len(ans) > 0 and ans != "----" and ans[:5] != "draw" and ans[:5] != "lost":
                p = game.piece_dict[ans[:2]]
                if p != " ":
                    # gets all possible moves
                    possible_moves = game.legal_moves()
                    for move in possible_moves:
                        if ans[:4] == move[:4] and not move_made:
                            # checks for promotion
                            if p.name[0] == "P" and (move[3] == "8" or move[3] == "1"):
                                if other_player == "human" or \
                                        (other_player == 'computer' and game.player_colour[0] == game.to_play()):
                                    # sets the top left x and y for the bishop piece
                                    # so that the other pieces can then be based off that
                                    if Gv.board_top_left_x + BaP.un_translate(move[2]) * \
                                            Gv.square_size < Gv.board_top_left_x + 5 * Gv.square_size:
                                        top_left_x_pos = Gv.board_top_left_x + \
                                                         BaP.un_translate(move[2]) * Gv.square_size
                                    else:
                                        top_left_x_pos = Gv.board_top_left_x + 4 * Gv.square_size
                                    if (move[3] == "1") != (game.player_colour[0] == "w"):
                                        top_left_y_pos = Gv.board_top_left_y + Gv.square_size
                                    else:
                                        top_left_y_pos = Gv.board_top_left_y + 6 * Gv.square_size

                                    # creates the images of the pieces to promote to and draws them on the screen
                                    bishop = Button.ImageButton(top_left_x_pos, top_left_y_pos, Gv.square_size,
                                                                Gv.square_size, "B" + game.to_play())
                                    knight = Button.ImageButton(top_left_x_pos + Gv.square_size, top_left_y_pos,
                                                                Gv.square_size, Gv.square_size, "N" + game.to_play())
                                    rook = Button.ImageButton(top_left_x_pos + 2 * Gv.square_size, top_left_y_pos,
                                                              Gv.square_size, Gv.square_size, "R" + game.to_play())
                                    queen = Button.ImageButton(top_left_x_pos + 3 * Gv.square_size, top_left_y_pos,
                                                               Gv.square_size, Gv.square_size, "Q" + game.to_play())
                                    promotion_pieces_buttons = pygame.sprite.Group()
                                    promotion_pieces_buttons.add(bishop, knight, rook, queen)
                                    promotion_pieces_buttons.draw(screen)
                                    pygame.display.flip()

                                    # gets the user's choice of promotion piece
                                    chosen = False
                                    while chosen is False:
                                        for event in pygame.event.get():
                                            if event.type == pygame.MOUSEBUTTONUP:
                                                mouse_x, mouse_y = pygame.mouse.get_pos()
                                                if rook.is_clicked(mouse_x, mouse_y):
                                                    chosen = True
                                                    prom = "R"
                                                elif bishop.is_clicked(mouse_x, mouse_y):
                                                    chosen = True
                                                    prom = "B"
                                                elif knight.is_clicked(mouse_x, mouse_y):
                                                    chosen = True
                                                    prom = "N"
                                                elif queen.is_clicked(mouse_x, mouse_y):
                                                    chosen = True
                                                    prom = "Q"
                                                ans = ans + prom
                                else:
                                    prom = move[4]

                            # applies the move
                            captured_piece, p, _, __, ___, ____, _____ = game.apply(ans)

                            # adds the increment to the time of the player
                            if mins != [0, 0] or secs != [0, 0]:
                                loc = 0 if game.to_play() == "b" else 1
                                secs[loc] += Gv.increment
                                mins[loc] += secs[loc] // 60
                                secs[loc] %= 60

                            # adds the taken piece to the side of the board
                            if captured_piece != " ":
                                piece_captured = True
                                pieces_taken, pieces_captured = add_to_pieces_taken(game.to_play(), pieces_captured,
                                                                                    pieces_taken, captured_piece.name,
                                                                                    player_colour, game.piece_list)
                            elif prom != "":
                                calculate_extra_material(pieces_taken, pieces_captured, game.piece_list, game.to_play())
                            p.move(game.player_colour)

                            # moves the rook object if castling
                            if p.name[0] == "K" and abs(BaP.un_translate(move[0]) - BaP.un_translate(move[2])) == 2:
                                p2 = game.piece_dict[("d" if (BaP.un_translate(move[0]) -
                                                              BaP.un_translate(move[2])) == 2 else "f") +
                                                     ("1" if game.to_play() == "b" else "8")]
                                p2.move(game.player_colour)
                            board_drawn = False
                            move_made = True

            # if the move attempted wasn't legal, the second click becomes a selection click
            # (i.e one where you select the piece you want to move)
            if not move_made and ans[:5] != "draw" and ans[:5] != "lost":
                for highlight in highlights:
                    if highlight.part_of_move(ans, player_colour):
                        highlights.remove(highlight)
                ans = ans[2:4]
                new_highlight = Square.Square(Gv.location_highlight_colour,
                                              BaP.un_translate(ans[0]) if game.player_colour[0] == 'w' else
                                              7 - BaP.un_translate(ans[0]),
                                              (8 - int(ans[1]) if game.player_colour[0] == 'w' else int(ans[1]) - 1))
                board_drawn = False
                highlights.add(new_highlight)
                answered = False

        # handles agreed draws
        if ans == "draw":
            move_made = True
            game_over = True
            BaP.print_screen(screen, "Draw agreed", Gv.board_top_left_x + 1.2 * Gv.square_size,
                             Gv.board_top_left_y + 3.2 * Gv.square_size, Gv.square_size, Gv.absolute_black)
            wins[2] += 1
            pygame.display.flip()

        # handles the case where one person loses on time, but their opponent cannot checkmate them with any
        # legal set of moves and the game is therefore declared a draw
        elif ans == "drawn on time":
            move_made = True
            game_over = True
            BaP.print_screen(screen, "Out of time", Gv.board_top_left_x + 1.5 * Gv.square_size,
                             Gv.board_top_left_y + 3.2 * Gv.square_size, Gv.square_size, Gv.absolute_black)
            BaP.print_screen(screen, "Draw", Gv.board_top_left_x + 3 * Gv.square_size,
                             Gv.board_top_left_y + 4.4 * Gv.square_size, Gv.square_size, Gv.absolute_black)
            wins[2] += 1
            pygame.display.flip()
        # handles the case of losing on time
        elif ans == "lost on time":
            move_made = True
            game_over = True
            if game.to_play() == "w":
                BaP.print_screen(screen, "Out of time", Gv.board_top_left_x + 1.5 * Gv.square_size,
                                 Gv.board_top_left_y + 3.2 * Gv.square_size, Gv.square_size, Gv.absolute_black)
                BaP.print_screen(screen, "Black wins", Gv.board_top_left_x + 1.5 * Gv.square_size,
                                 Gv.board_top_left_y + 4.4 * Gv.square_size, Gv.square_size, Gv.absolute_black)
                wins[1] += 1
            else:
                BaP.print_screen(screen, "Out of time", Gv.board_top_left_x + 1.5 * Gv.square_size,
                                 Gv.board_top_left_y + 3.2 * Gv.square_size, Gv.square_size, Gv.absolute_black)
                BaP.print_screen(screen, "White wins", Gv.board_top_left_x + 1.5 * Gv.square_size,
                                 Gv.board_top_left_y + 4.4 * Gv.square_size, Gv.square_size, Gv.absolute_black)
                wins[0] += 1

            pygame.display.flip()

        # checks for an end state if a move has been made
        if not board_drawn:
            if not move_made:
                pass
            else:
                if not game_over:
                    # these check for the various possible endings to the game
                    value = game.terminal()
                    if value is not None:
                        # checkmate
                        if value == 1:
                            draw_board(game.piece_list, squares, highlights, pieces_taken, game.player_colour, borders)
                            BaP.print_screen(screen, "Checkmate!", Gv.board_top_left_x + 1.2 * Gv.square_size,
                                             Gv.board_top_left_y + 3.2 * Gv.square_size, Gv.square_size,
                                             Gv.absolute_black)
                            BaP.print_screen(screen, "White wins!!", Gv.board_top_left_x + 1.2 * Gv.square_size,
                                             Gv.board_top_left_y + 4.2 * Gv.square_size, Gv.square_size,
                                             Gv.absolute_black)
                            wins[0] += 1
                            game_over = True
                            board_drawn = True
                        elif value == -1:
                            draw_board(game.piece_list, squares, highlights, pieces_taken, game.player_colour, borders)
                            BaP.print_screen(screen, "Checkmate!", Gv.board_top_left_x + 1.2 * Gv.square_size,
                                             Gv.board_top_left_y + 3.2 * Gv.square_size, Gv.square_size,
                                             Gv.absolute_black)
                            BaP.print_screen(screen, "Black wins!!", Gv.board_top_left_x + 1.2 * Gv.square_size,
                                             Gv.board_top_left_y + 4.2 * Gv.square_size, Gv.square_size,
                                             Gv.absolute_black)
                            wins[1] += 1
                            game_over = True
                            board_drawn = True

                        # draws
                        elif value == 0:
                            draw_board(game.piece_list, squares, highlights, pieces_taken, game.player_colour, borders)
                            BaP.print_screen(screen, "Draw!", Gv.board_top_left_x + 1.2 * Gv.square_size,
                                             Gv.board_top_left_y + 3.2 * Gv.square_size, Gv.square_size,
                                             Gv.absolute_black)
                            game_over = True
                            board_drawn = True
                            wins[2] += 1
                else:
                    # prints the result to the screen in the case of resignation
                    # (the only case in which this part of the code gets used)
                    if game.to_play() == "b":
                        BaP.print_screen(screen, "White wins!!", Gv.board_top_left_x + 1.2 * Gv.square_size,
                                         Gv.board_top_left_y + 4.2 * Gv.square_size, Gv.square_size, Gv.absolute_black)
                        wins[0] += 1
                    else:
                        BaP.print_screen(screen, "Black wins!!", Gv.board_top_left_x + 1.2 * Gv.square_size,
                                         Gv.board_top_left_y + 4.2 * Gv.square_size, Gv.square_size, Gv.absolute_black)
                        wins[1] += 1

                move_made = False

                # sets constants to values so that the code can be more easily understood
                if game.to_play() == "b":
                    total_move_count += 1
                x = Gv.board_top_left_x + 8 * Gv.square_size + 10
                shift_x = (5 * Gv.square_size // 2) * ((total_move_count - 1) // 25)
                y = Gv.board_top_left_y
                shift_y = Gv.square_size // 3 * ((total_move_count - 1) % 25)
                size = Gv.square_size // 7 * 2

                # prints the move to the screen
                if game.to_play() == "w":
                    output_move = BaP.proper_notation(ans, game, piece_captured, prom, game_over)
                    notation_moves.append(output_move)
                    BaP.print_screen(screen, output_move, x + Gv.square_size * 5 // 4 + shift_x,
                                     y + shift_y, size, Gv.text_colour)
                else:
                    output_move = BaP.proper_notation(ans, game, piece_captured, prom, game_over)
                    notation_moves.append(output_move)
                    BaP.print_screen(screen, str(total_move_count) + ". " + output_move,
                                     x + shift_x, y + shift_y, size, Gv.text_colour)

                pygame.display.flip()

                # resets the answer
                if ans != "":
                    ans = ""
            piece_captured = False
            answered = False

            # draws the board if this hasn't already been done
            if not board_drawn:
                draw_board(game.piece_list, squares, highlights, pieces_taken, game.player_colour, borders)
                board_drawn = True
    return game.history, notation_moves, wins, quit_code


# the main function from which everything else is called
def main():
    left = False
    return_button_group = pygame.sprite.Group()
    return_button = Button.ImageButton(2, 2, Gv.square_size * 2 // 3, Gv.square_size * 4 // 9, "backward_arrow")
    return_button.image.set_colorkey(Gv.absolute_white)
    return_button_group.add(return_button)
    while not left:
        option, left = Menu.menu(screen)
        screen.fill(Gv.background_colour)

        # option to play player vs player
        if option == 0:
            moves = play_game("human", return_button_group, Gv.config, Gv.config)
            if not moves[3]:
                save_game(moves[0], moves[1], moves[2])

        # option to play against a computer
        elif option == 1:
            moves, proper_moves, wins, quit_code = play_game('computer', return_button_group, Gv.config, Gv.config)
            if not quit_code:
                save_game(moves, proper_moves, wins)

        # option to replay a saved game
        elif option == 2:
            replay_saved_game(return_button_group)

        # option to look at the instructions
        elif option == 3:
            instructions(return_button_group)

        # option to change the settings
        elif option == 4:
            settings(return_button_group)


def test_config(config, old_config, test_length, num_programs, minimax_time):
    return_button_group = pygame.sprite.Group()
    return_button = Button.ImageButton(2, 2, Gv.square_size * 2 // 3, Gv.square_size * 4 // 9, "backward_arrow")
    return_button.image.set_colorkey(Gv.absolute_white)
    return_button_group.add(return_button)

    print('Testing:')
    print('Config:', config)
    print('Old config:', old_config)
    Gv.minimax_time = minimax_time
    score = 0
    draws = 0
    w_wins = 0
    for j in range(test_length//num_programs):
        print('Game', j + 1)
        moves, proper_moves, wins, quit_code = play_game('double_ai', return_button_group,
                                                         config if j % 2 == 0 else old_config,
                                                         old_config if j % 2 == 0 else config)
        if wins[2] == 1:
            score += 0.5
            draws += 1
        elif wins[1] == j % 2:
            score += 1
        if wins[0] == 1:
            w_wins += 1

        print('Score:', score)
        print('Draws:', draws)
        print('White wins:', w_wins)


# simulates a game given the probability of white winning and the probability of black winning
def get_result(w_win_prob, draw_prob):
    result = random.random()
    if result < w_win_prob:
        return 1
    elif result < w_win_prob + draw_prob:
        return 0.5
    return 0


# simulates a test between evenly matched opponents with a certain number of games and returns the score.
def simulate_test(w_win_prob, draw_prob, num_games):
    score = 0
    for i in range(num_games):
        result = get_result(w_win_prob, draw_prob)
        if i % 2 == 0:
            score += result
        else:
            score += 1 - result
    return score


# takes in the parameters of a testing setup, and returns the results needed to be certain that one ai is better at
# various significance levels.
def get_testing_distribution(w_win_prob, draw_prob, num_games):
    print('Distribution for', num_games, 'games in a test')
    num_simulations = 1000000
    # levels of certainty required that one ai is better than the other
    significance_levels = [0.01, 0.05, 0.1, 0.5, 1, 5, 10]
    scores = []
    for i in range(num_simulations):
        score = simulate_test(w_win_prob, draw_prob, num_games)
        scores.append(score)
    sorted_scores = sorted(scores)
    for level in significance_levels:
        score_at_level = sorted_scores[int(round((1 - level/100) * len(sorted_scores)))]
        # The score at level will return the score which is at that significance level,
        # meaning 0.5 more is required to pass
        score_required = score_at_level + 0.5
        print('Percent score required to show one bot is better at the', str(level) + '% significance level:',
              round(100 * score_required/num_games, 1))
        # score = 1/(1 + 10 ** (elodiff/400))  (where the score is expressed as a fraction e.g 0.6 = 60% score)
        # 10 ** (elodiff/400) = 1/score - 1
        # elodiff = 400log10(1/score - 1)
        print('Elo sensitivity:', round(-400 * math.log10(num_games/score_required - 1)))
    print('Time required:', int((num_games * 1.8)//60), 'hours', int(round((num_games * 1.5) % 60)), 'minutes')


def print_book(book):
    previous_book = AI.get_opening_book()
    f = open('Opening book', 'w')
    min_visit_sum = 5
    # adds results from previous books to this book so that data isn't lost
    for key in previous_book:
        if key in book:
            for key2 in previous_book[key]:
                if key2 in book[key] and key2 != 'FEN':
                    for i in range(len(previous_book[key][key2])):
                        book[key][key2][i] += previous_book[key][key2][i]
                else:
                    book[key][key2] = previous_book[key][key2]
        else:
            book[key] = previous_book[key]

    for key in book:
        visit_sum = sum((book[key][key2][0] if key2 != 'FEN' else 0) for key2 in book[key].keys())
        if visit_sum > min_visit_sum:
            book_entry = str(key) + ' FEN ' + str(book[key]['FEN']) + ' FEN'
            for key2 in book[key].keys():
                if key2 != 'FEN':
                    book_entry += ' ' + key2 + ' ' + str(book[key][key2][0]) + ' ' + str(book[key][key2][1])
            f.write(book_entry + '\n')
    f.close()


def create_opening_book():
    f = open('All_training_data', 'r')
    all_games = f.readlines()
    all_games = all_games[1940000:]
    book = {}
    i = 0
    for item in all_games:
        i += 1
        if i % 1000 == 0:
            print(i, time.ctime(time.time()))

        next_game = item.split()
        board, past_board_list, piece_dict, piece_list, king_loc, squares = Game_starters.set_up('white')
        game = Game.Game(piece_dict, piece_list, board, past_board_list, [True, True],
                         [True, True], "white", king_loc)
        using_game = True
        if next_game[-1] == '1/2-1/2':
            score = 0.5
        elif next_game[-1] == '1-0':
            score = 1
        elif next_game[-1] == '0-1':
            score = 0
        else:
            using_game = False
        if using_game:
            player = 0
            for move in next_game[:-1]:
                if game.hash in book.keys():
                    if move in book[game.hash].keys():
                        # returns 1 if player = 0 and score = 1 or player = 1 and score = 0 (player 0 is white, 1 black)
                        book[game.hash][move][0] += 1
                        book[game.hash][move][1] += abs(player - score)
                    else:
                        book[game.hash][move] = [1, abs(player - score)]
                else:
                    book[game.hash] = {'FEN': game.fen(), move: [1, abs(player - score)]}
                game.apply_efficient(move)
                player = 1 - player

        # removes superfluous positions which are wasting storage
        if i % 100000 == 0:
            print(len(book))
            pop_list = []
            for item in book:
                times_reached = sum((book[item][key][0] if key != 'FEN' else 0) for key in book[item].keys())
                if times_reached == 1:
                    pop_list.append(item)
            for item in pop_list:
                book.pop(item)
            print(len(book))

    print_book(book)

def perft(game, depth):
    moves = game.legal_moves()
    if depth == 1:
        return len(moves)

    num_moves = 0
    for move in moves:
        captured_piece, p, en_passant, castling_change, prev_counter, prev_past_boards, promoted_pawn = game.apply(move)
        num_moves += perft(game, depth - 1)
        game.un_apply(move, captured_piece, en_passant, castling_change, prev_counter, prev_past_boards, promoted_pawn)

    return num_moves


def speed_test():
    print('Speed test started')
    speeds = [[],[],[],[],[]]
    for i in range(3):
        depth = i + 3
        original_start_time = time.time()
        trials = 0
        num_moves = 0
        print('Started depth', depth, time.ctime(time.time()))
        while time.time() - original_start_time < 600:
            board, past_board_list, piece_dict, piece_list, king_loc, squares = Game_starters.set_up('white')
            game = Game.Game(piece_dict, piece_list, board, past_board_list, [True, True],
                             [True, True], "white", king_loc)
            start_time = time.time()
            num_moves = perft(game, depth=depth)
            time_taken = time.time() - start_time
            speeds[i].append(num_moves/time_taken)
            trials += 1

        print('Finished depth', depth)

        if len(speeds[i]) > 1:
            avg_speed = np.average(speeds[i])
            speed_std = np.std(speeds[i], ddof=1)
            error = speed_std/np.sqrt(len(speeds[i]))
            print('Speed estimate for depth', depth, round(avg_speed, -1), '+-', round(error, -1))
            print('Trials:', trials)
            print('Number of nodes:', num_moves)
    print('Finished')


if __name__ == "__main__":
    # create_opening_book()
    '''
    original_start_time = time.time()
    test_config(Gv.config, Gv.original_config, test_length=1000, num_programs=10, minimax_time=10)
    time_taken = time.time() - original_start_time
    print('Time taken:', BaP.to_time(time_taken))


    original_start_time = time.time()
    test_config(Gv.config, Gv.config, test_length=1000, num_programs=10)
    time_taken = time.time() - original_start_time
    print('Time taken:', BaP.to_time(time_taken))
    '''
    speed_test()
    # main()
    # for i in range(10):
    #     get_testing_distribution(0.42, 0.1, 100 * (i + 1))
    # f = open('All_training_data')
    # a = f.readlines()
    # print(len(a))



'''
Averages:
set up 0.002+-0.001
move 28.1+-0.2
apply 9e-05+-2e-05
terminal 0.00052+-3e-05
result nan+-6e-07
'''
# 166 games 30 + 33 + 30 + 36 + 37
# 67 w wins 10 + 13 + 10 + 14 + 20
# 26 draws 6 + 6 + 7 + 5 + 2

'''
300 game test (9h):
10% sig: 160  (53.3%) (sensitivity 23 elo)
5% sig: 163  (54.3%) (sensitivity 30 elo)
1% sig: 168.5 (56.1%) (sensitivity 43 elo)
0.5% sig: 170 (56.7%) (sensitivity 48 elo)
0.1% sig: 174.5 (58.2%) (sensitivity 57 elo)


400 game test (12h):
10% sig: 211.5 (52.9%) (sensitivity 20 elo)
5% sig: 215 (53.8%) (sensitivity 26 elo)
1% sig: 221.5 (55.4%) (sensitivity 37 elo)
0.5% sig: 224 (56.0%) (sensitivity 42 elo)
0.1% sig: 230 (57.5%) (sensitivity 53 elo)
0.05% sig: 


500 game test (15h):
10% sig: 263.5 (52.7%) (sensitivity 19 elo)
5% sig: 267 (53.4%) (sensitivity 24 elo)
1% sig: 274 (54.8%) (sensitivity 33 elo)
0.5% sig: 277 (55.4%) (sensitivity 38 elo)
0.1% sig: 282 (56.4%) (sensitivity 45 elo)
'''

