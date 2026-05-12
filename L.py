import pygame
import math
import sys
import random
import time

pygame.init()

WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("L")

clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)

# -----------------------------
# WORLD SHAPE (MUST BE FIRST)
# -----------------------------
def tunnel(x, y):
    t = math.sin(x * 0.08) * 2 + math.sin(y * 0.05) * 2
    return abs(t) < 0.6

def is_wall(x, y):
    return not tunnel(x, y)


# -----------------------------
# PLAYER
# -----------------------------
px, py = 0.0, 0.0
pa = 0.0

MOVE_SPEED = 0.6
ROT_SPEED = 0.02

FOV = math.pi / 3
RAYS = 120
MAX_DEPTH = 300


# -----------------------------
# WORLD / L SYSTEM
# -----------------------------
CHUNK_SIZE = 120
VISIBLE_CHUNKS = 1

L_objects = {}
wall_depth_buffer = [MAX_DEPTH] * RAYS
L_count = 0


# -----------------------------
# STALKER SYSTEM
# -----------------------------
stalker_x, stalker_y = 0, 0
stalker_speed = 0.45

stalker_lock = False
glitch_timer = 0


def reset_stalker():
    global stalker_x, stalker_y

    for _ in range(300):

        # 70% far, 30% near
        if random.random() < 0.7:
            dist = random.uniform(200, 450)
        else:
            dist = random.uniform(40, 120)

        angle = random.uniform(0, math.tau)

        x = px + math.cos(angle) * dist
        y = py + math.sin(angle) * dist

        if not is_wall(x, y):
            stalker_x = x
            stalker_y = y
            return

    stalker_x, stalker_y = px + 80, py + 80


reset_stalker()


