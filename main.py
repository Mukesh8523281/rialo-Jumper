import pygame
import random
import math
import sys, os

pygame.init()

# --- Helper for PyInstaller ---
def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# --- Screen ---
WIDTH, HEIGHT = 800, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Rialo Jumper")

# --- Colors ---
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
BLUE = (100, 200, 255)
PURPLE = (200, 100, 255)

# --- Load assets ---
player_img = pygame.image.load(resource_path("rialo_logo.png"))
player_img = pygame.transform.scale(player_img, (50, 50))
bg_img = pygame.image.load(resource_path("background.png"))
bg_img = pygame.transform.scale(bg_img, (WIDTH, HEIGHT))
cloud_img = pygame.image.load(resource_path("clouds.png")).convert_alpha()
cloud_img = pygame.transform.scale(cloud_img, (400, 100))  # smaller clouds

# --- Sounds ---
jump_sound = pygame.mixer.Sound(resource_path("jump.wav"))
double_jump_sound = pygame.mixer.Sound(resource_path("double_jump.wav"))
collision_sound = pygame.mixer.Sound(resource_path("collision.wav"))
score_sound = pygame.mixer.Sound(resource_path("score.wav"))
powerup_sound = pygame.mixer.Sound(resource_path("powerup.wav"))
pygame.mixer.music.load(resource_path("background_music.mp3"))
pygame.mixer.music.play(-1)

# --- Background ---
bg_x = 0
cloud_x = 0
cloud_y = 50  # clouds higher
bg_scroll_speed = 2
cloud_speed = 1

# --- Player ---
player_rect = player_img.get_rect()
player_rect.x = 50
player_rect.y = HEIGHT - 100
player_velocity = 0
gravity = 0.5
jump_strength = -12
jump_cut = 0.5
max_jumps = 2
jumps_left = max_jumps

def get_player_hitbox():
    return pygame.Rect(player_rect.x + 5, player_rect.y + 35, 40, 15)

# --- Obstacles ---
obstacles = []
obstacle_width = 50
spawn_timer = 0
spawn_interval = 90
obstacle_speed = 5

# --- Particles ---
particles = []

# --- Powerups ---
powerups = []
powerup_timer = 0
active_powerup = None
powerup_duration = 200
invincible = False

# --- Score ---
score = 0
font = pygame.font.Font(None, 36)
title_font = pygame.font.Font(None, 72)

# --- Game state ---
game_active = False
game_over = False

# --- Clock / animation ---
clock = pygame.time.Clock()
bob_counter = 0
bob_speed = 0.05
bob_amount = 3

# --- Screen shake ---
shake_timer = 0
shake_offset = [0,0]

# --- Helpers ---
def draw_text(text, font, color, surface, x, y, outline=True):
    if outline:
        shadow = font.render(text, True, BLACK)
        surface.blit(shadow, (x+2, y+2))
    surface.blit(font.render(text, True, color), (x, y))

def draw_pulse_text(text, font, color1, color2, surface, x, y, time):
    pulse = (math.sin(time * 3) + 1) / 2
    color = (
        int(color1[0] * (1 - pulse) + color2[0] * pulse),
        int(color1[1] * (1 - pulse) + color2[1] * pulse),
        int(color1[2] * (1 - pulse) + color2[2] * pulse),
    )
    text_surf = font.render(text, True, color)
    rect = text_surf.get_rect(center=(x, y))
    surface.blit(text_surf, rect)

def reset_game():
    global player_rect, player_velocity, obstacles, particles, powerups
    global score, game_over, spawn_interval, obstacle_speed
    global active_powerup, powerup_timer, invincible, jumps_left
    global shake_timer
    player_rect.y = HEIGHT - 100
    player_velocity = 0
    obstacles = []
    particles = []
    powerups = []
    score = 0
    game_over = False
    spawn_interval = 90
    obstacle_speed = 5
    active_powerup = None
    powerup_timer = 0
    invincible = False
    jumps_left = max_jumps
    shake_timer = 0

