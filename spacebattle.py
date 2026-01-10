import pygame
import math
import random
import numpy as np

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

# Star properties - multi-layer parallax starfield
STAR_LAYERS = [
    {"count": 80, "size_range": (1, 1), "speed": 0.1, "colors": [(60, 60, 80), (50, 50, 70)]},  # Distant dim stars
    {"count": 50, "size_range": (1, 2), "speed": 0.3, "colors": [(100, 100, 120), (80, 80, 100)]},  # Mid-distance
    {"count": 30, "size_range": (1, 2), "speed": 0.5, "colors": [(150, 150, 180), (120, 140, 180), (180, 150, 120)]},  # Closer
    {"count": 15, "size_range": (2, 3), "speed": 0.8, "colors": [(255, 255, 255), (200, 220, 255), (255, 240, 200), (255, 200, 200)]},  # Close bright stars
]
# Nebula properties
NEBULA_COLORS = [
    (40, 20, 60, 30),   # Purple nebula
    (20, 40, 60, 25),   # Blue nebula
    (60, 30, 40, 20),   # Red/pink nebula
]

# Strategy properties
NUM_SYSTEMS = 7
SYSTEM_RADIUS = 12
STRATEGY_SPEED = 3
LANDING_RADIUS = 15

# Fuel system
FUEL_MAX_DEFAULT = 100.0
FUEL_TIME_DRAIN = 0.03      # Fuel lost per frame
FUEL_DISTANCE_DRAIN = 0.08  # Fuel lost per pixel moved

# Planet resources
PLANET_FUEL_MIN = 15
PLANET_FUEL_MAX = 40
PLANET_ARTIFACTS_MIN = 0
PLANET_ARTIFACTS_MAX = 2

# Upgrade costs (in artifacts)
UPGRADE_COSTS = {
    "rotation_speed": 2,
    "acceleration": 2,
    "fuel_capacity": 2,
    "machine_gun_damage": 3,
    "missile_damage": 3,
}

# Game states
GAME_STRATEGY = 0
GAME_BATTLE = 1
GAME_OVER = 2
GAME_SHIP_SELECT = 3
GAME_GALAXY_SELECT = 4
GAME_GALAXY_COMPLETE = 5

# Ship types configuration
SHIP_TYPES = {
    "interceptor": {
        "name": "Interceptor",
        "description": "Fast & agile, fires missiles",
        "max_speed": 7,
        "acceleration": 0.25,
        "rotation_speed": 7,
        "shields": 80,
        "color_player": (0, 255, 100),
        "color_enemy": (255, 100, 100),
        "special": "missile",
        "special_cooldown": 60,
    },
    "defender": {
        "name": "Defender",
        "description": "Balanced, temporary shield",
        "max_speed": 5,
        "acceleration": 0.20,
        "rotation_speed": 5,
        "shields": 100,
        "color_player": (100, 150, 255),
        "color_enemy": (255, 150, 50),
        "special": "shield",
        "special_duration": 120,
        "special_cooldown": 300,
    },
    "juggernaut": {
        "name": "Juggernaut",
        "description": "Heavy tank, deploys drone",
        "max_speed": 3.5,
        "acceleration": 0.12,
        "rotation_speed": 3,
        "shields": 150,
        "color_player": (255, 220, 50),
        "color_enemy": (200, 50, 200),
        "special": "drone",
        "special_cooldown": 480,
    },
}
SHIP_TYPE_ORDER = ["interceptor", "defender", "juggernaut"]

# Galaxy configuration
NUM_GALAXIES = 5
GALAXY_CONFIG = {
    1: {"name": "Orion Sector", "planets": 7, "enemies": 2, "fuel": 100, "drain_mult": 1.0, "enemy_hp_mult": 1.0,
        "color": (100, 150, 255), "core_color": (200, 220, 255)},
    2: {"name": "Cygnus Arm", "planets": 8, "enemies": 3, "fuel": 90, "drain_mult": 1.1, "enemy_hp_mult": 1.2,
        "color": (255, 200, 100), "core_color": (255, 240, 200)},
    3: {"name": "Sagittarius Reach", "planets": 9, "enemies": 4, "fuel": 80, "drain_mult": 1.2, "enemy_hp_mult": 1.4,
        "color": (200, 100, 255), "core_color": (240, 200, 255)},
    4: {"name": "Perseus Void", "planets": 10, "enemies": 5, "fuel": 70, "drain_mult": 1.3, "enemy_hp_mult": 1.6,
        "color": (100, 255, 150), "core_color": (200, 255, 220)},
    5: {"name": "Core Nebula", "planets": 12, "enemies": 6, "fuel": 60, "drain_mult": 1.5, "enemy_hp_mult": 2.0,
        "color": (255, 100, 100), "core_color": (255, 200, 150)},
}


