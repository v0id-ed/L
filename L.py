import pygame
import math
import random
import sys

pygame.init()

WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# ---------------- WORLD ----------------
MAP_SIZE = 20
WORLD_SEED = random.randint(0, 999999)
random.seed(WORLD_SEED)

def generate_world():
    grid = [[1 for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]

    room_count = random.randint(6, 12)

    for _ in range(room_count):

        w = random.randint(3, 7)
        h = random.randint(3, 7)

        x = random.randint(1, MAP_SIZE - w - 2)
        y = random.randint(1, MAP_SIZE - h - 2)

        # carve room
        for iy in range(y, y + h):
            for ix in range(x, x + w):
                grid[iy][ix] = 0

        # corridor connection (liminal broken layout feel)
        if random.random() < 0.7:
            cx = x + w // 2
            cy = y + h // 2

            for i in range(random.randint(3, 6)):
                if random.random() < 0.5:
                    if cy + i < MAP_SIZE:
                        grid[cy + i][cx] = 0
                else:
                    if cx + i < MAP_SIZE:
                        grid[cy][cx + i] = 0

    return grid

world = generate_world()

# ---------------- PLAYER ----------------
px, py = MAP_SIZE // 2 + 0.5, MAP_SIZE // 2 + 0.5
angle = 0

FOV = math.pi / 3
DEPTH = 20

# ---------------- GHOST ENTITIES ----------------
entities = []

def spawn_entity():
    # rare direct manifestation in front of player
    if random.random() < 0.08:
        ex = px + math.cos(angle) * random.uniform(1.5, 2.5)
        ey = py + math.sin(angle) * random.uniform(1.5, 2.5)
        mode = "manifest"
    else:
        side = random.choice(["top", "bottom", "left", "right"])

        if side == "top":
            ex, ey = random.randint(0, MAP_SIZE), 0
        elif side == "bottom":
            ex, ey = random.randint(0, MAP_SIZE), MAP_SIZE - 1
        elif side == "left":
            ex, ey = 0, random.randint(0, MAP_SIZE)
        else:
            ex, ey = MAP_SIZE - 1, random.randint(0, MAP_SIZE)

        ex += random.uniform(-0.5, 0.5)
        ey += random.uniform(-0.5, 0.5)
        mode = "peripheral"

    entities.append({
        "x": ex,
        "y": ey,
        "life": random.randint(35, 85),
        "phase": random.uniform(0, math.pi * 2),
        "seen": False,
        "mode": mode
    })

def update_entities():
    global entities

    for e in entities:
        e["life"] -= 1
        e["phase"] += 0.08

        # ghost drift (not physical movement)
        e["x"] += math.sin(e["phase"]) * 0.01
        e["y"] += math.cos(e["phase"]) * 0.01

        dx = e["x"] - px
        dy = e["y"] - py
        dist = math.sqrt(dx * dx + dy * dy)

        angle_to = math.atan2(dy, dx)
        diff = (angle_to - angle + math.pi) % (2 * math.pi) - math.pi

        in_view = abs(diff) < 0.3 and dist < 8

        if in_view:
            e["seen"] = True
            e["life"] -= 3  # observation collapses it faster

    entities = [e for e in entities if e["life"] > 0]

def draw_entities():
    for e in entities:

        dx = e["x"] - px
        dy = e["y"] - py

        dist = math.sqrt(dx * dx + dy * dy)
        angle_to = math.atan2(dy, dx)
        diff = (angle_to - angle + math.pi) % (2 * math.pi) - math.pi

        if abs(diff) < 0.5 and dist < 10:

            screen_x = WIDTH // 2 + (diff / FOV) * WIDTH
            base_y = HEIGHT // 2

            size = 200 / (dist + 0.1)

            # ghost instability fade
            shade = max(20, 200 - int(dist * 20))
            col = (shade // 8, 0, 0)

            jitter_x = random.randint(-2, 2)
            jitter_y = random.randint(-2, 2)

            # ---------------- BODY ----------------
            body_w = size * random.uniform(0.3, 0.6)
            body_h = size * random.uniform(1.4, 2.4)

            pygame.draw.rect(
                screen,
                col,
                (screen_x - body_w // 2 + jitter_x,
                 base_y - body_h + jitter_y,
                 body_w,
                 body_h)
            )

            # ---------------- HEAD ----------------
            head_r = max(4, size * 0.3)

            head_x = screen_x + jitter_x
            head_y = base_y - body_h + jitter_y

            pygame.draw.circle(
                screen,
                col,
                (int(head_x), int(head_y)),
                int(head_r)
            )

            # ---------------- FACE (unstable apparition) ----------------
            face_chance = random.random()

            if face_chance < 0.5:
                # empty void face
                pass

            elif face_chance < 0.8:
                # misaligned eyes
                pygame.draw.circle(screen, (0, 0, 0),
                                   (int(head_x - head_r * 0.3), int(head_y - 2)), 2)
                pygame.draw.circle(screen, (0, 0, 0),
                                   (int(head_x + head_r * 0.3), int(head_y)), 2)

            else:
                # faint mouth line
                pygame.draw.line(
                    screen,
                    (20, 0, 0),
                    (head_x - 4, head_y + 3),
                    (head_x + 4, head_y + 3),
                    1
                )

# ---------------- RAYCAST ----------------
def cast_rays():
    screen.fill((10, 10, 10))

    num_rays = 200

    for i in range(num_rays):
        ray_angle = angle - FOV / 2 + (i / num_rays) * FOV

        for depth in range(1, DEPTH * 10):

            tx = px + math.cos(ray_angle) * (depth * 0.1)
            ty = py + math.sin(ray_angle) * (depth * 0.1)

            ix, iy = int(tx), int(ty)

            if 0 <= ix < MAP_SIZE and 0 <= iy < MAP_SIZE:

                if world[iy][ix] == 1:

                    shade = 255 / (1 + depth * depth * 0.02)
                    color = (shade, shade, shade)

                    wall_h = HEIGHT / (depth * 0.1 + 0.0001)

                    pygame.draw.rect(
                        screen,
                        color,
                        (i * (WIDTH // num_rays),
                         HEIGHT // 2 - wall_h // 2,
                         WIDTH // num_rays + 1,
                         wall_h)
                    )
                    break

# ---------------- MOVEMENT ----------------
def move():
    global px, py, angle

    keys = pygame.key.get_pressed()

    if keys[pygame.K_LEFT]:
        angle -= 0.03
    if keys[pygame.K_RIGHT]:
        angle += 0.03

    dx = math.cos(angle) * 0.05
    dy = math.sin(angle) * 0.05

    def blocked(x, y):
        if 0 <= int(x) < MAP_SIZE and 0 <= int(y) < MAP_SIZE:
            return world[int(y)][int(x)] == 1
        return True

    if keys[pygame.K_UP]:
        nx, ny = px + dx, py + dy
        if not blocked(nx, ny):
            px, py = nx, ny

    if keys[pygame.K_DOWN]:
        nx, ny = px - dx, py - dy
        if not blocked(nx, ny):
            px, py = nx, ny

# ---------------- WORLD DRIFT ----------------
def drift_world():
    if random.random() < 0.01:
        x = random.randint(1, MAP_SIZE - 2)
        y = random.randint(1, MAP_SIZE - 2)
        world[y][x] = 1 - world[y][x]

def soft_world_shift():
    global world

    # extremely subtle instability (does NOT ruin layout)
    if random.random() < 0.002:
        x = random.randint(1, MAP_SIZE - 2)
        y = random.randint(1, MAP_SIZE - 2)

        world[y][x] = 1 - world[y][x]

# ---------------- MAIN LOOP ----------------
running = True
spawn_timer = 0

while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    move()
    drift_world()
    update_entities()
    soft_world_shift()

    spawn_timer += 1
    if spawn_timer > random.randint(50, 100):
        spawn_entity()
        spawn_timer = 0

    cast_rays()
    draw_entities()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()