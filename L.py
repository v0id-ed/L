import pygame
import math
import sys

pygame.init()

WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("L")

clock = pygame.time.Clock()

# Player
px, py = 0.0, 0.0
pa = 0.0

MOVE_SPEED = 0.6
ROT_SPEED = 0.02

FOV = math.pi / 3
RAYS = 120
MAX_DEPTH = 300


# -----------------------------
# TUNNEL FUNCTION (NO OPEN ROOMS)
# -----------------------------
def tunnel(x, y):
    t = math.sin(x * 0.08) * 2 + math.sin(y * 0.05) * 2
    return abs(t) < 0.6  # narrow guaranteed tunnel


def is_wall(x, y):
    return not tunnel(x, y)


# -----------------------------
# RAYCASTING
# -----------------------------
def cast_world():
    screen.fill((0, 0, 0))

    start_angle = pa - FOV / 2

    for ray in range(RAYS):
        angle = start_angle + (ray / RAYS) * FOV

        sin_a = math.sin(angle)
        cos_a = math.cos(angle)

        for depth in range(1, MAX_DEPTH):
            x = px + cos_a * depth
            y = py + sin_a * depth

            if is_wall(x, y):

                # fix fisheye distortion
                depth *= math.cos(pa - angle)

                shade = 255 / (1 + depth * depth * 0.0012)
                shade = max(0, min(120, int(shade)))

                color = (shade, 0, 0)  # dark red horror walls

                wall_h = min(HEIGHT, 4500 / (depth + 0.1))

                col = int(ray * (WIDTH / RAYS))

                pygame.draw.rect(
                    screen,
                    color,
                    (col,
                     HEIGHT // 2 - wall_h // 2,
                     WIDTH // RAYS + 1,
                     wall_h)
                )
                break


# -----------------------------
# MOVEMENT (SLOW + STABLE)
# -----------------------------
def move():
    global px, py, pa

    keys = pygame.key.get_pressed()

    if keys[pygame.K_LEFT]:
        pa -= ROT_SPEED
    if keys[pygame.K_RIGHT]:
        pa += ROT_SPEED

    dx = math.cos(pa) * MOVE_SPEED
    dy = math.sin(pa) * MOVE_SPEED

    if keys[pygame.K_UP]:
        if not is_wall(px + dx, py):
            px += dx
        if not is_wall(px, py + dy):
            py += dy

    if keys[pygame.K_DOWN]:
        if not is_wall(px - dx, py):
            px -= dx
        if not is_wall(px, py - dy):
            py -= dy


# -----------------------------
# MAIN LOOP
# -----------------------------
running = True
while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    move()
    cast_world()

    pygame.display.flip()

pygame.quit()
sys.exit()