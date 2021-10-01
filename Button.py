import Bits_and_Pieces as BaP
import Global_variables as Gv
import pygame


# class for any kind of button in the program
class Button(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, text="", font_size=10,
                 text_colour=Gv.absolute_black, colour=Gv.light_grey, font="Calibri", left_align=True):
        super().__init__()
        self.width = width
        self.height = height
        self.colour = colour
        self.text = text
        self.image = pygame.Surface([width, height])
        self.image.fill(colour)
        BaP.print_screen(self.image, text, width//2, height//2, font_size, text_colour, False, font_type=font)
        self.rect = self.image.get_rect()
        if left_align:
            self.rect.x = x
        else:
            self.rect.x = x - width//2
        self.rect.y = y
        self.font_size = font_size
        self.text_colour = text_colour
        self.font = font

    # given coordinates of a click this returns a boolean saying whether or not the button has been clicked
    def is_clicked(self, mouse_x, mouse_y):
        if self.rect.x < mouse_x < self.rect.x + self.width and self.rect.y < mouse_y < self.rect.y + self.height:
            return True
        else:
            return False

    # Moves the button a small amount, called when the mouse passes over the button in the menu
    def jitter(self, screen):
        self.image.fill(Gv.background_colour)
        screen.blit(self.image, (self.rect.x, self.rect.y))
        self.rect.x += 5
        self.rect.y -= 5
        BaP.print_screen(self.image, self.text, self.width // 2, self.height // 2, self.font_size, self.text_colour,
                         False, self.font)
        pygame.display.flip()

    # returns the button to its original position
    def un_jitter(self, screen):
        self.image.fill(Gv.background_colour)
        screen.blit(self.image, (self.rect.x, self.rect.y))
        self.rect.x -= 5
        self.rect.y += 5
        BaP.print_screen(self.image, self.text, self.width // 2, self.height // 2, self.font_size, self.text_colour,
                         False, self.font)
        pygame.display.flip()


# class for buttons which are just labelled with images, such as arrows
class ImageButton(Button):
    def __init__(self, x, y, width, height, image):
        super().__init__(x, y, width, height)
        self.image.fill(Gv.absolute_white)
        picture = BaP.load_image(image)
        picture = pygame.transform.scale(picture, (width, height))
        self.image.blit(picture, (0, 0))
