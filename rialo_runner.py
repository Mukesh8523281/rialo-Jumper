import pygame
import random
import math

pygame.init()
pygame.mixer.init()  # enable sound

WIDTH, HEIGHT = 800, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Rialo Runner")

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
RED_GLOW = (255, 150, 150)
SPIKE_GLOW = (200, 200, 200)
YELLOW = (255, 255, 0)
BLUE = (0, 200, 255)

# Load player logo
player_img = pygame.image.load("rialo_logo.png")
player_img = pygame.transform.scale(player_img, (50, 50))

# Load background
bg_img = pygame.image.load("background.png")
bg_img_far = pygame.transform.scale(bg_img, (WIDTH, HEIGHT))
bg_img_mid = pygame.transform.scale(bg_img, (int(WIDTH*1.1), HEIGHT))
bg_far_x = 0
bg_mid_x = 0

# Load sounds
jump_sound = pygame.mixer.Sound("jump.wav")
collision_sound = pygame.mixer.Sound("collision.wav")
score_sound = pygame.mixer.Sound("score.wav")
powerup_sound = pygame.mixer.Sound("powerup.wav")

# Load background music
pygame.mixer.music.load("background_music.mp3")  # your music file
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)  # loop indefinitely

# Player setup
player_rect = player_img.get_rect()
player_rect.x = 50
player_rect.y = HEIGHT - 100
player_velocity = 0
gravity = 0.5
jump_strength = -10

def get_player_hitbox():
    return pygame.Rect(player_rect.x + 5, player_rect.y + 35, 40, 15)

# Obstacles
obstacles = []
obstacle_width = 50
spawn_timer = 0
spawn_interval = 90
obstacle_speed = 5

# Power-ups
powerups = []
POWERUP_TYPES = ["shield", "double_score"]
powerup_timer = 0

# Trail particles
trail_particles = []

# Particle system
class Particle:
    def __init__(self, x, y, color, lifetime):
        self.x = x
        self.y = y
        self.color = color
        self.lifetime = lifetime
        self.radius = random.randint(2, 4)
        self.vx = random.uniform(-0.5, 0.5)
        self.vy = random.uniform(-1, -0.5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        self.radius *= 0.96

    def draw(self, surface):
        if self.lifetime > 0:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.radius))

particles = []

# Score
score = 0
font = pygame.font.Font(None, 36)

# Game state
game_active = False
game_over = False
shield_active = False
double_score_active = False
double_score_timer = 0
shield_timer = 0

# Clock
clock = pygame.time.Clock()
bob_counter = 0
bob_speed = 0.05
bob_amount = 3

def reset_game():
    global player_rect, player_velocity, obstacles, score, game_over
    global spawn_interval, obstacle_speed, particles, powerups
    global shield_active, double_score_active, shield_timer, double_score_timer
    player_rect.y = HEIGHT - 100
    player_velocity = 0
    obstacles = []
    particles = []
    trail_particles.clear()
    powerups = []
    score = 0
    game_over = False
    spawn_interval = 90
    obstacle_speed = 5
    shield_active = False
    double_score_active = False
    shield_timer = 0
    double_score_timer = 0

# Helper
def draw_text(text, font, color, surface, x, y):
    surface.blit(font.render(text, True, color), (x, y))

