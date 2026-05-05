import pygame
import random
import math
import sys

pygame.init()

WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("???")
clock = pygame.time.Clock()

BEIGE = (222, 210, 180)
WHITE = (240, 240, 240)
BLACK = (10, 10, 10)
RED = (220, 40, 40)
GREY = (70, 70, 70)
BROWN = (120, 80, 40)
ORANGE = (255, 140, 0)

font = pygame.font.SysFont("consolas", 18)
big_font = pygame.font.SysFont("arial", 60)

# ---------------- CAT ----------------
cat_x, cat_y = WIDTH // 2, HEIGHT // 2
speed = 4

BASE_CAT_COLOR = [
    random.randint(120, 255),
    random.randint(120, 255),
    random.randint(120, 255)
]

def get_color():
    t = instability / 10
    return (
        int(BASE_CAT_COLOR[0] * (1 - t) + 120 * t),
        int(BASE_CAT_COLOR[1] * (1 - t) + 40 * t),
        int(BASE_CAT_COLOR[2] * (1 - t) + 40 * t)
    )

# ---------------- CAT DRAW ----------------
def draw_cat(surf, x, y, smile=False):
    c = get_color()

    jitter = int(instability * 0.8)
    x += random.randint(-jitter, jitter)
    y += random.randint(-jitter, jitter)

    pygame.draw.rect(surf, c, (x, y, 20, 20))

    # ears
    pygame.draw.polygon(surf, c, [(x+2, y), (x+6, y-10), (x+10, y)])
    pygame.draw.polygon(surf, c, [(x+10, y), (x+14, y-10), (x+18, y)])

    # eyes
    pygame.draw.circle(surf, WHITE, (x+6, y+8), 4)
    pygame.draw.circle(surf, WHITE, (x+14, y+8), 4)

    if smile:
        # controlled creepy grin (never flips)
        points_smile = [
            (x + 3,  y + 11),
            (x + 6,  y + 14),
            (x + 10, y + 15),
            (x + 14, y + 14),
            (x + 17, y + 11),
        ]

        pygame.draw.lines(surf, BLACK, False, points_smile, 2)

        # “uneven teeth” effect
        for i, px in enumerate(range(x + 6, x + 15, 3)):
            if i % 2 == 0:
                pygame.draw.circle(surf, BLACK, (px, y + 14), 1)

# ---------------- GAME STATE ----------------
points = 0
cube_pos = [random.randint(0, WIDTH-15), random.randint(0, HEIGHT-15)]

ending_triggered = False
ending_timer = 120

it_count = 0
it_cap = random.randint(3, 7)
tearing_active = False

# ---------------- WORLD ----------------
eyes = []
texts = []

instability = 0.0
silence_bias = 1.0

state = "normal"
state_timer = 0

system_msg = None
system_timer = 0

cooldowns = {
    "eyes": 0,
    "text": 0,
    "red": 0,
    "dupe": 0,
    "face": 0
}

# ---------------- CUBE ----------------
def draw_cube(surf):
    pygame.draw.rect(surf, ORANGE, (cube_pos[0], cube_pos[1], 15, 15))

def check_cube():
    global points, cube_pos
    cat_rect = pygame.Rect(cat_x, cat_y, 20, 20)
    cube_rect = pygame.Rect(cube_pos[0], cube_pos[1], 15, 15)

    if cat_rect.colliderect(cube_rect):
        points += 6
        cube_pos = [random.randint(0, WIDTH-15), random.randint(0, HEIGHT-15)]

# ---------------- EYES ----------------
def draw_eyes(surf):
    for e in eyes:
        ex, ey = e["x"], e["y"]

        pygame.draw.circle(surf, WHITE, (ex, ey), 6)

        dx = cat_x - ex
        dy = cat_y - ey
        dist = math.sqrt(dx*dx + dy*dy) + 0.001

        px = ex + int((dx / dist) * 2)
        py = ey + int((dy / dist) * 2)

        pygame.draw.circle(surf, BLACK, (px, py), 3)

# ---------------- TEXT ----------------
def spawn_text():
    texts.append({
        "t": random.choice([
            "it remembers",
            "you are being observed",
            "something is wrong",
            "do not continue"
        ]),
        "x": random.randint(0, WIDTH),
        "y": random.randint(0, HEIGHT),
        "life": 100
    })

def draw_texts(world):
    for t in texts[:]:
        world.blit(font.render(t["t"], True, RED), (t["x"], t["y"]))
        t["life"] -= 1
        if t["life"] <= 0:
            texts.remove(t)

# ---------------- SYSTEM UI ----------------
def update_system():
    global system_msg, system_timer

    if system_msg is None and random.random() < 0.002 + instability * 0.001:
        system_msg = random.choice([
            "tracking movement",
            "input logged",
            "state unstable",
            "pattern detected",
            "anomaly forming"
        ])
        system_timer = random.randint(80, 140)

    if system_msg:
        system_timer -= 1
        if system_timer <= 0:
            system_msg = None

def draw_system(world):
    if system_msg:
        pygame.draw.rect(world, GREY, (10, 10, 300, 40))
        world.blit(font.render(system_msg, True, WHITE), (20, 20))

