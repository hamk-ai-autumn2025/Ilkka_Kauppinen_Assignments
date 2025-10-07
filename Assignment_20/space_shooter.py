# space_shooter.py
import math
import random
import sys
import pygame
from pygame import Vector2

# ---------- Configuration ----------
WIDTH, HEIGHT = 900, 600
FPS = 60

# Player settings
PLAYER_SPEED = 340        # pixels per second
PLAYER_SIZE = (48, 36)
PLAYER_FIRE_COOLDOWN = 0.18  # seconds

# Bullet settings
BULLET_SPEED = 700
BULLET_SIZE = (6, 14)

# Enemy settings
ENEMY_SPEED_MIN = 60
ENEMY_SPEED_MAX = 140
ENEMY_SPAWN_INTERVAL = 1.0  # seconds
ENEMY_SIZE = (42, 30)

# Particle settings (for explosions)
PARTICLE_COUNT = 18
PARTICLE_SPEED = 180
PARTICLE_LIFETIME = 0.6

# Colors (pleasant pastel palette)
PALETTE = {
    "bg_dark": (12, 18, 33),
    "bg_soft": (18, 28, 50),
    "star1": (255, 236, 219),
    "star2": (230, 241, 255),
    "player": (142, 215, 206),
    "player_shade": (69, 138, 128),
    "bullet": (255, 180, 178),
    "enemy": (255, 157, 168),
    "enemy_shade": (225, 110, 123),
    "ui": (200, 220, 255),
    "particle": (255, 205, 170)
}

# ---------- Pygame init ----------
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pastel Space Shooter")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 28)


# ---------- Utilities ----------
def clamp(v, a, b):
    return max(a, min(b, v))


# ---------- Visual Helpers ----------
def rounded_rect(surface, rect, color, radius=6):
    """Draw a rounded rect on surface (helpful for UI)"""
    x, y, w, h = rect
    pygame.draw.rect(surface, color, (x + radius, y, w - 2 * radius, h))
    pygame.draw.rect(surface, color, (x, y + radius, w, h - 2 * radius))
    pygame.draw.circle(surface, color, (x + radius, y + radius), radius)
    pygame.draw.circle(surface, color, (x + w - radius, y + radius), radius)
    pygame.draw.circle(surface, color, (x + radius, y + h - radius), radius)
    pygame.draw.circle(surface, color, (x + w - radius, y + h - radius), radius)


# ---------- Sprites ----------
class Player(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.base_image = self.make_image()
        self.image = self.base_image
        self.rect = self.image.get_rect(center=pos)
        self.pos = Vector2(pos)
        self.vel = Vector2(0, 0)
        self.fire_timer = 0.0
        self.score = 0
        self.lives = 3

    def make_image(self):
        surf = pygame.Surface(PLAYER_SIZE, pygame.SRCALPHA)
        w, h = PLAYER_SIZE
        # main body
        pygame.draw.polygon(
            surf,
            PALETTE["player"],
            [(w * 0.5, 0), (w, h * 0.75), (w * 0.7, h * 0.75), (w * 0.5, h * 0.45),
             (w * 0.3, h * 0.75), (0, h * 0.75)]
        )
        # cockpit
        pygame.draw.ellipse(surf, PALETTE["player_shade"], (w * 0.35, h * 0.15, w * 0.3, h * 0.28))
        return surf

    def update(self, dt, keys):
        # Movement input
        move = Vector2(0, 0)
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move.x -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move.x += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            move.y -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            move.y += 1
        if move.length_squared() > 0:
            move = move.normalize()
        self.vel = move * PLAYER_SPEED
        self.pos += self.vel * dt
        # keep on screen
        self.pos.x = clamp(self.pos.x, self.rect.width / 2, WIDTH - self.rect.width / 2)
        self.pos.y = clamp(self.pos.y, self.rect.height / 2, HEIGHT - self.rect.height / 2)
        self.rect.center = self.pos

        # tilt effect
        tilt = -self.vel.x / PLAYER_SPEED * 12  # degrees
        self.image = pygame.transform.rotozoom(self.base_image, tilt, 1.0)

        # fire timer
        self.fire_timer = max(0.0, self.fire_timer - dt)

    def can_shoot(self):
        return self.fire_timer <= 0.0

    def shoot(self):
        self.fire_timer = PLAYER_FIRE_COOLDOWN


class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface(BULLET_SIZE, pygame.SRCALPHA)
        # soft rounded bullet
        pygame.draw.rect(self.image, PALETTE["bullet"], self.image.get_rect(), border_radius=4)
        self.rect = self.image.get_rect(center=pos)
        self.pos = Vector2(pos)
        self.vel = Vector2(0, -BULLET_SPEED)

    def update(self, dt):
        self.pos += self.vel * dt
        self.rect.center = self.pos
        if self.rect.bottom < -20:
            self.kill()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos, speed):
        super().__init__()
        self.base_image = self.make_image()
        self.image = self.base_image
        self.rect = self.image.get_rect(center=pos)
        self.pos = Vector2(pos)
        self.speed = speed
        # slight oscillation for a bit of personality
        self.phase = random.random() * math.pi * 2
        self.osc_amp = random.uniform(8, 26)

    def make_image(self):
        surf = pygame.Surface(ENEMY_SIZE, pygame.SRCALPHA)
        w, h = ENEMY_SIZE
        pygame.draw.ellipse(surf, PALETTE["enemy"], (0, 0, w, h))
        # stylized "mouth" or stripe
        pygame.draw.arc(surf, PALETTE["enemy_shade"], (w * 0.12, h * 0.25, w * 0.76, h * 0.6), math.radians(200), math.radians(340), 4)
        return surf

    def update(self, dt):
        # Move down, with horizontal wobble
        self.phase += dt * 4.0
        wobble = math.sin(self.phase) * self.osc_amp
        self.pos += Vector2(wobble * dt, self.speed * dt)
        self.rect.center = self.pos
        if self.rect.top > HEIGHT + 40:
            self.kill()


