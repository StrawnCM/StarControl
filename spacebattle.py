import pygame
import math
import random

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Simple Space Battle")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# Ship properties
SHIP_SIZE = 30
SHIP_COLOR = GREEN
SHIP_SPEED = 3
SHIP_ROTATION_SPEED = 5
SHIP_MAX_SPEED = 5
SHIP_INITIAL_SHIELDS = 100

# Weapon properties
MACHINE_GUN_DAMAGE = 5
MACHINE_GUN_COOLDOWN = 5  # Frames between shots
MISSILE_DAMAGE = 25
MISSILE_SPEED = 7
MISSILE_COOLDOWN = 60  # Frames between shots

# Star properties
NUM_STARS = 50
STAR_SIZE = 2
STAR_COLOR = WHITE

# Strategy properties
NUM_SYSTEMS = 5
SYSTEM_RADIUS = 10
STRATEGY_SPEED = 2

# Game states
GAME_STRATEGY = 0
GAME_BATTLE = 1
GAME_OVER = 2


# --- Classes ---

class Ship(pygame.sprite.Sprite):
    def __init__(self, x, y, color):
        super().__init__()
        self.x = x
        self.y = y
        self.angle = 0
        self.vx = 0
        self.vy = 0
        self.color = color
        self.shields = SHIP_INITIAL_SHIELDS
        self.last_machine_gun_shot = 0
        self.last_missile_shot = 0
        if self.color == GREEN:
            self.image = pygame.image.load("/Users/jacobstrawn/Documents/Space Battle Game/ship1.png").convert_alpha()
        else:
            self.image = pygame.image.load("/Users/jacobstrawn/Documents/Space Battle Game/ship2.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (SHIP_SIZE, SHIP_SIZE))
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.original_image = self.image.copy()

    def update(self):
        self.x += self.vx
        self.y += self.vy

        # Keep ship within bounds (simple wrapping)
        if self.x < 0:
            self.x = SCREEN_WIDTH
        elif self.x > SCREEN_WIDTH:
            self.x = 0
        if self.y < 0:
            self.y = SCREEN_HEIGHT
        elif self.y > SCREEN_HEIGHT:
            self.y = 0

        self.rect.center = (self.x, self.y)  # Update rect position

    def rotate(self, angle_change):
        self.angle += angle_change
        self.image = pygame.transform.rotate(self.original_image, -self.angle)  # Rotate the *original* image
        self.rect = self.image.get_rect(center=self.rect.center)  # Update the rect after rotation

    def accelerate(self, amount):
        self.vx += amount * math.cos(math.radians(self.angle))
        self.vy += amount * math.sin(math.radians(self.angle))
        speed = math.sqrt(self.vx**2 + self.vy**2)
        if speed > SHIP_MAX_SPEED:
            scale = SHIP_MAX_SPEED / speed
            self.vx *= scale
            self.vy *= scale

    def shoot_machine_gun(self):
        now = pygame.time.get_ticks()
        if now - self.last_machine_gun_shot > MACHINE_GUN_COOLDOWN * (1000 / 60):  # Convert frames to milliseconds
            self.last_machine_gun_shot = now
            return MachineGunBullet(self.x, self.y, self.angle, self.color)
        return None

    def shoot_missile(self):
        now = pygame.time.get_ticks()
        if now - self.last_missile_shot > MISSILE_COOLDOWN * (1000 / 60):
            self.last_missile_shot = now
            return Missile(self.x, self.y, self.angle, self.color)
        return None

    def take_damage(self, damage):
        self.shields -= damage
        if self.shields < 0:
            self.shields = 0


class Bullet(pygame.sprite.Sprite):  # Abstract Base Class for bullets
    def __init__(self, x, y, angle, speed, damage, color):
        super().__init__()
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.damage = damage
        self.color = color
        self.image = pygame.Surface((4, 4))  # Small square
        self.image.fill(self.color)
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def update(self):
        self.x += self.speed * math.cos(math.radians(self.angle))
        self.y += self.speed * math.sin(math.radians(self.angle))
        self.rect.center = (self.x, self.y)

        # Remove if out of bounds
        if self.x < 0 or self.x > SCREEN_WIDTH or self.y < 0 or self.y > SCREEN_HEIGHT:
            self.kill()


class MachineGunBullet(Bullet):
    def __init__(self, x, y, angle, color):
        super().__init__(x, y, angle, 10, MACHINE_GUN_DAMAGE, color)


class Missile(Bullet):
    def __init__(self, x, y, angle, color):
        super().__init__(x, y, angle, MISSILE_SPEED, MISSILE_DAMAGE, color)
        self.image = pygame.Surface((8, 8))  # Make it bigger so that it is easier to see it's a missile
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect(center=(self.x, self.y))


# --- Game Setup ---

# Starfield (background)
stars = []
for _ in range(NUM_STARS):
    x = random.randint(0, SCREEN_WIDTH)
    y = random.randint(0, SCREEN_HEIGHT)
    stars.append((x, y))

# Placeholders for battle entities
player = None
computer = None
player_group = pygame.sprite.Group()
computer_group = pygame.sprite.Group()
player_bullets = pygame.sprite.Group()
computer_bullets = pygame.sprite.Group()


def start_strategy():
    """Initialize the strategic starfield mode."""
    global game_state, systems, strategy_player_pos
    systems = []
    for i in range(NUM_SYSTEMS):
        x = random.randint(50, SCREEN_WIDTH - 50)
        y = random.randint(50, SCREEN_HEIGHT - 50)
        has_enemy = i == 0  # ensure at least one enemy system
        systems.append({"x": x, "y": y, "enemy": has_enemy})
    strategy_player_pos = [SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2]
    game_state = GAME_STRATEGY


def start_battle():
    """Setup a new battle between player and computer."""
    global player, computer, player_group, computer_group, player_bullets, computer_bullets, game_state
    player = Ship(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2, GREEN)
    computer = Ship(SCREEN_WIDTH * 3 // 4, SCREEN_HEIGHT // 2, RED)
    player_group = pygame.sprite.Group(player)
    computer_group = pygame.sprite.Group(computer)
    player_bullets = pygame.sprite.Group()
    computer_bullets = pygame.sprite.Group()
    game_state = GAME_BATTLE


# --- Game Logic Functions ---

def computer_ai(computer, player, player_bullets):  
    """Simple AI for the computer ship."""
    # Aim at the player (very basic)
    dx = player.x - computer.x
    dy = player.y - computer.y
    angle_to_player = math.degrees(math.atan2(dy, dx))
    angle_difference = (angle_to_player - computer.angle + 180) % 360 - 180  # Keep angle difference within -180 to 180

    # Rotate towards the player
    if angle_difference > 5:
        computer.rotate(SHIP_ROTATION_SPEED)
    elif angle_difference < -5:
        computer.rotate(-SHIP_ROTATION_SPEED)

    # Move towards the player
    if abs(angle_difference) < 15:  # Only move if roughly facing the player
        computer.accelerate(0.2)  # Small acceleration amount
    else:
        computer.accelerate(-0.1)  # Try to slow down if not facing player

    # Shoot (randomly choose between machine gun and missile, check for cooldown)
    if random.random() < 0.02:  # Small chance to shoot
        if random.random() < 0.5:  # 50% chance to shoot the machine gun
            bullet = computer.shoot_machine_gun()
            if bullet:
                computer_bullets.add(bullet)
        else:  # Other 50% chance to shoot the missile
            missile = computer.shoot_missile()
            if missile:
                computer_bullets.add(missile)


# --- Game Loop ---

running = True
clock = pygame.time.Clock()
start_strategy()

while running:
    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_n and game_state == GAME_OVER:
                start_strategy()

    # --- Game Logic ---
    if game_state == GAME_STRATEGY:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            strategy_player_pos[1] -= STRATEGY_SPEED
        if keys[pygame.K_DOWN]:
            strategy_player_pos[1] += STRATEGY_SPEED
        if keys[pygame.K_LEFT]:
            strategy_player_pos[0] -= STRATEGY_SPEED
        if keys[pygame.K_RIGHT]:
            strategy_player_pos[0] += STRATEGY_SPEED
        strategy_player_pos[0] = max(0, min(SCREEN_WIDTH, strategy_player_pos[0]))
        strategy_player_pos[1] = max(0, min(SCREEN_HEIGHT, strategy_player_pos[1]))
        if keys[pygame.K_SPACE]:
            for system in systems:
                if system["enemy"]:
                    dx = strategy_player_pos[0] - system["x"]
                    dy = strategy_player_pos[1] - system["y"]
                    if math.hypot(dx, dy) < SYSTEM_RADIUS:
                        system["enemy"] = False
                        start_battle()
                        break
    elif game_state == GAME_BATTLE:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            player.accelerate(0.2)
        if keys[pygame.K_DOWN]:
            player.accelerate(-0.1)  # Decelerate
        if keys[pygame.K_LEFT]:
            player.rotate(-SHIP_ROTATION_SPEED)
        if keys[pygame.K_RIGHT]:
            player.rotate(SHIP_ROTATION_SPEED)
        if keys[pygame.K_SPACE]:  # Machine gun shot
            bullet = player.shoot_machine_gun()
            if bullet:
                player_bullets.add(bullet)
        if keys[pygame.K_LSHIFT]:  # Missile shot
            missile = player.shoot_missile()
            if missile:
                player_bullets.add(missile)

        # Update ships
        player_group.update()
        computer_group.update()

        # Update bullets
        player_bullets.update()
        computer_bullets.update()

        # Computer AI
        computer_ai(computer, player, player_bullets)

        # --- Collision Detection ---

        # Player bullets hitting computer
        hits = pygame.sprite.groupcollide(computer_group, player_bullets, False, True)
        for computer_ship, bullets_hit in hits.items():
            for bullet in bullets_hit:
                computer_ship.take_damage(bullet.damage)

        # Computer bullets hitting player
        hits = pygame.sprite.groupcollide(player_group, computer_bullets, False, True)
        for player_ship, bullets_hit in hits.items():
            for bullet in bullets_hit:
                player_ship.take_damage(bullet.damage)

        # Check for game over (ship destroyed)
        if player.shields <= 0 or computer.shields <= 0:
            game_state = GAME_OVER

    # --- Drawing ---
    screen.fill(BLACK)

    # Draw stars
    for x, y in stars:
        pygame.draw.circle(screen, STAR_COLOR, (x, y), STAR_SIZE)

    if game_state == GAME_STRATEGY:
        for system in systems:
            color = RED if system["enemy"] else WHITE
            pygame.draw.circle(screen, color, (system["x"], system["y"]), SYSTEM_RADIUS)
        pygame.draw.circle(screen, GREEN, (int(strategy_player_pos[0]), int(strategy_player_pos[1])), SYSTEM_RADIUS // 2)
    else:
        player_group.draw(screen)
        computer_group.draw(screen)
        player_bullets.draw(screen)
        computer_bullets.draw(screen)

        font = pygame.font.Font(None, 24)
        player_shields_text = font.render(f"Player Shields: {player.shields}", True, GREEN)
        computer_shields_text = font.render(f"Computer Shields: {computer.shields}", True, RED)
        screen.blit(player_shields_text, (10, 10))
        screen.blit(computer_shields_text, (SCREEN_WIDTH - 200, 10))

        if game_state == GAME_OVER:
            font = pygame.font.Font(None, 48)
            if player.shields <= 0:
                text = font.render("Computer Wins!", True, RED)
            else:
                text = font.render("Player Wins!", True, GREEN)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(text, text_rect)

pygame.display.flip()  # Update the display
clock.tick(60)  # Limit frame rate to 60 FPS

pygame.quit()
