import random
import pygame


def draw_first_frame(surface, rect, px_mover, color):
    for x in range(0, rect[2]):
        for y in range(0, rect[3]):
            if y == 0:
                surface.set_at((rect[0] + x, rect[1] + y), color)
            else:
                has_color = True
                for i in range(0, y):
                    if px_mover(x, i) is None:
                        has_color = False
                if has_color:
                    surface.set_at((rect[0] + x, rect[1] + y), color)


def draw_frame(surface, rect, last_frame_rect, px_mover, color):
    for x in range(0, rect[2]):
        for y in range(0, rect[3]):
            last_frame_has_color = (color == surface.get_at((x + last_frame_rect[0],
                                                             y + last_frame_rect[1])))
            if last_frame_has_color:
                move_to = px_mover(x, y)
                if move_to is not None and move_to[1] < rect[3]:
                    move_to = (move_to[0] % rect[2], move_to[1] % rect[3])
                    surface.set_at((move_to[0] + rect[0], move_to[1] + rect[1]), color)

            if y == 0:
                surface.set_at((rect[0] + x, rect[1]), color)


if __name__ == "__main__":
    n_frames = 16
    img_size = (16, 16)
    smoke_color = (0, 0, 0)
    bg_color = (255, 255, 255)

    n_frames_plus = n_frames + 4
    test_surface = pygame.Surface((img_size[0] * n_frames_plus, img_size[1]))
    test_surface.fill(bg_color)

    height = img_size[1]

    def move_funct(x, y):
        if random.random() < (y / height) ** 2:
            # pixel disappears
            return None
        else:
            val = random.random()
            if val < 0.05:
                return (x, y)
            elif val < 0.6:
                return (x, y + 1)
            elif val < 0.8:
                return (x - 1, y + 1)
            else:
                return (x + 1, y + 1)


    last_rect = [0, 0, img_size[0], img_size[1]]
    draw_first_frame(test_surface, last_rect, move_funct, smoke_color)

    for i in range(1, n_frames_plus):
        last_rect = [(i - 1) * img_size[0], 0, img_size[0], img_size[1]]
        cur_rect = [i * img_size[0], 0, img_size[0], img_size[1]]
        draw_frame(test_surface, cur_rect, last_rect, move_funct, smoke_color)

    # slice off seeding frames
    result_surf = test_surface.subsurface((img_size[0] * (n_frames_plus - n_frames),
                                           0,
                                           img_size[0] * n_frames,
                                           img_size[1]))

    pygame.image.save(result_surf, "test_smoke.png")