class Particle(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.pos = Vector2(pos)
        angle = random.random() * math.tau
        speed = random.random() * PARTICLE_SPEED
        self.vel = Vector2(math.cos(angle), math.sin(angle)) * speed
        self.lifetime = random.uniform(PARTICLE_LIFETIME * 0.6, PARTICLE_LIFETIME)
        self.age = 0.0
        size = random.randint(2, 6)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, PALETTE["particle"], (size // 2, size // 2), size // 2)
        self.rect = self.image.get_rect(center=self.pos)

    def update(self, dt):
        self.age += dt
        if self.age >= self.lifetime:
            self.kill()
            return
        # simple physics + fade
        self.pos += self.vel * dt
        self.vel *= 0.98  # gentle drag
        alpha = int(255 * (1.0 - (self.age / self.lifetime)))
        self.image.set_alpha(alpha)
        self.rect.center = self.pos


# ---------- Starfield for parallax ----------
class Star:
    def __init__(self, x, y, size, layer):
        self.pos = Vector2(x, y)
        self.size = size
        self.layer = layer  # 0 = near (fast), 2 = far (slow)
        self.base_x = x

    def update(self, dt, speed_factor):
        # drift downward slightly and loop
        self.pos.y += (20 + self.layer * 40) * dt * speed_factor
        if self.pos.y > HEIGHT + 10:
            self.pos.y = -10
            self.pos.x = random.uniform(0, WIDTH)

    def draw(self, surf):
        if self.layer == 0:
            # bright rough star
            pygame.draw.circle(surf, PALETTE["star2"], (int(self.pos.x), int(self.pos.y)), max(1, self.size))
        else:
            pygame.draw.circle(surf, PALETTE["star1"], (int(self.pos.x), int(self.pos.y)), max(1, self.size))


def create_starfield(count=120):
    stars = []
    for _ in range(count):
        x = random.uniform(0, WIDTH)
        y = random.uniform(0, HEIGHT)
        layer = random.choices([0, 1, 2], weights=[0.2, 0.4, 0.4])[0]
        size = random.randint(1, 3) if layer > 0 else random.randint(2, 4)
        stars.append(Star(x, y, size, layer))
    return stars


# ---------- Game Manager ----------
def spawn_enemy(group):
    x = random.uniform(40, WIDTH - 40)
    y = random.uniform(-110, -30)
    speed = random.uniform(ENEMY_SPEED_MIN, ENEMY_SPEED_MAX)
    e = Enemy((x, y), speed)
    group.add(e)
    return e


def spawn_explosion(pos, particle_group):
    for _ in range(PARTICLE_COUNT):
        p = Particle(pos)
        particle_group.add(p)


def draw_hud(surf, player):
    # score and lives
    score_surf = font.render(f"Score: {player.score}", True, PALETTE["ui"])
    lives_surf = font.render(f"Lives: {player.lives}", True, PALETTE["ui"])
    surf.blit(score_surf, (12, 12))
    surf.blit(lives_surf, (WIDTH - lives_surf.get_width() - 12, 12))
    # hint
    hint = font.render("Move: Arrows / WASD    Shoot: Space", True, PALETTE["ui"])
    surf.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 30))