# -----------------------------
# CHUNK SYSTEM
# -----------------------------
def get_chunk(x, y):
    return int(x // CHUNK_SIZE), int(y // CHUNK_SIZE)


def generate_l_in_chunk(cx, cy):
    random.seed(cx * 928371 + cy * 123719)

    ls = []

    count = random.choices(
        [0, 0, 1, 1, 2],
        weights=[60, 25, 10, 4, 1]
    )[0]

    for _ in range(count):
        for _try in range(10):

            lx = cx * CHUNK_SIZE + random.uniform(0, CHUNK_SIZE)
            ly = cy * CHUNK_SIZE + random.uniform(0, CHUNK_SIZE)

            if not is_wall(lx, ly):
                ls.append((lx, ly))
                break

    return ls


def update_Ls():
    player_chunk = get_chunk(px, py)

    for cx in range(player_chunk[0] - VISIBLE_CHUNKS,
                     player_chunk[0] + VISIBLE_CHUNKS + 1):
        for cy in range(player_chunk[1] - VISIBLE_CHUNKS,
                         player_chunk[1] + VISIBLE_CHUNKS + 1):

            key = (cx, cy)

            if key not in L_objects:
                L_objects[key] = generate_l_in_chunk(cx, cy)


# -----------------------------
# MOVEMENT
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
# RAYCAST WORLD
# -----------------------------
def cast_world():
    screen.fill((0, 0, 0))

    start_angle = pa - FOV / 2

    for ray in range(RAYS):
        angle = start_angle + (ray / RAYS) * FOV

        sin_a = math.sin(angle)
        cos_a = math.cos(angle)

        wall_depth_buffer[ray] = MAX_DEPTH

        for depth in range(1, MAX_DEPTH):
            x = px + cos_a * depth
            y = py + sin_a * depth

            if is_wall(x, y):

                wall_depth_buffer[ray] = depth

                depth_corr = max(0.1, depth * math.cos(pa - angle))

                shade = max(0, min(120, int(255 / (1 + depth_corr * 0.02))))
                color = (shade, 0, 0)

                wall_h = min(HEIGHT, 4500 / depth_corr)
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
# DRAW Ls
# -----------------------------
def draw_Ls():

    for chunk in L_objects.values():
        for lx, ly in chunk:

            dx = lx - px
            dy = ly - py

            dist = math.hypot(dx, dy)
            if dist < 0.1:
                continue

            angle = math.atan2(dy, dx)
            rel = (angle - pa + math.pi) % (2 * math.pi) - math.pi

            if abs(rel) > FOV / 2:
                continue

            ray = int((rel + FOV / 2) / FOV * RAYS)
            if ray < 0 or ray >= RAYS:
                continue

            if dist > wall_depth_buffer[ray]:
                continue

            depth_corr = max(1.0, dist * math.cos(rel))

            size = int(2800 / depth_corr)
            size = max(6, min(size, 260))

            col = int(ray * (WIDTH / RAYS))

            shade = max(50, min(120, int(255 / (1 + depth_corr * 0.02))))
            color = (shade // 3, 0, 0)

            base = font.render("L", True, color)

            w = max(2, size // 3)
            h = max(2, size)

            sprite = pygame.transform.scale(base, (w, h))

            screen.blit(sprite, (col - w // 2, HEIGHT // 2 - h // 2))


# -----------------------------
# STALKER AI
# -----------------------------
def update_stalker():
    global stalker_x, stalker_y, stalker_lock, glitch_timer

    if stalker_lock:
        glitch_timer += 1
        return

    dx = px - stalker_x
    dy = py - stalker_y

    dist = math.hypot(dx, dy)

    if dist < 10:
        stalker_lock = True
        glitch_timer = 0
        return

    dx /= dist
    dy /= dist

    speed = stalker_speed
    if dist < 80:
        speed = 0.9
    elif dist < 150:
        speed = 0.6

    nx = stalker_x + dx * speed
    ny = stalker_y + dy * speed

    if not is_wall(nx, stalker_y):
        stalker_x = nx
    if not is_wall(stalker_x, ny):
        stalker_y = ny


def draw_stalker():

    if stalker_lock:
        screen.fill((0, 0, 0))

        for _ in range(25):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            size = random.randint(80, 500)

            surf = font.render("STALKER", True, (255, 0, 0))
            surf = pygame.transform.scale(surf, (size, size // 2))

            screen.blit(surf, (x, y))

        if glitch_timer > 180:
            pygame.quit()
            sys.exit()

        return

    dx = stalker_x - px
    dy = stalker_y - py

    dist = math.hypot(dx, dy)

    angle = math.atan2(dy, dx)
    rel = (angle - pa + math.pi) % (2 * math.pi) - math.pi

    if abs(rel) > FOV / 2:
        return

    ray = int((rel + FOV / 2) / FOV * RAYS)
    if ray < 0 or ray >= RAYS:
        return

    depth_corr = max(1.0, dist)

    size = int(2500 / depth_corr)
    size = max(40, min(size, 400))

    col = int(ray * (WIDTH / RAYS))

    surf = font.render("STALKER", True, (255, 0, 0))
    surf = pygame.transform.scale(surf, (size, size // 2))

    screen.blit(surf, (col - size // 2, HEIGHT // 2 - size // 4))


# -----------------------------
# INTERACTION
# -----------------------------
def check_L_interaction():
    global L_count

    for chunk in list(L_objects.keys()):
        new_list = []

        for lx, ly in L_objects[chunk]:
            if math.hypot(lx - px, ly - py) < 15:
                L_count += 1
            else:
                new_list.append((lx, ly))

        L_objects[chunk] = new_list


# -----------------------------
# UI
# -----------------------------
def draw_ui():
    text = font.render(f"{L_count}/6", True, (139, 69, 19))
    screen.blit(text, (WIDTH - 100, 20))


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

    update_Ls()
    update_stalker()

    cast_world()
    draw_stalker()
    draw_Ls()
    check_L_interaction()
    draw_ui()

    pygame.display.flip()

pygame.quit()
sys.exit()