def draw_galaxy_image(surface, cx, cy, radius, color, core_color, locked=False):
    """Draw a spiral galaxy visual."""
    # Draw spiral arms
    for arm in range(2):
        arm_offset = arm * math.pi
        for i in range(40):
            t = i / 40.0
            r = radius * t * 0.9
            angle = t * 4 * math.pi + arm_offset
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle) * 0.5  # Flatten for perspective
            size = max(1, int(3 - t * 2))
            if locked:
                c = (60, 60, 60)
            else:
                fade = 1 - t * 0.5
                c = tuple(int(v * fade) for v in color)
            pygame.draw.circle(surface, c, (int(x), int(y)), size)

    # Draw scattered stars in galaxy
    random.seed(radius)  # Consistent stars per galaxy
    for _ in range(30):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(0, radius * 0.8)
        x = cx + dist * math.cos(angle)
        y = cy + dist * math.sin(angle) * 0.5
        if locked:
            c = (50, 50, 50)
        else:
            brightness = random.uniform(0.3, 1.0)
            c = tuple(int(v * brightness) for v in color)
        pygame.draw.circle(surface, c, (int(x), int(y)), 1)

    # Draw bright core
    for r in range(int(radius * 0.25), 0, -2):
        alpha = int(255 * (1 - r / (radius * 0.25)))
        if locked:
            c = (40 + alpha // 4, 40 + alpha // 4, 40 + alpha // 4)
        else:
            c = tuple(min(255, int(core_color[i] * (0.5 + alpha / 510))) for i in range(3))
        pygame.draw.circle(surface, c, (cx, cy), r)


# --- Classes ---

class SoundManager:
    """Manages all game sounds using programmatically generated tones."""

    def __init__(self):
        pygame.mixer.init(frequency=44100, size=-16, channels=2)
        pygame.mixer.set_num_channels(16)
        self.sounds = {}
        self.enabled = True
        self._generate_all_sounds()

    def _generate_tone(self, frequency, duration, wave_type="sine", fade_out=0.1, volume=0.5):
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, n_samples, False)
        if wave_type == "sine":
            wave = np.sin(2 * np.pi * frequency * t)
        elif wave_type == "square":
            wave = np.sign(np.sin(2 * np.pi * frequency * t))
        elif wave_type == "sawtooth":
            wave = 2 * (t * frequency % 1) - 1
        elif wave_type == "noise":
            wave = np.random.uniform(-1, 1, n_samples)
        else:
            wave = np.sin(2 * np.pi * frequency * t)
        fade_samples = int(sample_rate * fade_out)
        if fade_samples > 0 and fade_samples < n_samples:
            fade = np.linspace(1, 0, fade_samples)
            wave[-fade_samples:] *= fade
        samples = (wave * volume * 32767).astype(np.int16)
        stereo = np.column_stack((samples, samples))
        return pygame.sndarray.make_sound(stereo)

    def _generate_sweep(self, freq_start, freq_end, duration, volume):
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, n_samples, False)
        freq = np.linspace(freq_start, freq_end, n_samples)
        phase = np.cumsum(2 * np.pi * freq / sample_rate)
        wave = np.sin(phase) * volume
        fade = int(n_samples * 0.3)
        if fade > 0:
            wave[-fade:] *= np.linspace(1, 0, fade)
        samples = (wave * 32767).astype(np.int16)
        stereo = np.column_stack((samples, samples))
        return pygame.sndarray.make_sound(stereo)

    def _generate_explosion(self, duration):
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        noise = np.random.uniform(-1, 1, n_samples)
        envelope = np.exp(-np.linspace(0, 5, n_samples))
        wave = noise * envelope * 0.7
        samples = (wave * 32767).astype(np.int16)
        stereo = np.column_stack((samples, samples))
        return pygame.sndarray.make_sound(stereo)

    def _generate_chime(self, frequencies, duration):
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, n_samples, False)
        wave = np.zeros(n_samples)
        for i, freq in enumerate(frequencies):
            delay = i * 0.05
            delay_samples = int(delay * sample_rate)
            if delay_samples < n_samples:
                sub_t = t[delay_samples:] - delay
                sub_wave = np.sin(2 * np.pi * freq * sub_t)
                sub_wave *= np.exp(-sub_t * 3)
                wave[delay_samples:] += sub_wave * 0.3
        samples = (wave * 32767).astype(np.int16)
        stereo = np.column_stack((samples, samples))
        return pygame.sndarray.make_sound(stereo)

    def _generate_ambient_music(self, duration):
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, n_samples, False)
        wave = np.sin(2 * np.pi * 55 * t) * 0.15
        wave += np.sin(2 * np.pi * 82.5 * t) * 0.1
        mod = np.sin(2 * np.pi * 0.1 * t) * 0.5 + 0.5
        wave *= mod
        wave += np.sin(2 * np.pi * 220 * t) * 0.03 * mod
        samples = (wave * 32767).astype(np.int16)
        stereo = np.column_stack((samples, samples))
        return pygame.sndarray.make_sound(stereo)

    def _generate_all_sounds(self):
        self.sounds["thrust"] = self._generate_tone(80, 0.2, "sawtooth", 0, 0.3)
        self.sounds["machinegun"] = self._generate_tone(800, 0.05, "square", 0.02, 0.4)
        self.sounds["missile"] = self._generate_sweep(200, 600, 0.3, 0.5)
        self.sounds["explosion"] = self._generate_explosion(0.5)
        self.sounds["collision"] = self._generate_tone(120, 0.15, "sine", 0.1, 0.6)
        self.sounds["landing"] = self._generate_chime([400, 500, 600], 0.3)
        self.sounds["collect"] = self._generate_chime([300, 400, 500, 600], 0.4)
        self.sounds["upgrade"] = self._generate_chime([262, 330, 392, 523], 0.6)
        self.sounds["shield"] = self._generate_sweep(300, 800, 0.2, 0.4)
        self.sounds["drone"] = self._generate_sweep(500, 200, 0.3, 0.4)
        self.sounds["music"] = self._generate_ambient_music(8.0)
        self.sounds["select"] = self._generate_tone(440, 0.1, "sine", 0.05, 0.3)
        self.sounds["victory"] = self._generate_chime([523, 659, 784, 1047], 0.8)

    def play(self, sound_name, loops=0):
        if self.enabled and sound_name in self.sounds:
            self.sounds[sound_name].play(loops=loops)

    def stop(self, sound_name):
        if sound_name in self.sounds:
            self.sounds[sound_name].stop()

    def play_music(self):
        if self.enabled:
            self.sounds["music"].play(loops=-1)

    def stop_music(self):
        self.sounds["music"].stop()

    def toggle(self):
        self.enabled = not self.enabled
        if not self.enabled:
            pygame.mixer.stop()


class ScoutDrone(pygame.sprite.Sprite):
    """Small drone that chases and damages enemy ships."""

    def __init__(self, x, y, owner_is_player):
        super().__init__()
        self.x = x
        self.y = y
        self.owner_is_player = owner_is_player
        self.speed = 4
        self.damage = 3
        self.lifespan = 300  # 5 seconds at 60fps
        self.color = GREEN if owner_is_player else RED
        self.image = pygame.Surface((12, 12), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color, (6, 6), 5)
        pygame.draw.circle(self.image, WHITE, (6, 6), 5, 1)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self, target):
        if target is None:
            self.lifespan = 0
            return
        dx = target.x - self.x
        dy = target.y - self.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed
        self.rect.center = (int(self.x), int(self.y))
        self.lifespan -= 1
        if self.lifespan <= 0:
            self.kill()

    def check_hit(self, target):
        dx = target.x - self.x
        dy = target.y - self.y
        return math.hypot(dx, dy) < SHIP_SIZE // 2 + 6