def main():
    # sprite groups
    player_group = pygame.sprite.GroupSingle()
    bullet_group = pygame.sprite.Group()
    enemy_group = pygame.sprite.Group()
    particle_group = pygame.sprite.Group()

    player = Player((WIDTH // 2, HEIGHT - 100))
    player_group.add(player)

    stars = create_starfield(140)
    last_spawn = 0.0
    spawn_timer = 0.0
    running = True
    paused = False
    speed_factor = 1.0  # used to accelerate starfield when player moves

    # subtle background gradient surface
    bg_surf = pygame.Surface((WIDTH, HEIGHT))
    for y in range(HEIGHT):
        # interpolation between two bg colors
        t = y / HEIGHT
        r = int(PALETTE["bg_dark"][0] * (1 - t) + PALETTE["bg_soft"][0] * t)
        g = int(PALETTE["bg_dark"][1] * (1 - t) + PALETTE["bg_soft"][1] * t)
        b = int(PALETTE["bg_dark"][2] * (1 - t) + PALETTE["bg_soft"][2] * t)
        pygame.draw.line(bg_surf, (r, g, b), (0, y), (WIDTH, y))

    # main loop
    while running:
        dt = clock.tick(FPS) / 1000.0  # seconds passed since last frame
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_p:
                    paused = not paused

        keys = pygame.key.get_pressed()

        if not paused:
            # update starfield speed factor from player horizontal input
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                speed_factor = 0.75
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                speed_factor = 1.25
            else:
                # gently return to neutral
                speed_factor += (1.0 - speed_factor) * min(1.0, dt * 3.0)

            # spawn enemies periodically (increase difficulty slowly with score)
            spawn_timer += dt
            spawn_interval = max(0.35, ENEMY_SPAWN_INTERVAL - min(player.score / 50.0, 0.7))
            if spawn_timer >= spawn_interval:
                spawn_timer = 0.0
                spawn_enemy(enemy_group)

            # player update
            player.update(dt, keys)

            # shooting
            if (keys[pygame.K_SPACE] or keys[pygame.K_z]) and player.can_shoot():
                # create two bullets for a little spread
                b1 = Bullet(player.rect.midtop - Vector2(10, 0))
                b2 = Bullet(player.rect.midtop + Vector2(10, 0))
                bullet_group.add(b1, b2)
                player.shoot()

            # update bullets, enemies, particles
            bullet_group.update(dt)
            enemy_group.update(dt)
            particle_group.update(dt)

            # update stars
            for s in stars:
                s.update(dt, speed_factor)

            # collisions: bullets -> enemies
            hits = pygame.sprite.groupcollide(enemy_group, bullet_group, True, True)
            for enemy in hits:
                player.score += 10
                # explosion particles
                spawn_explosion(enemy.rect.center, particle_group)

            # collisions: enemies -> player
            if pygame.sprite.spritecollide(player, enemy_group, True, pygame.sprite.collide_mask if False else pygame.sprite.collide_rect):
                player.lives -= 1
                spawn_explosion(player.rect.center, particle_group)
                if player.lives <= 0:
                    # Game over: reset score and lives, clear enemies but keep running
                    # a bit of a soft reset with a small flash
                    spawn_explosion(player.rect.center, particle_group)
                    player.lives = 3
                    player.score = 0
                    for e in enemy_group:
                        spawn_explosion(e.rect.center, particle_group)
                    enemy_group.empty()
                    bullet_group.empty()

        # --- Drawing ---
        screen.blit(bg_surf, (0, 0))

        # draw stars in layers for depth (far to near)
        for layer in (2, 1, 0):
            for s in [x for x in stars if x.layer == layer]:
                s.draw(screen)

        # small additive glow behind player
        glow = pygame.Surface((player.rect.width * 2, player.rect.height * 2), pygame.SRCALPHA)
        gx, gy = glow.get_size()
        pygame.draw.ellipse(glow, (PALETTE["player"][0], PALETTE["player"][1], PALETTE["player"][2], 40), (0, 0, gx, gy))
        screen.blit(glow, (player.rect.centerx - gx // 2, player.rect.centery - gy // 2 + 10), special_flags=pygame.BLEND_ADD)

        # draw sprites
        for sprite in enemy_group:
            screen.blit(sprite.image, sprite.rect)
        for sprite in bullet_group:
            screen.blit(sprite.image, sprite.rect)
        for sprite in particle_group:
            screen.blit(sprite.image, sprite.rect)
        for sprite in player_group:
            screen.blit(sprite.image, sprite.rect)

        # HUD
        draw_hud(screen, player)

        # pause overlay
        if paused:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((8, 12, 22, 180))
            screen.blit(overlay, (0, 0))
            text = font.render("PAUSED - Press P to resume", True, PALETTE["ui"])
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
