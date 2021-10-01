import Global_variables as Gv
import Bits_and_Pieces as BaP
import Button
import pygame


# displays the menu on screen and returns the user's choice
def menu(screen):
    font = "Calibri"

    # sets up the buttons
    buttons = pygame.sprite.Group()
    button_list = []
    x = Gv.screen_width // 2
    y = 2.5 * Gv.square_size
    spacing = 1.3 * Gv.square_size
    width = Gv.screen_width // 2
    height = spacing
    text_size = 1.3 * Gv.square_size

    # prints menu on screen
    screen.fill(Gv.background_colour)
    BaP.print_screen(screen, "Menu", Gv.screen_width // 2, Gv.screen_height // 10, Gv.square_size * 2, Gv.text_colour,
                     False, font)

    # draws the buttons to the screen
    names = ["2 Player", "Computer", "Saved Games", "Instructions", "Settings"]
    for i in range(len(names)):
        button = Button.Button(x, y + i * spacing, width, height, names[i], text_size, Gv.text_colour,
                               Gv.background_colour, font, False)
        buttons.add(button)
        button_list.append(button)
    buttons.draw(screen)
    pygame.display.flip()

    # loops through until the menu has either been quit or an option has been clicked
    clicked = False
    quit = False
    while not clicked:
        chosen = False
        mouse_x = 0
        mouse_y = 0
        jittered = None

        while not chosen:
            mouse_x, mouse_y = pygame.mouse.get_pos()

            # performs the jittering effect on the buttons
            if jittered is None:
                for i in range(len(button_list)):
                    if button_list[i].is_clicked(mouse_x, mouse_y):
                        button_list[i].jitter(screen)
                        jittered = i

            if jittered is not None:
                for i in range(len(button_list)):
                    if jittered == i and not button_list[i].is_clicked(mouse_x, mouse_y):
                        button_list[i].un_jitter(screen)
                        jittered = None

            buttons.draw(screen)
            pygame.display.flip()

            # checks if the user has clicked on something
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONUP:
                    chosen = True
                elif event.type == pygame.QUIT:
                    quit = True
                    chosen = True

        # returns the option chosen
        for i in range(len(button_list)):
            if button_list[i].is_clicked(mouse_x, mouse_y):
                return i, False
        if quit:
            return None, True
