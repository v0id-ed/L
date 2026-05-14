import pygame
import math
import sys
import random

pygame.init()

WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("L")

clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)

# -----------------------------
# WORLD
# -----------------------------
def tunnel(x, y):
    t = math.sin(x * 0.08) * 2 + math.sin(y * 0.05) * 2
    return abs(t) < 0.6

def is_wall(x, y):
    return not tunnel(x, y)

px, py = 0.0, 0.0
pa = 0.0

MOVE_SPEED = 0.6
ROT_SPEED = 0.02

FOV = math.pi / 3
RAYS = 120
MAX_DEPTH = 300

wall_depth_buffer = [MAX_DEPTH] * RAYS

# -----------------------------
# L SYSTEM
# -----------------------------
CHUNK_SIZE = 120
VISIBLE_CHUNKS = 1

L_objects = {}
L_count = 0

# -----------------------------
# STARS / CORRUPTION
# -----------------------------
stars = []
star_power = 0.0
collapse = False
collapse_timer = 0
rotation = 0.0


def spawn_star():
    if random.random() < 0.002 + star_power * 0.02:
        stars.append([
            random.randint(0, WIDTH),
            random.randint(0, HEIGHT),
            random.randint(1, 3)
        ])


# -----------------------------
# CHUNKS
# -----------------------------
def get_chunk(x, y):
    return int(x // CHUNK_SIZE), int(y // CHUNK_SIZE)


def generate_l_in_chunk(cx, cy):
    random.seed(cx * 928371 + cy * 123719)
    ls = []

    count = random.choices([0, 0, 1, 1, 2], weights=[60, 25, 10, 4, 1])[0]

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
# RAYCAST
# -----------------------------
def cast_world():
    start_angle = pa - FOV / 2

    for ray in range(RAYS):
        angle = start_angle + (ray / RAYS) * FOV

        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

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
                    (col, HEIGHT // 2 - wall_h // 2,
                     WIDTH // RAYS + 1, wall_h)
                )
                break


# -----------------------------
# L DRAW
# -----------------------------
def draw_Ls():
    for chunk in L_objects.values():
        for lx, ly in chunk:

            dx = lx - px
            dy = ly - py

            dist = math.hypot(dx, dy)
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

            brightness = max(40, min(120, int(255 / (1 + depth_corr * 0.02))))
            color = (brightness // 3, 0, 0)

            base = font.render("L", True, color)
            w = max(2, size // 3)
            h = max(2, size)

            sprite = pygame.transform.scale(base, (w, h))
            screen.blit(sprite, (col - w // 2, HEIGHT // 2 - h // 2))


# -----------------------------
# INTERACTION (FIXED RESET)
# -----------------------------
def check_L_interaction():
    global L_count, star_power, stars, collapse

    for chunk in list(L_objects.keys()):
        new_list = []

        for lx, ly in L_objects[chunk]:
            if math.hypot(lx - px, ly - py) < 15:
                L_count += 1

                # FULL RESET (NOW ACTUALLY WORKS)
                star_power = 0.0
                stars.clear()
                collapse = False
                collapse_timer = 0

            else:
                new_list.append((lx, ly))

        L_objects[chunk] = new_list


# -----------------------------
# STARS + COLLAPSE
# -----------------------------
def update_stars():
    global star_power, collapse, collapse_timer, rotation

    if not collapse:
        star_power += 0.002

        # STAR SPAWN (ONLY PLACE IT HAPPENS)
        if random.random() < 0.002 + star_power * 0.02:
            stars.append([
                random.randint(0, WIDTH),
                random.randint(0, HEIGHT),
                random.randint(1, 3)
            ])

    if star_power > 8:
        collapse = True

    if collapse:
        collapse_timer += 1
        rotation += 0.04


def draw_stars():
    if collapse:
        screen.fill((0, 0, 0))

        for s in stars:
            x = int(s[0] + math.sin(rotation) * 80)
            y = int(s[1] + math.cos(rotation) * 80)

            pygame.draw.circle(screen, (255, 255, 255), (x, y), s[2])

        if collapse_timer > 180:
            pygame.quit()
            sys.exit()

        return

    for s in stars:
        brightness = min(255, 200 + int(star_power * 10))
        color = (brightness, brightness, brightness)

        pygame.draw.circle(screen, color, (s[0], s[1]), s[2])


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
    update_stars()

    screen.fill((0, 0, 0))

    if not collapse:
        cast_world()
        draw_Ls()

    draw_stars()
    check_L_interaction()
    draw_ui()

    pygame.display.flip()

pygame.quit()
sys.exit()