# --- Main loop ---
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
                elif jumps_left > 0:
                    player_velocity = jump_strength
                    if jumps_left == 1:
                        double_jump_sound.play()
                        for i in range(15):
                            particles.append([[player_rect.x+25, player_rect.y+45],
                                              [random.uniform(-2,2), random.uniform(-2,-1)],
                                              random.randint(4,7),
                                              YELLOW])
                    else:
                        jump_sound.play()
                    jumps_left -= 1
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE and player_velocity < 0:
                player_velocity *= jump_cut

    if game_active:
        # --- Background + clouds ---
        bg_x -= bg_scroll_speed
        if bg_x <= -WIDTH:
            bg_x = 0
        cloud_x -= cloud_speed
        if cloud_x <= -400:
            cloud_x = 0
        screen.blit(bg_img, (bg_x + shake_offset[0], shake_offset[1]))
        screen.blit(bg_img, (bg_x + WIDTH + shake_offset[0], shake_offset[1]))
        screen.blit(cloud_img, (cloud_x + shake_offset[0], cloud_y + shake_offset[1]))
        screen.blit(cloud_img, (cloud_x + 400 + shake_offset[0], cloud_y + shake_offset[1]))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))  # vignette
        screen.blit(overlay, (0, 0))

        # --- Player physics ---
        player_velocity += gravity
        player_rect.y += player_velocity
        if player_rect.y > HEIGHT - 100:
            player_rect.y = HEIGHT - 100
            player_velocity = 0
            jumps_left = max_jumps

        # --- Player bob ---
        bob_offset = math.sin(bob_counter * 2 * math.pi) * bob_amount if player_rect.y >= HEIGHT-100 else -5
        if player_rect.y >= HEIGHT-100:
            bob_counter += bob_speed
        screen.blit(player_img, (player_rect.x, player_rect.y + bob_offset + shake_offset[1]))

        # --- Particle trail ---
        particles.append([[player_rect.x+25, player_rect.y+45],
                          [random.uniform(-1,-0.5), random.uniform(-1,1)],
                          random.randint(4,6),
                          BLUE])
        for p in particles[:]:
            p[0][0] += p[1][0]
            p[0][1] += p[1][1]
            p[2] -= 0.1
            if p[2]<=0:
                particles.remove(p)
            else:
                pygame.draw.circle(screen, p[3], (int(p[0][0]), int(p[0][1])), int(p[2]))

        # --- Obstacles + collisions ---
        spawn_timer += 1
        if spawn_timer > spawn_interval:
            obstacle_type = random.choice(["firewall","spike"])
            height = random.randint(120,180) if obstacle_type=="firewall" else random.randint(100,160)
            y_pos = HEIGHT - height
            obstacles.append({"rect":pygame.Rect(WIDTH, y_pos, obstacle_width, height),"type":obstacle_type})
            if random.random() < 0.2:  # paired
                offset = random.randint(50,120)
                obstacles.append({"rect":pygame.Rect(WIDTH+offset, y_pos, obstacle_width, height),"type":obstacle_type})
            spawn_timer = 0

        for obstacle in obstacles[:]:
            obstacle["rect"].x -= obstacle_speed
            if obstacle["type"]=="firewall":
                pulse = 128 + int(127*math.sin(pygame.time.get_ticks()/200))
                glow_rect = obstacle["rect"].inflate(12,12)
                pygame.draw.rect(screen, (255,pulse,pulse), glow_rect)
                pygame.draw.rect(screen, RED, obstacle["rect"])
            else:  # spike
                obstacle["rect"].y += math.sin(pygame.time.get_ticks()/200)*2
                points = [(obstacle["rect"].x, obstacle["rect"].y+obstacle["rect"].height),
                          (obstacle["rect"].x+obstacle_width//2, obstacle["rect"].y),
                          (obstacle["rect"].x+obstacle_width, obstacle["rect"].y+obstacle["rect"].height)]
                pulse = 128 + int(127*math.sin(pygame.time.get_ticks()/200))
                glow_points = [(x, y+3) for x,y in points]
                pygame.draw.polygon(screen, (pulse,pulse,pulse), glow_points)
                pygame.draw.polygon(screen, WHITE, points)

            if not invincible and get_player_hitbox().colliderect(obstacle["rect"]):
                collision_sound.play()
                shake_timer = 10
                game_active = False
                game_over = True

            if obstacle["rect"].x + obstacle_width < 0:
                obstacles.remove(obstacle)
                score += 1
                score_sound.play()
                if score % 3 == 0 and spawn_interval > 40:
                    spawn_interval -= 2
                    obstacle_speed += 0.5

        # --- Powerups ---
        powerup_timer += 1
        if powerup_timer > 600:
            p_type = random.choice(["score_boost","slowdown","invincible"])
            powerups.append({"rect":pygame.Rect(WIDTH, random.randint(150,250),30,30),"type":p_type})
            powerup_timer = 0

        for p in powerups[:]:
            p["rect"].x -= 3
            col = YELLOW if p["type"]=="score_boost" else BLUE if p["type"]=="slowdown" else PURPLE
            pulse = 128 + int(127*math.sin(pygame.time.get_ticks()/200))
            pygame.draw.circle(screen, (pulse, pulse, col[2]), p["rect"].center, 15)
            if player_rect.colliderect(p["rect"]):
                powerup_sound.play()
                active_powerup = p["type"]
                powerups.remove(p)
                powerup_timer = 0
                if active_powerup=="score_boost":
                    score += 5
                elif active_powerup=="slowdown":
                    obstacle_speed = max(3, obstacle_speed-2)
                elif active_powerup=="invincible":
                    invincible = True

        if active_powerup:
            powerup_timer += 1
            status_text = "Score Boost!" if active_powerup=="score_boost" else "Slow Motion!" if active_powerup=="slowdown" else "Invincible!"
            draw_text(status_text, font, YELLOW, screen, 10,50)
            bar_ratio = max(0,(powerup_duration - powerup_timer)/powerup_duration)
            pygame.draw.rect(screen, WHITE, (30,70,40,6))
            col = BLUE if active_powerup=="slowdown" else YELLOW if active_powerup=="score_boost" else PURPLE
            pygame.draw.rect(screen, col, (30,70,int(40*bar_ratio),6))
            if powerup_timer>=powerup_duration:
                if active_powerup=="slowdown":
                    obstacle_speed += 2
                elif active_powerup=="invincible":
                    invincible=False
                active_powerup=None
                powerup_timer=0

        # --- Score ---
        draw_text(f"Score: {score}", font, WHITE, screen, 10,10)

        # --- Screen shake ---
        if shake_timer>0:
            shake_timer -= 1
            shake_offset[0] = random.randint(-5,5)
            shake_offset[1] = random.randint(-5,5)
        else:
            shake_offset = [0,0]

    elif game_over:
        # Background dimmed
        screen.blit(bg_img, (0, 0))
        screen.blit(cloud_img, (cloud_x, cloud_y))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # Glowing "Game Over!"
        pulse = 128 + int(127 * math.sin(pygame.time.get_ticks()/200))
        gameover_surf = title_font.render("GAME OVER", True, (pulse, 0, 0))
        gameover_rect = gameover_surf.get_rect(center=(WIDTH//2, HEIGHT//2 - 80))
        screen.blit(gameover_surf, gameover_rect)

        # Score
        draw_text(f"Score: {score}", font, WHITE, screen, WIDTH//2 - 50, HEIGHT//2)

        # Restart prompt
        draw_pulse_text("Press SPACE to Restart", font, (255, 255, 255), (255, 100, 100), screen, WIDTH//2, HEIGHT//2 + 60, pygame.time.get_ticks()/1000)

    else:  # Start screen
        screen.blit(bg_img, (0, 0))
        screen.blit(cloud_img, (cloud_x, cloud_y))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # dim background
        screen.blit(overlay, (0, 0))

        # Title
        title_surf = title_font.render("Rialo Jumper", True, (255, 215, 0))
        title_rect = title_surf.get_rect(center=(WIDTH//2, HEIGHT//2 - 60))
        screen.blit(title_surf, title_rect)

        # Pulsing "Press SPACE to Start"
        draw_pulse_text("Press SPACE to Start", font, (255, 255, 255), (200, 200, 0), screen, WIDTH//2, HEIGHT//2 + 40, pygame.time.get_ticks()/1000)

    pygame.display.flip()

pygame.quit()