class BattlePlanet:
    """Planet in battle arena with gravity well."""

    def __init__(self, x, y, radius=35, mass=800):
        self.x = x
        self.y = y
        self.radius = radius
        self.mass = mass
        self.gravity_range = radius * 5
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        for i in range(radius, 0, -1):
            shade = int(80 + (radius - i) * 2)
            color = (min(shade, 160), min(shade // 2, 80), min(shade // 3, 50))
            pygame.draw.circle(self.image, color, (radius, radius), i)
        self.rect = self.image.get_rect(center=(x, y))

    def apply_gravity(self, ship):
        dx = self.x - ship.x
        dy = self.y - ship.y
        dist = math.hypot(dx, dy)
        if dist < self.gravity_range and dist > 0:
            force = self.mass / max(dist ** 2, 100)
            force = min(force, 0.4)
            ship.vx += (dx / dist) * force
            ship.vy += (dy / dist) * force

    def check_collision(self, ship):
        dx = self.x - ship.x
        dy = self.y - ship.y
        dist = math.hypot(dx, dy)
        return dist < self.radius + SHIP_SIZE // 2

    def handle_collision(self, ship):
        dx = ship.x - self.x
        dy = ship.y - self.y
        dist = max(math.hypot(dx, dy), 1)
        ship.take_damage(40)
        ship.vx = (dx / dist) * 4
        ship.vy = (dy / dist) * 4
        ship.x = self.x + (dx / dist) * (self.radius + SHIP_SIZE)
        ship.y = self.y + (dy / dist) * (self.radius + SHIP_SIZE)

    def draw(self, surface):
        for i in range(3):
            r = int(self.gravity_range - i * (self.gravity_range // 3))
            pygame.draw.circle(surface, (40, 40, 60), (int(self.x), int(self.y)), r, 1)
        surface.blit(self.image, self.rect)


class Ship(pygame.sprite.Sprite):
    def __init__(self, x, y, ship_type, is_player=True, hp_mult=1.0):
        super().__init__()
        self.x = x
        self.y = y
        self.angle = 0
        self.vx = 0
        self.vy = 0
        self.ship_type = ship_type
        self.is_player = is_player

        # Get config from ship type
        config = SHIP_TYPES[ship_type]
        self.color = config["color_player"] if is_player else config["color_enemy"]
        self.max_speed = config["max_speed"]
        self.base_acceleration = config["acceleration"]
        self.rotation_speed = config["rotation_speed"]
        self.max_shields = int(config["shields"] * hp_mult)
        self.shields = self.max_shields

        # Special ability
        self.special_type = config["special"]
        self.special_cooldown_max = config["special_cooldown"]
        self.special_cooldown = 0
        self.special_duration = config.get("special_duration", 0)
        self.special_active_timer = 0
        self.shield_active = False
        self.active_drone = None

        self.last_machine_gun_shot = 0
        self.last_missile_shot = 0

        # Upgrade bonuses (applied by start_battle for player)
        self.acceleration_bonus = 0
        self.rotation_bonus = 0
        self.mg_damage = MACHINE_GUN_DAMAGE
        self.missile_damage = MISSILE_DAMAGE

        # Create ship visual
        self._create_ship_image()

    def _create_ship_image(self):
        self.image = pygame.Surface((SHIP_SIZE, SHIP_SIZE), pygame.SRCALPHA)
        points = [
            (SHIP_SIZE, SHIP_SIZE // 2),
            (0, 0),
            (0, SHIP_SIZE),
        ]
        pygame.draw.polygon(self.image, self.color, points)
        outline = (max(0, self.color[0]-50), max(0, self.color[1]-50), max(0, self.color[2]-50))
        pygame.draw.polygon(self.image, outline, points, 2)
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.original_image = self.image.copy()

    def update(self):
        self.x += self.vx
        self.y += self.vy

        if self.x < 0:
            self.x = SCREEN_WIDTH
        elif self.x > SCREEN_WIDTH:
            self.x = 0
        if self.y < 0:
            self.y = SCREEN_HEIGHT
        elif self.y > SCREEN_HEIGHT:
            self.y = 0

        self.rect.center = (self.x, self.y)

        # Update special ability timers
        if self.special_cooldown > 0:
            self.special_cooldown -= 1
        if self.special_active_timer > 0:
            self.special_active_timer -= 1
            if self.special_active_timer <= 0:
                self.shield_active = False

    def rotate(self, angle_change):
        self.angle += angle_change
        self.image = pygame.transform.rotate(self.original_image, -self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)

    def accelerate(self, amount):
        self.vx += amount * math.cos(math.radians(self.angle))
        self.vy += amount * math.sin(math.radians(self.angle))
        speed = math.sqrt(self.vx**2 + self.vy**2)
        if speed > self.max_speed:
            scale = self.max_speed / speed
            self.vx *= scale
            self.vy *= scale

    def get_effective_rotation(self):
        return self.rotation_speed + self.rotation_bonus

    def get_effective_acceleration(self):
        return self.base_acceleration + self.acceleration_bonus

    def shoot_machine_gun(self):
        now = pygame.time.get_ticks()
        if now - self.last_machine_gun_shot > MACHINE_GUN_COOLDOWN * (1000 / 60):
            self.last_machine_gun_shot = now
            return MachineGunBullet(self.x, self.y, self.angle, self.color, self.mg_damage)
        return None

    def shoot_missile(self):
        now = pygame.time.get_ticks()
        if now - self.last_missile_shot > MISSILE_COOLDOWN * (1000 / 60):
            self.last_missile_shot = now
            return Missile(self.x, self.y, self.angle, self.color, self.missile_damage)
        return None

    def use_special(self):
        """Use ship's special ability. Returns result or None."""
        if self.special_cooldown > 0:
            return None
        self.special_cooldown = self.special_cooldown_max

        if self.special_type == "missile":
            return self.shoot_missile()
        elif self.special_type == "shield":
            self.shield_active = True
            self.special_active_timer = self.special_duration
            return "shield"
        elif self.special_type == "drone":
            drone = ScoutDrone(self.x, self.y, self.is_player)
            self.active_drone = drone
            return drone
        return None

    def take_damage(self, damage):
        if self.shield_active:
            return  # Invincible while shield active
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
    def __init__(self, x, y, angle, color, damage=MACHINE_GUN_DAMAGE):
        super().__init__(x, y, angle, 10, damage, color)


class Missile(Bullet):
    def __init__(self, x, y, angle, color, damage=MISSILE_DAMAGE):
        super().__init__(x, y, angle, MISSILE_SPEED, damage, color)
        self.image = pygame.Surface((8, 8))  # Make it bigger so that it is easier to see it's a missile
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect(center=(self.x, self.y))


# --- Game Setup ---

# Multi-layer parallax starfield
star_layers = []
for layer in STAR_LAYERS:
    stars = []
    for _ in range(layer["count"]):
        x = random.uniform(0, SCREEN_WIDTH)
        y = random.uniform(0, SCREEN_HEIGHT)
        size = random.randint(layer["size_range"][0], layer["size_range"][1])
        color = random.choice(layer["colors"])
        # Add twinkle phase for bright stars
        twinkle = random.uniform(0, 2 * math.pi) if size >= 2 else None
        stars.append({"x": x, "y": y, "size": size, "color": color, "speed": layer["speed"], "twinkle": twinkle})
    star_layers.append(stars)

# Generate nebula clouds (pre-rendered for performance)
nebula_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
for _ in range(8):
    color = random.choice(NEBULA_COLORS)
    cx = random.randint(0, SCREEN_WIDTH)
    cy = random.randint(0, SCREEN_HEIGHT)
    for r in range(150, 20, -10):
        alpha = max(5, color[3] - (150 - r) // 5)
        c = (color[0], color[1], color[2], alpha)
        pygame.draw.circle(nebula_surface, c, (cx, cy), r)

# Initialize sound manager
sound_manager = SoundManager()

# Placeholders for battle entities
player = None
computer = None
player_group = pygame.sprite.Group()
computer_group = pygame.sprite.Group()
player_bullets = pygame.sprite.Group()
computer_bullets = pygame.sprite.Group()
player_drones = pygame.sprite.Group()
computer_drones = pygame.sprite.Group()
battle_planet = None

# Player persistent state
player_state = {
    "fuel": FUEL_MAX_DEFAULT,
    "artifacts": 0,
    "upgrades": {
        "rotation_speed": 0,
        "acceleration": 0,
        "fuel_capacity": 0,
        "machine_gun_damage": 0,
        "missile_damage": 0,
    },
}

# Galaxy progress
galaxy_progress = {
    "current_galaxy": 1,
    "completed": set(),
    "player_ship_type": "interceptor",
}

# Planet/system data
planets = []
current_planet_index = -1
game_over_reason = ""
thrust_sound_playing = False


# --- Helper Functions ---

def get_fuel_capacity():
    """Get current max fuel capacity including upgrades."""
    return FUEL_MAX_DEFAULT + player_state["upgrades"]["fuel_capacity"] * 25

def get_rotation_speed():
    """Get effective rotation speed with upgrades."""
    return SHIP_ROTATION_SPEED + player_state["upgrades"]["rotation_speed"] * 1

def get_acceleration_bonus():
    """Get acceleration bonus from upgrades."""
    return player_state["upgrades"]["acceleration"] * 0.05

def get_machine_gun_damage():
    """Get effective machine gun damage with upgrades."""
    return MACHINE_GUN_DAMAGE + player_state["upgrades"]["machine_gun_damage"] * 2

def get_missile_damage():
    """Get effective missile damage with upgrades."""
    return MISSILE_DAMAGE + player_state["upgrades"]["missile_damage"] * 5

def apply_upgrade(upgrade_type):
    """Apply an upgrade if player has enough artifacts."""
    global player_state
    cost = UPGRADE_COSTS.get(upgrade_type, 999)
    if player_state["artifacts"] >= cost:
        player_state["artifacts"] -= cost
        player_state["upgrades"][upgrade_type] += 1
        return True
    return False

def generate_planet(has_enemy=False):
    """Generate a planet with resources."""
    return {
        "x": random.randint(60, SCREEN_WIDTH - 60),
        "y": random.randint(60, SCREEN_HEIGHT - 60),
        "fuel": random.randint(PLANET_FUEL_MIN, PLANET_FUEL_MAX),
        "artifacts": random.randint(PLANET_ARTIFACTS_MIN, PLANET_ARTIFACTS_MAX),
        "has_enemy": has_enemy,
        "visited": False,
    }

def consume_fuel(distance_moved):
    """Consume fuel based on time and distance. Returns True if still alive."""
    global player_state
    drain_mult = player_state.get("fuel_drain_mult", 1.0)
    player_state["fuel"] -= FUEL_TIME_DRAIN * drain_mult
    player_state["fuel"] -= distance_moved * FUEL_DISTANCE_DRAIN * drain_mult
    if player_state["fuel"] < 0:
        player_state["fuel"] = 0
    return player_state["fuel"] > 0

def collect_resources(planet):
    """Collect fuel and artifacts from a planet."""
    global player_state
    # Collect fuel up to capacity
    fuel_capacity = get_fuel_capacity()
    refuel_amount = min(planet["fuel"], fuel_capacity - player_state["fuel"])
    player_state["fuel"] += refuel_amount
    planet["fuel"] -= refuel_amount
    # Collect artifacts
    player_state["artifacts"] += planet["artifacts"]
    planet["artifacts"] = 0


def start_strategy(galaxy_num=None):
    """Initialize the strategic starfield mode for a galaxy."""
    global game_state, planets, strategy_player_pos, player_state, game_over_reason

    if galaxy_num is None:
        galaxy_num = galaxy_progress["current_galaxy"]

    config = GALAXY_CONFIG[galaxy_num]

    # Generate planets with resources based on galaxy config
    planets = []
    enemy_count = 0
    for i in range(config["planets"]):
        has_enemy = enemy_count < config["enemies"]
        if has_enemy:
            enemy_count += 1
        planet = generate_planet(has_enemy)
        # First safe planet gets bonus resources
        if not has_enemy and len([p for p in planets if not p["has_enemy"]]) == 0:
            planet["fuel"] = PLANET_FUEL_MAX
            planet["artifacts"] = PLANET_ARTIFACTS_MAX
        planets.append(planet)

    random.shuffle(planets)  # Randomize positions
    strategy_player_pos = [SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2]

    # Reset player state for new galaxy
    player_state["fuel"] = config["fuel"]
    player_state["fuel_drain_mult"] = config["drain_mult"]
    player_state["artifacts"] = 0
    player_state["upgrades"] = {
        "rotation_speed": 0,
        "acceleration": 0,
        "fuel_capacity": 0,
        "machine_gun_damage": 0,
        "missile_damage": 0,
    }
    game_over_reason = ""
    game_state = GAME_STRATEGY


def start_battle():
    """Setup a new battle between player and computer."""
    global player, computer, player_group, computer_group, player_bullets, computer_bullets
    global player_drones, computer_drones, battle_planet, game_state

    # Get enemy HP multiplier from current galaxy
    config = GALAXY_CONFIG[galaxy_progress["current_galaxy"]]
    enemy_hp_mult = config["enemy_hp_mult"]

    # Create player ship with selected type
    player_ship_type = galaxy_progress["player_ship_type"]
    player = Ship(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2, player_ship_type, is_player=True)

    # Create enemy with random ship type
    enemy_ship_type = random.choice(SHIP_TYPE_ORDER)
    computer = Ship(SCREEN_WIDTH * 3 // 4, SCREEN_HEIGHT // 2, enemy_ship_type, is_player=False, hp_mult=enemy_hp_mult)

    # Apply player upgrades
    player.rotation_bonus = player_state["upgrades"]["rotation_speed"]
    player.acceleration_bonus = player_state["upgrades"]["acceleration"] * 0.03
    player.mg_damage = MACHINE_GUN_DAMAGE + player_state["upgrades"]["machine_gun_damage"] * 2
    player.missile_damage = MISSILE_DAMAGE + player_state["upgrades"]["missile_damage"] * 5

    player_group = pygame.sprite.Group(player)
    computer_group = pygame.sprite.Group(computer)
    player_bullets = pygame.sprite.Group()
    computer_bullets = pygame.sprite.Group()
    player_drones = pygame.sprite.Group()
    computer_drones = pygame.sprite.Group()

    # Create battle planet with gravity
    battle_planet = BattlePlanet(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

    game_state = GAME_BATTLE


def end_battle(player_won):
    """Handle end of battle and return to strategy mode or game over."""
    global game_state, game_over_reason, planets, current_planet_index

    if player_won:
        sound_manager.play("victory")
        # Remove enemy from planet and mark as visited
        if current_planet_index >= 0 and current_planet_index < len(planets):
            planet = planets[current_planet_index]
            planet["has_enemy"] = False
            planet["visited"] = True
            # Collect resources from conquered planet
            collect_resources(planet)
            sound_manager.play("collect")

        # Check if galaxy is complete
        if check_galaxy_complete():
            game_state = GAME_GALAXY_COMPLETE
        else:
            game_state = GAME_STRATEGY
    else:
        sound_manager.play("explosion")
        game_state = GAME_OVER
        game_over_reason = "DESTROYED"


def check_galaxy_complete():
    """Check if current galaxy win conditions are met."""
    enemies_left = sum(1 for p in planets if p["has_enemy"])
    all_visited = all(p["visited"] or p["has_enemy"] for p in planets)
    return enemies_left == 0 and all_visited


def complete_galaxy():
    """Handle galaxy completion and unlock next."""
    global game_state
    galaxy_num = galaxy_progress["current_galaxy"]
    galaxy_progress["completed"].add(galaxy_num)

    if galaxy_num >= NUM_GALAXIES:
        game_state = GAME_OVER
        game_over_reason = "VICTORY"
    else:
        game_state = GAME_GALAXY_SELECT


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

    # Move towards the player (only thrust when roughly facing them - no brakes!)
    if abs(angle_difference) < 30:
        computer.accelerate(0.15)

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
frame_count = 0
game_state = GAME_SHIP_SELECT  # Start at ship selection
sound_manager.play_music()

while running:
    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            # Sound toggle
            if event.key == pygame.K_m:
                sound_manager.toggle()

            # Ship selection
            if game_state == GAME_SHIP_SELECT:
                if event.key == pygame.K_1:
                    galaxy_progress["player_ship_type"] = "interceptor"
                    sound_manager.play("select")
                    game_state = GAME_GALAXY_SELECT
                elif event.key == pygame.K_2:
                    galaxy_progress["player_ship_type"] = "defender"
                    sound_manager.play("select")
                    game_state = GAME_GALAXY_SELECT
                elif event.key == pygame.K_3:
                    galaxy_progress["player_ship_type"] = "juggernaut"
                    sound_manager.play("select")
                    game_state = GAME_GALAXY_SELECT

            # Galaxy selection
            elif game_state == GAME_GALAXY_SELECT:
                for i in range(1, NUM_GALAXIES + 1):
                    if event.key == getattr(pygame, f"K_{i}"):
                        # Check if unlocked
                        if i == 1 or (i - 1) in galaxy_progress["completed"]:
                            galaxy_progress["current_galaxy"] = i
                            sound_manager.play("select")
                            start_strategy(i)

            # Galaxy complete - continue to next
            elif game_state == GAME_GALAXY_COMPLETE:
                if event.key == pygame.K_SPACE:
                    complete_galaxy()

            # Game over
            elif game_state == GAME_OVER:
                if event.key == pygame.K_n:
                    galaxy_progress["completed"] = set()
                    galaxy_progress["current_galaxy"] = 1
                    game_state = GAME_SHIP_SELECT

            # Upgrade purchases in strategy mode
            elif game_state == GAME_STRATEGY:
                if event.key == pygame.K_1:
                    if apply_upgrade("rotation_speed"):
                        sound_manager.play("upgrade")
                elif event.key == pygame.K_2:
                    if apply_upgrade("acceleration"):
                        sound_manager.play("upgrade")
                elif event.key == pygame.K_3:
                    if apply_upgrade("fuel_capacity"):
                        sound_manager.play("upgrade")
                elif event.key == pygame.K_4:
                    if apply_upgrade("machine_gun_damage"):
                        sound_manager.play("upgrade")
                elif event.key == pygame.K_5:
                    if apply_upgrade("missile_damage"):
                        sound_manager.play("upgrade")

    # --- Game Logic ---
    if game_state == GAME_STRATEGY:
        # Check for out of fuel
        if player_state["fuel"] <= 0:
            game_state = GAME_OVER
            game_over_reason = "OUT_OF_FUEL"
        else:
            old_pos = strategy_player_pos.copy()

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

            # Calculate distance moved and consume fuel
            dx = strategy_player_pos[0] - old_pos[0]
            dy = strategy_player_pos[1] - old_pos[1]
            distance = math.hypot(dx, dy)
            consume_fuel(distance)

            # Planet landing with SPACE key
            if keys[pygame.K_SPACE]:
                for i, planet in enumerate(planets):
                    px = strategy_player_pos[0] - planet["x"]
                    py = strategy_player_pos[1] - planet["y"]
                    if math.hypot(px, py) < LANDING_RADIUS:
                        current_planet_index = i
                        if planet["has_enemy"]:
                            # Enemy present - trigger battle
                            start_battle()
                        else:
                            # Collect resources
                            if not planet["visited"]:
                                collect_resources(planet)
                                planet["visited"] = True
                            elif planet["fuel"] > 0:
                                # Can still refuel from visited planets
                                collect_resources(planet)
                        break
    elif game_state == GAME_BATTLE:
        keys = pygame.key.get_pressed()

        # Thrust with sound
        if keys[pygame.K_UP]:
            player.accelerate(player.get_effective_acceleration())
            if not thrust_sound_playing:
                sound_manager.play("thrust", loops=-1)
                thrust_sound_playing = True
        else:
            if thrust_sound_playing:
                sound_manager.stop("thrust")
                thrust_sound_playing = False

        if keys[pygame.K_LEFT]:
            player.rotate(-player.get_effective_rotation())
        if keys[pygame.K_RIGHT]:
            player.rotate(player.get_effective_rotation())

        # Machine gun
        if keys[pygame.K_SPACE]:
            bullet = player.shoot_machine_gun()
            if bullet:
                player_bullets.add(bullet)
                sound_manager.play("machinegun")

        # Special ability (SHIFT)
        if keys[pygame.K_LSHIFT]:
            result = player.use_special()
            if result:
                if result == "shield":
                    sound_manager.play("shield")
                elif isinstance(result, ScoutDrone):
                    player_drones.add(result)
                    sound_manager.play("drone")
                elif isinstance(result, Missile):
                    player_bullets.add(result)
                    sound_manager.play("missile")

        # Apply gravity from battle planet
        if battle_planet:
            battle_planet.apply_gravity(player)
            battle_planet.apply_gravity(computer)

            # Check planet collisions
            if battle_planet.check_collision(player):
                battle_planet.handle_collision(player)
                sound_manager.play("collision")
            if battle_planet.check_collision(computer):
                battle_planet.handle_collision(computer)

        # Update ships
        player_group.update()
        computer_group.update()

        # Update bullets
        player_bullets.update()
        computer_bullets.update()

        # Update drones
        for drone in player_drones:
            drone.update(computer)
            if drone.check_hit(computer):
                computer.take_damage(drone.damage)
        for drone in computer_drones:
            drone.update(player)
            if drone.check_hit(player):
                player.take_damage(drone.damage)

        # Computer AI
        computer_ai(computer, player, player_bullets)

        # Computer special ability (random chance)
        if random.random() < 0.005 and computer.special_cooldown == 0:
            result = computer.use_special()
            if result:
                if isinstance(result, ScoutDrone):
                    computer_drones.add(result)
                elif isinstance(result, Missile):
                    computer_bullets.add(result)

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

        # Ship-to-ship collision
        dx = player.x - computer.x
        dy = player.y - computer.y
        dist = math.hypot(dx, dy)
        min_dist = SHIP_SIZE  # Collision distance

        if dist < min_dist and dist > 0:
            # Collision! Both ships take damage
            collision_damage = 10
            player.take_damage(collision_damage)
            computer.take_damage(collision_damage)
            sound_manager.play("collision")

            # Calculate bounce - push ships apart
            # Normalize the direction vector
            nx = dx / dist
            ny = dy / dist

            # Move ships apart so they don't overlap
            overlap = min_dist - dist
            player.x += nx * (overlap / 2 + 1)
            player.y += ny * (overlap / 2 + 1)
            computer.x -= nx * (overlap / 2 + 1)
            computer.y -= ny * (overlap / 2 + 1)

            # Bounce velocities - swap and reflect
            # Calculate relative velocity
            rel_vx = player.vx - computer.vx
            rel_vy = player.vy - computer.vy

            # Calculate impulse along collision normal
            impulse = rel_vx * nx + rel_vy * ny

            # Apply bounce (coefficient of restitution = 0.8)
            bounce = 0.8
            player.vx -= impulse * nx * bounce
            player.vy -= impulse * ny * bounce
            computer.vx += impulse * nx * bounce
            computer.vy += impulse * ny * bounce

        # Check for battle outcome
        if player.shields <= 0:
            end_battle(player_won=False)
        elif computer.shields <= 0:
            end_battle(player_won=True)

    # --- Drawing ---
    frame_count += 1
    screen.fill(BLACK)

    # Draw nebula background
    screen.blit(nebula_surface, (0, 0))

    # Get player velocity for parallax (use 0 if in strategy mode or no player)
    if game_state == GAME_BATTLE and player:
        px_vel, py_vel = player.vx, player.vy
    else:
        px_vel, py_vel = 0, 0

    # Draw parallax starfield layers
    for layer_stars in star_layers:
        for star in layer_stars:
            # Move stars based on player velocity (parallax effect)
            star["x"] -= px_vel * star["speed"]
            star["y"] -= py_vel * star["speed"]
            # Wrap stars around screen
            if star["x"] < 0:
                star["x"] += SCREEN_WIDTH
            elif star["x"] > SCREEN_WIDTH:
                star["x"] -= SCREEN_WIDTH
            if star["y"] < 0:
                star["y"] += SCREEN_HEIGHT
            elif star["y"] > SCREEN_HEIGHT:
                star["y"] -= SCREEN_HEIGHT
            # Calculate twinkle brightness for bright stars
            size = star["size"]
            color = star["color"]
            if star["twinkle"] is not None:
                twinkle_factor = 0.7 + 0.3 * math.sin(frame_count * 0.1 + star["twinkle"])
                color = tuple(int(c * twinkle_factor) for c in color)
            pygame.draw.circle(screen, color, (int(star["x"]), int(star["y"])), size)

    if game_state == GAME_STRATEGY:
        # Draw planets with visual states
        for planet in planets:
            # Enemy indicator (red glow)
            if planet["has_enemy"]:
                pygame.draw.circle(screen, (100, 0, 0), (planet["x"], planet["y"]), SYSTEM_RADIUS + 4)
                color = RED
            elif planet["visited"]:
                color = (80, 80, 80)  # Dim gray for visited
            else:
                color = WHITE

            pygame.draw.circle(screen, color, (planet["x"], planet["y"]), SYSTEM_RADIUS)

            # Artifact indicator (yellow dot)
            if planet["artifacts"] > 0 and not planet["visited"]:
                pygame.draw.circle(screen, YELLOW, (planet["x"], planet["y"]), 3)

            # Show info when player is near
            dx = strategy_player_pos[0] - planet["x"]
            dy = strategy_player_pos[1] - planet["y"]
            dist = math.hypot(dx, dy)
            if dist < 50:
                font_small = pygame.font.Font(None, 18)
                if planet["has_enemy"]:
                    info = font_small.render("ENEMY!", True, RED)
                elif planet["visited"]:
                    info = font_small.render(f"Fuel: {planet['fuel']}", True, (120, 120, 120))
                else:
                    info = font_small.render(f"Fuel: {planet['fuel']} Art: {planet['artifacts']}", True, WHITE)
                screen.blit(info, (planet["x"] - info.get_width() // 2, planet["y"] - 25))

        # Draw player
        pygame.draw.circle(screen, GREEN, (int(strategy_player_pos[0]), int(strategy_player_pos[1])), SYSTEM_RADIUS // 2)

        # Strategy HUD
        font = pygame.font.Font(None, 22)

        # Fuel bar
        fuel_pct = player_state["fuel"] / get_fuel_capacity()
        fuel_color = GREEN if fuel_pct > 0.3 else YELLOW if fuel_pct > 0.15 else RED
        pygame.draw.rect(screen, (40, 40, 40), (10, 10, 104, 16))
        pygame.draw.rect(screen, fuel_color, (12, 12, int(100 * fuel_pct), 12))
        fuel_text = font.render(f"Fuel: {int(player_state['fuel'])}/{int(get_fuel_capacity())}", True, WHITE)
        screen.blit(fuel_text, (120, 10))

        # Artifacts
        artifact_text = font.render(f"Artifacts: {player_state['artifacts']}", True, YELLOW)
        screen.blit(artifact_text, (10, 32))

        # Upgrade hints
        hint_font = pygame.font.Font(None, 18)
        hints = [
            f"1:Rot({player_state['upgrades']['rotation_speed']})",
            f"2:Acc({player_state['upgrades']['acceleration']})",
            f"3:Tank({player_state['upgrades']['fuel_capacity']})",
            f"4:MG({player_state['upgrades']['machine_gun_damage']})",
            f"5:Mis({player_state['upgrades']['missile_damage']})",
        ]
        hint_text = hint_font.render("Upgrades: " + " | ".join(hints), True, (150, 150, 150))
        screen.blit(hint_text, (10, SCREEN_HEIGHT - 22))

        controls_text = hint_font.render("Arrows: Move | SPACE: Land on planet", True, (100, 100, 100))
        screen.blit(controls_text, (10, SCREEN_HEIGHT - 38))

    elif game_state == GAME_SHIP_SELECT:
        # Ship selection screen
        font_title = pygame.font.Font(None, 48)
        title = font_title.render("SELECT YOUR SHIP", True, WHITE)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 60))

        font_info = pygame.font.Font(None, 24)
        font_small = pygame.font.Font(None, 20)

        for i, ship_key in enumerate(SHIP_TYPE_ORDER):
            cfg = SHIP_TYPES[ship_key]
            x = 130 + i * 220
            y = 200

            # Draw ship preview
            preview = pygame.Surface((50, 50), pygame.SRCALPHA)
            pts = [(50, 25), (0, 0), (0, 50)]
            pygame.draw.polygon(preview, cfg["color_player"], pts)
            screen.blit(preview, (x - 25, y))

            # Ship name
            name = font_info.render(f"{i+1}. {cfg['name']}", True, cfg["color_player"])
            screen.blit(name, (x - name.get_width() // 2, y + 60))

            # Stats
            stats = [
                f"Speed: {'*' * int(cfg['max_speed'])}",
                f"Shields: {cfg['shields']}",
                f"Special: {cfg['special'].title()}",
            ]
            for j, stat in enumerate(stats):
                st = font_small.render(stat, True, (180, 180, 180))
                screen.blit(st, (x - st.get_width() // 2, y + 85 + j * 18))

            # Description
            desc = font_small.render(cfg["description"], True, (120, 120, 120))
            screen.blit(desc, (x - desc.get_width() // 2, y + 150))

        hint = font_small.render("Press 1, 2, or 3 to select | M to toggle sound", True, (100, 100, 100))
        screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 40))

    elif game_state == GAME_GALAXY_SELECT:
        # Galaxy selection screen with visual galaxies
        font_title = pygame.font.Font(None, 48)
        title = font_title.render("SELECT GALAXY", True, WHITE)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 30))

        font_name = pygame.font.Font(None, 22)
        font_num = pygame.font.Font(None, 28)
        font_small = pygame.font.Font(None, 18)

        galaxy_radius = 55
        spacing = SCREEN_WIDTH // (NUM_GALAXIES + 1)

        for i in range(1, NUM_GALAXIES + 1):
            cfg = GALAXY_CONFIG[i]
            x = spacing * i
            y = 200

            unlocked = i == 1 or (i - 1) in galaxy_progress["completed"]
            completed = i in galaxy_progress["completed"]

            # Draw galaxy visual
            draw_galaxy_image(screen, x, y, galaxy_radius, cfg["color"], cfg["core_color"], locked=not unlocked)

            # Draw number above galaxy
            num_color = GREEN if completed else (WHITE if unlocked else (60, 60, 60))
            num_text = font_num.render(str(i), True, num_color)
            screen.blit(num_text, (x - num_text.get_width() // 2, y - galaxy_radius - 25))

            # Draw name below galaxy
            name_color = cfg["color"] if unlocked else (60, 60, 60)
            name_text = font_name.render(cfg["name"], True, name_color)
            screen.blit(name_text, (x - name_text.get_width() // 2, y + galaxy_radius + 10))

            # Draw status
            if completed:
                status = font_small.render("COMPLETE", True, GREEN)
                screen.blit(status, (x - status.get_width() // 2, y + galaxy_radius + 28))
            elif not unlocked:
                status = font_small.render("LOCKED", True, (80, 80, 80))
                screen.blit(status, (x - status.get_width() // 2, y + galaxy_radius + 28))

            # Show difficulty on hover area (always visible for unlocked)
            if unlocked:
                diff_text = font_small.render(f"x{cfg['enemy_hp_mult']} difficulty", True, (120, 120, 120))
                screen.blit(diff_text, (x - diff_text.get_width() // 2, y + galaxy_radius + 45))

        # Show selected ship at bottom
        ship_cfg = SHIP_TYPES[galaxy_progress["player_ship_type"]]
        ship_text = font_small.render(f"Ship: {ship_cfg['name']}", True, ship_cfg["color_player"])
        screen.blit(ship_text, (10, SCREEN_HEIGHT - 50))

        hint = font_small.render("Press 1-5 to select unlocked galaxy | M to toggle sound", True, (100, 100, 100))
        screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 25))

    elif game_state == GAME_GALAXY_COMPLETE:
        # Galaxy complete screen
        font_title = pygame.font.Font(None, 56)
        title = font_title.render("GALAXY CLEARED!", True, GREEN)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 60))

        font_info = pygame.font.Font(None, 32)
        cfg = GALAXY_CONFIG[galaxy_progress["current_galaxy"]]
        gal_name = font_info.render(f"{cfg['name']} Complete", True, WHITE)
        screen.blit(gal_name, (SCREEN_WIDTH // 2 - gal_name.get_width() // 2, SCREEN_HEIGHT // 2))

        font_small = pygame.font.Font(None, 24)
        cont = font_small.render("Press SPACE to continue", True, (150, 150, 150))
        screen.blit(cont, (SCREEN_WIDTH // 2 - cont.get_width() // 2, SCREEN_HEIGHT // 2 + 50))

    elif game_state == GAME_OVER:
        # Game over screen
        font = pygame.font.Font(None, 48)
        if game_over_reason == "OUT_OF_FUEL":
            text = font.render("Out of Fuel!", True, RED)
        elif game_over_reason == "DESTROYED":
            text = font.render("Ship Destroyed!", True, RED)
        elif game_over_reason == "VICTORY":
            text = font.render("VICTORY! All Galaxies Cleared!", True, GREEN)
        else:
            text = font.render("Game Over", True, RED)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        screen.blit(text, text_rect)

        font_small = pygame.font.Font(None, 28)
        restart_text = font_small.render("Press N to start new game", True, WHITE)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        screen.blit(restart_text, restart_rect)

    elif game_state == GAME_BATTLE:
        # Draw battle planet first (background)
        if battle_planet:
            battle_planet.draw(screen)

        # Draw ships
        player_group.draw(screen)
        computer_group.draw(screen)

        # Draw shield effect if active
        if player.shield_active:
            pygame.draw.circle(screen, (100, 150, 255), (int(player.x), int(player.y)), SHIP_SIZE, 3)
        if computer.shield_active:
            pygame.draw.circle(screen, (255, 150, 100), (int(computer.x), int(computer.y)), SHIP_SIZE, 3)

        # Draw bullets and drones
        player_bullets.draw(screen)
        computer_bullets.draw(screen)
        player_drones.draw(screen)
        computer_drones.draw(screen)

        # HUD
        font = pygame.font.Font(None, 24)
        p_shields = font.render(f"{SHIP_TYPES[player.ship_type]['name']}: {player.shields}/{player.max_shields}", True, player.color)
        c_shields = font.render(f"{SHIP_TYPES[computer.ship_type]['name']}: {computer.shields}/{computer.max_shields}", True, computer.color)
        screen.blit(p_shields, (10, 10))
        screen.blit(c_shields, (SCREEN_WIDTH - c_shields.get_width() - 10, 10))

        # Special cooldown indicator
        font_small = pygame.font.Font(None, 18)
        if player.special_cooldown > 0:
            cd_text = font_small.render(f"Special: {player.special_cooldown // 60 + 1}s", True, (150, 150, 150))
        else:
            cd_text = font_small.render(f"Special: READY ({player.special_type})", True, GREEN)
        screen.blit(cd_text, (10, 30))

        # Controls hint
        hint = font_small.render("UP: Thrust | Arrows: Turn | SPACE: Shoot | SHIFT: Special | M: Mute", True, (80, 80, 80))
        screen.blit(hint, (10, SCREEN_HEIGHT - 20))

    pygame.display.flip()  # Update the display
    clock.tick(60)  # Limit frame rate to 60 FPS

pygame.quit()