# ---------------- EVENTS ----------------
def face_jumpscare(world):
    world.fill(BLACK)

    messages = [
        "IT IS HERE","DO NOT LOOK","YOU SAW IT","STAY STILL",
        "TURN BACK","IT FOUND YOU","DON'T MOVE","YOU CAN'T LEAVE",
        "TOO LATE","WHY DID YOU LOOK"
    ]

    for _ in range(random.randint(1, 4)):
        size = random.randint(40, 80)
        f = pygame.font.SysFont("arial", size)
        txt = f.render(random.choice(messages), True, RED)

        x = WIDTH//2 - txt.get_width()//2 + random.randint(-120, 120)
        y = HEIGHT//2 - txt.get_height()//2 + random.randint(-80, 80)

        world.blit(txt, (x, y))

# ---------------- RED FLOOD ----------------
def red_flood(world):
    for _ in range(40):
        world.blit(font.render("ERROR", True, RED),
                   (random.randint(0, WIDTH), random.randint(0, HEIGHT)))

# ---------------- DUPES ----------------
def spawn_dupes(world):
    for _ in range(10):
        pygame.draw.rect(world, get_color(),
                         (cat_x + random.randint(-80, 80),
                          cat_y + random.randint(-80, 80), 20, 20))

# ---------------- TEARING ----------------
def apply_tearing(surface):
    if not tearing_active:
        return surface

    out = surface.copy()

    direction = random.choice(["horizontal", "vertical", "diagonal"])
    pos = random.randint(0, HEIGHT if direction == "horizontal" else WIDTH)
    thickness = random.randint(10, 25)

    for i in range(thickness):

        if direction == "horizontal":
            y = pos + i
            if 0 <= y < HEIGHT:
                shift = random.randint(-80, 80)
                strip = surface.subsurface((0, y, WIDTH, 1))
                out.blit(strip, (shift, y))

        elif direction == "vertical":
            x = pos + i
            if 0 <= x < WIDTH:
                shift = random.randint(-80, 80)
                strip = surface.subsurface((x, 0, 1, HEIGHT))
                out.blit(strip, (x, shift))

        else:
            x = pos + i
            y = pos + i
            if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                try:
                    block = surface.subsurface((x, y, 4, 4))
                    out.blit(block, (x + random.randint(-40, 40),
                                     y + random.randint(-40, 40)))
                except:
                    pass

        for _ in range(5):
            pygame.draw.rect(out, random.choice([RED, BLACK]),
                              (random.randint(0, WIDTH), random.randint(0, HEIGHT), 2, 2))

    return out

# ---------------- ANOMALIES ----------------
def update_anomalies(world):
    global silence_bias, state, state_timer, it_count, tearing_active, points

    silence_bias += 0.002
    threshold = random.random() * silence_bias

    for k in cooldowns:
        cooldowns[k] = max(0, cooldowns[k] - 1)

    if instability > threshold:
        silence_bias = 1.0

        options = [k for k in cooldowns if cooldowns[k] == 0]
        if not options:
            options = ["text"]

        chosen = random.choice(options)
        cooldowns[chosen] = random.randint(120, 200)

        if chosen == "eyes":
            for _ in range(3):
                eyes.append({"x": random.randint(0, WIDTH),
                             "y": random.randint(0, HEIGHT)})

        elif chosen == "text":
            spawn_text()

        elif chosen == "dupe":
            spawn_dupes(world)

        elif chosen == "face":
            state = "face"
            state_timer = 25
            it_count += 1

            if it_count > it_cap:
                tearing_active = True
                points = 0

        elif chosen == "red":
            state = "red"
            state_timer = 40

# ---------------- MAIN LOOP ----------------
running = True

while running:

    world = pygame.Surface((WIDTH, HEIGHT))
    world.fill((222, 210, 180))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    if not ending_triggered:
        if keys[pygame.K_LEFT]: cat_x -= 4
        if keys[pygame.K_RIGHT]: cat_x += 4
        if keys[pygame.K_UP]: cat_y -= 4
        if keys[pygame.K_DOWN]: cat_y += 4

    cat_x = max(0, min(WIDTH-20, cat_x))
    cat_y = max(0, min(HEIGHT-20, cat_y))

    instability = max(0, min(10,
        instability + (0.01 if any(keys) else -0.005)
    ))

    update_system()
    update_anomalies(world)
    check_cube()

    if points >= 66 and not ending_triggered:
        ending_triggered = True

    draw_texts(world)
    draw_eyes(world)
    draw_system(world)
    draw_cube(world)

    if state == "face":
        face_jumpscare(world)
        state_timer -= 1
        if state_timer <= 0:
            state = "normal"

    elif state == "red":
        red_flood(world)
        state_timer -= 1
        if state_timer <= 0:
            state = "normal"

    if ending_triggered:
        ending_timer -= 1
        draw_cat(world, cat_x, cat_y, smile=True)

        if ending_timer <= 0:
            pygame.quit()
            sys.exit()
    else:
        draw_cat(world, cat_x, cat_y)

    world.blit(font.render(f"POINTS: {points}", True, BROWN),
               (WIDTH-180, 10))

    final = apply_tearing(world)
    screen.blit(final, (0, 0))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