# Main game loop
running = True
while running:
    dt = clock.tick(60) / 1000
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if not game_active:
                    game_active = True
                    reset_game()
                elif player_rect.y >= HEIGHT - 100:
                    player_velocity = jump_strength
                    jump_sound.play()

    if game_active:
        # Scroll backgrounds
        bg_far_x -= 1
        bg_mid_x -= 2
        if bg_far_x <= -WIDTH: bg_far_x = 0
        if bg_mid_x <= -WIDTH*1.1: bg_mid_x = 0

        screen.blit(bg_img_far, (bg_far_x, 0))
        screen.blit(bg_img_far, (bg_far_x + WIDTH, 0))
        screen.blit(bg_img_mid, (bg_mid_x, 0))
        screen.blit(bg_img_mid, (bg_mid_x + WIDTH*1.1, 0))

        # Vignette overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        screen.blit(overlay, (0, 0))

        # Player physics
        player_velocity += gravity
        player_rect.y += player_velocity
        if player_rect.y > HEIGHT - 100:
            player_rect.y = HEIGHT - 100
            player_velocity = 0

        # Running bob
        if player_rect.y >= HEIGHT - 100:
            bob_counter += bob_speed
            bob_offset = math.sin(bob_counter * 2 * math.pi) * bob_amount
        else:
            bob_offset = -5

        # Spawn obstacles
        spawn_timer += 1
        if spawn_timer > spawn_interval:
            obstacle_type = random.choice(["firewall", "spike"])
            if obstacle_type == "firewall":
                height = random.randint(60, 100)
                y_pos = HEIGHT - height
                move_pattern = {"type": "horizontal", "amplitude": random.randint(2, 6), "speed": random.uniform(0.03, 0.07)}
            else:
                height = random.randint(60, 120)
                y_pos = HEIGHT - height
                move_pattern = {"type": "vertical", "amplitude": random.randint(10, 20), "speed": random.uniform(0.03, 0.07)}
            obstacles.append({
                "rect": pygame.Rect(WIDTH, y_pos, obstacle_width, height),
                "type": obstacle_type,
                "move": move_pattern,
                "move_counter": 0
            })
            spawn_timer = 0

        # Spawn power-ups
        powerup_timer += 1
        if powerup_timer > 500:
            p_type = random.choice(POWERUP_TYPES)
            y_pos = HEIGHT - 120
            powerups.append({"rect": pygame.Rect(WIDTH, y_pos, 30, 30), "type": p_type})
            powerup_timer = 0

        # Move and draw obstacles
        for obstacle in obstacles[:]:
            obstacle["rect"].x -= obstacle_speed

            move = obstacle.get("move")
            if move:
                obstacle["move_counter"] += move["speed"]
                if move["type"] == "vertical":
                    offset = math.sin(obstacle["move_counter"] * 2 * math.pi) * move["amplitude"]
                    obstacle["rect"].y = (HEIGHT - obstacle["rect"].height) + offset
                elif move["type"] == "horizontal":
                    offset = math.sin(obstacle["move_counter"] * 2 * math.pi) * move["amplitude"]
                    obstacle["rect"].x += offset

            if obstacle["type"] == "firewall":
                glow_rect = obstacle["rect"].inflate(8, 8)
                pygame.draw.rect(screen, RED_GLOW, glow_rect)
                pygame.draw.rect(screen, RED, obstacle["rect"])
            else:
                points = [
                    (obstacle["rect"].x, obstacle["rect"].y + obstacle["rect"].height),
                    (obstacle["rect"].x + obstacle_width//2, obstacle["rect"].y),
                    (obstacle["rect"].x + obstacle_width, obstacle["rect"].y + obstacle["rect"].height)
                ]
                glow_points = [(x, y + 3) for x, y in points]
                pygame.draw.polygon(screen, SPIKE_GLOW, glow_points)
                pygame.draw.polygon(screen, WHITE, points)

            # Collision
            if get_player_hitbox().colliderect(obstacle["rect"]) and not shield_active:
                collision_sound.play()
                game_active = False
                game_over = True

            # Score update
            if obstacle["rect"].x + obstacle_width < 0:
                obstacles.remove(obstacle)
                score += 2 if double_score_active else 1
                score_sound.play()
                if score % 5 == 0 and spawn_interval > 40:
                    spawn_interval -= 2
                    obstacle_speed += 0.5

        # Move and draw power-ups
        for powerup in powerups[:]:
            powerup["rect"].x -= obstacle_speed
            color = BLUE if powerup["type"]=="shield" else YELLOW
            pygame.draw.rect(screen, color, powerup["rect"])
            if player_rect.colliderect(powerup["rect"]):
                powerup_sound.play()
                if powerup["type"] == "shield":
                    shield_active = True
                    shield_timer = 300
                else:
                    double_score_active = True
                    double_score_timer = 300
                powerups.remove(powerup)

        # Update power-up timers
        if shield_active:
            shield_timer -= 1
            if shield_timer <= 0: shield_active = False
        if double_score_active:
            double_score_timer -= 1
            if double_score_timer <= 0: double_score_active = False

        # Player trail
        trail_particles.append(Particle(player_rect.x + 25, player_rect.y + 50 + bob_offset, WHITE, 20))
        for particle in trail_particles[:]:
            particle.update()
            particle.draw(screen)
            if particle.lifetime <= 0: trail_particles.remove(particle)

        # Draw player
        screen.blit(player_img, (player_rect.x, player_rect.y + bob_offset))

        # Draw score and power-up indicators
        draw_text(f"Score: {score}", font, WHITE, screen, 10, 10)
        if shield_active: draw_text("Shield", font, BLUE, screen, 10, 40)
        if double_score_active: draw_text("2x Score", font, YELLOW, screen, 10, 70)

    elif game_over:
        screen.fill(WHITE)
        draw_text("Game Over!", font, RED, screen, WIDTH//2 - 80, HEIGHT//2 - 30)
        draw_text(f"Score: {score}", font, BLACK, screen, WIDTH//2 - 50, HEIGHT//2)
        draw_text("Press SPACE to Restart", font, BLACK, screen, WIDTH//2 - 120, HEIGHT//2 + 40)
    else:
        screen.fill(WHITE)
        draw_text("Rialo Runner", font, BLACK, screen, WIDTH//2 - 80, HEIGHT//2 - 30)
        draw_text("Press SPACE to Start", font, BLACK, screen, WIDTH//2 - 100, HEIGHT//2 + 10)

    pygame.display.flip()

pygame.quit()
