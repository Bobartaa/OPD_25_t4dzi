import pygame
import random
import sys
import math 
pygame.init()
# ================================================
#  Конфигурация
# ================================================
WIDTH, HEIGHT = 420, 600  
BASE_WIDTH = 800
BASE_HEIGHT = 480

# Коэффициенты масштабирования
SCALE_X = WIDTH / BASE_WIDTH
SCALE_Y = HEIGHT / BASE_HEIGHT

# Функция для масштабирования чисел
def scale(val, scale_factor):
    return int(val * scale_factor)

# Функции для масштабирования по осям X и Y   
def sx(val): return scale(val, SCALE_X)
def sy(val): return scale(val, SCALE_Y)   

# Цвета
WHITE     = (255, 255, 255)
BLACK     = (  0,   0,   0)
RED       = (255,   0,   0)
GREEN     = (  0, 255,   0)
BLUE      = (  0,   0, 255)
YELLOW    = (255, 255,   0)
LIGHTGRAY = (170, 170, 170)

# ================================================
#  Классы фон/игрок/пули 
# ================================================
class Background(pygame.sprite.Sprite):
    def __init__(self, x):
        super().__init__()
        match x:
            case 0:
                self.background = pygame.image.load("images/backgrounds/background.png")
            case 1:
                self.background = pygame.image.load("images/backgrounds/background1.png")
            case 2:
                self.background = pygame.image.load("images/backgrounds/background2.png")
            case 3:
                self.background = pygame.image.load("images/backgrounds/background3.png")
            case 4:
                self.background = pygame.image.load("images/backgrounds/background4.jpg")
            case 5:
                self.background = pygame.image.load("images/backgrounds/background5.jpg")
            case 6:
                self.background = pygame.image.load("images/backgrounds/background6.png")
        self.image = pygame.transform.scale(self.background, (WIDTH, HEIGHT))
        self.rect = self.image.get_rect()
# ================================================
#  Классы игровых объектов
# ================================================
class Player(pygame.sprite.Sprite):
    sprite = None
    def __init__(self, health):
        super().__init__()
        if Player.sprite is None:
            img = pygame.image.load("images/player/player.png")
            Player.sprite = pygame.transform.scale(img, (sx(100),sy(50)))
        self.image = Player.sprite
        self.rect = self.image.get_rect()
        self.rect.centerx = WIDTH // 2
        self.rect.bottom = HEIGHT - 10
        self.health = health
        self.shield = 0 # счётчик щита
        # Поля для автопушки
        self.autofire = False
        self.autofire_end_time = 0
        self.last_autofire_shot = 0
        # Поле для задержки выстрелов
        self.last_shot = 0

    def update(self):
        keys = pygame.key.get_pressed()
        dx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = sx(-15)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = sx(15)

        self.rect.x += dx
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH

class Bullet(pygame.sprite.Sprite):
    sprite = None
    def __init__(self, x, y):
        super().__init__()
        if Bullet.sprite is None:
            img = pygame.image.load("images/bullet/playerbullet.png")
            Bullet.sprite = pygame.transform.scale(img, (sx(12), sy(43)))
        self.image = Bullet.sprite
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed_y = sy(-15)

    def update(self):
        self.rect.y += self.speed_y
        if self.rect.bottom < 0:
            self.kill()

class Boss(pygame.sprite.Sprite):
    """Босс для 5‑го уровня."""
    sprite = None
    def __init__(self, game):
        super().__init__()
        self.game = game
        if Boss.sprite is None:
            img = pygame.image.load("images/enemies/boss.png")
            Boss.sprite = pygame.transform.scale(img, (sx(350), sy(200)))
        self.image = Boss.sprite
        self.rect = self.image.get_rect()
        self.rect.centerx = (WIDTH // 2) + 20
        self.rect.top = -30  # небольшое смещение от верхнего края
        self.health = 100
        self.is_fighter = False
        self.is_alien   = False
        self.is_boss    = True
        self.speed_y = 0  # не двигается

        #  стрельба
        self.shoot_delay = 800
        self.last_shot   = pygame.time.get_ticks() - self.shoot_delay  # сразу может стрелять

        # интрудер каждые 5 потерянных HP
        self.next_intruder_hp = self.health - 5

        # ▼ состояние «шквала»
        now = pygame.time.get_ticks()
        self.rapidfire_next = now + 10000  # первый запуск через 10 с
        self.rapidfire_end  = 0
        self.in_rapidfire   = False
        self._delay_backup  = self.shoot_delay          # храним обычную задержку

    def update(self):
        now = pygame.time.get_ticks()
        if not self.in_rapidfire and now >= self.rapidfire_next:
            # включаем шквал
            self.in_rapidfire = True
            self.rapidfire_end = now + 7000
            self._delay_backup = self.shoot_delay
            self.shoot_delay = 250                      # стреляем каждый кадр
        elif self.in_rapidfire and now >= self.rapidfire_end:
            # выключаем шквал
            self.in_rapidfire = False
            self.shoot_delay = self._delay_backup
            self.rapidfire_next = now + 10000
        if now - self.last_shot >= self.shoot_delay:
            # случайная точка по ширине босса
            bullet_x = random.randint(
                self.rect.left + 27 // 2,
                self.rect.right - 27 // 2
            )
            bullet_y = self.rect.bottom
            #  целимся в игрока
            target = self.game.player.rect.center
            bullet = BossBullet(bullet_x, bullet_y, target)
            self.game.enemy_bullets.add(bullet)
            self.game.all_sprites.add(bullet)

            self.last_shot = now

class Enemy(pygame.sprite.Sprite):
    asteroid_sprite = None
    fighter_sprite  = None
    alien_sprite    = None
    def __init__(self, level, is_fighter=False, is_alien=False):
        super().__init__()
        if is_alien:
            if Enemy.alien_sprite is None:
                img = pygame.image.load("images/enemies/alien.png")
                Enemy.alien_sprite = pygame.transform.scale(img, (sx(100), sy(60)))
            self.image = Enemy.alien_sprite
        elif is_fighter:
            if Enemy.fighter_sprite is None:
                img = pygame.image.load("images/enemies/fighter.png")
                Enemy.fighter_sprite = pygame.transform.scale(img, (sx(100), sy(60)))
            self.image = Enemy.fighter_sprite
        else:  # обычный астероид
            if Enemy.asteroid_sprite is None:
                img = pygame.image.load("images/enemies/asteroid.png")
                Enemy.asteroid_sprite = pygame.transform.scale(img, (sx(100), sy(70)))
            self.image = Enemy.asteroid_sprite
        self.rect = self.image.get_rect()
        self.speed_y = sy(3)
        self.is_fighter = is_fighter
        self.is_alien = is_alien
        self.is_boss = False
        self.health = 1

    def update(self):
        self.rect.y += self.speed_y
        if self.rect.top > HEIGHT + 10:
            self.kill()

class ShootingEnemy(Enemy):
    """Класс истребителя, который стреляет."""
    def __init__(self, game):
        super().__init__(level=None, is_fighter=True, is_alien=False)
        self.game = game
        self.shoot_delay = 3000
        self.last_shot = pygame.time.get_ticks() - self.shoot_delay 
    def update(self):
        super().update()
        now = pygame.time.get_ticks()
        if now - self.last_shot >= self.shoot_delay:
            bullet = EnemyBullet(self.rect.centerx, self.rect.bottom)
            self.game.enemy_bullets.add(bullet)
            self.game.all_sprites.add(bullet)
            self.last_shot = now

class Alien(Enemy):
    """Класс инопланетян: стреляют очередью из 3 пуль каждые 3 секунды."""
    def __init__(self, game):
        super().__init__(level=None, is_fighter=False, is_alien=True)
        self.game = game
        self.shoot_delay = 3000
        self.last_shot = pygame.time.get_ticks() - self.shoot_delay
    def update(self):
        super().update()
        now = pygame.time.get_ticks()
        if now - self.last_shot >= self.shoot_delay:
            offsets = [-10, 0, 10]
            for off in offsets:
                bullet = EnemyBullet(self.rect.centerx + off, self.rect.bottom)
                self.game.enemy_bullets.add(bullet)
                self.game.all_sprites.add(bullet)
            self.last_shot = now

class Intruder(Enemy):
    """Новый враг для 4 уровня (Intruder)."""
    sprite = None
    def __init__(self, game):
        super().__init__(level=None, is_fighter=False, is_alien=False)
        self.game = game
        if Intruder.sprite is None:
            img = pygame.image.load("images/enemies/intruder.png")
            Intruder.sprite = pygame.transform.scale(img, (sx(100), sy(70)))
        self.image = Intruder.sprite   
        self.speed_y = 0  # не опускается вниз    
        self.speed_x = sx(1)+1  
        self.center_x = random.randint(0, WIDTH - 72)
        self.rect.x = self.center_x
        self.rect.y = random.randint(0, HEIGHT // 2 - 72)
        self.radius = 50
        self.direction = 1
        self.health = 1 
        self.shoot_delay = 3000
        self.last_shot = pygame.time.get_ticks() - self.shoot_delay
    def update(self):
        # Движение влево-вправо в заданном радиусе
        self.rect.x += self.speed_x * self.direction
        if self.rect.x > self.center_x + self.radius:
            self.direction = -1
        if self.rect.x < self.center_x - self.radius:
            self.direction = 1
        now = pygame.time.get_ticks()
        if now - self.last_shot >= self.shoot_delay:
            bullet = EnemyBullet(self.rect.centerx, self.rect.bottom)
            self.game.enemy_bullets.add(bullet)
            self.game.all_sprites.add(bullet)
            self.last_shot = now

class EnemyBullet(pygame.sprite.Sprite):
    sprite = None
    def __init__(self, x, y):
        super().__init__()
        if EnemyBullet.sprite is None:
            img = pygame.image.load("images/bullet/enemybullet.png")
            EnemyBullet.sprite = pygame.transform.scale(img, (sx(27), sy(27)))
        self.image = EnemyBullet.sprite
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.top = y
        self.speed_y = sy(8)
    def update(self):
        self.rect.y += self.speed_y
        if self.rect.top > HEIGHT:
            self.kill()

class BossBullet(pygame.sprite.Sprite):
    """Пуля, летящая по направлению к игроку с той же скоростью, что обычная."""
    sprite = None
    def __init__(self, x, y, target_pos):
        super().__init__()
        if BossBullet.sprite is None:
            img = pygame.image.load("images/bullet/enemybullet.png")
            BossBullet.sprite = pygame.transform.scale(img, (sx(27), sy(27)))
        self.image = BossBullet.sprite
        self.rect = self.image.get_rect(center=(x, y))

        dx = target_pos[0] - x
        dy = target_pos[1] - y
        length = math.hypot(dx, dy) or 1      
        self.vx = 8 * dx / length
        self.vy = 8 * dy / length

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        # убираем пулю, если она ушла с экрана
        if (self.rect.bottom < 0 or self.rect.top > HEIGHT or
            self.rect.right < 0 or self.rect.left > WIDTH):
            self.kill()

class HealthPack(pygame.sprite.Sprite):
    sprite = None
    def __init__(self, game):
        super().__init__()
        self.game = game
        if HealthPack.sprite is None:
            img = pygame.image.load("images/buffs/apteka.png")
            HealthPack.sprite = pygame.transform.scale(img, (sx(80), sy(40)))
        self.image = HealthPack.sprite
        self.rect = self.image.get_rect()
        x, y = self.game.get_safe_position(54)
        self.rect.x = x
        self.rect.y = y
        self.speed_y = sy(2)
    def update(self):
        self.rect.y += self.speed_y
        if self.rect.top > HEIGHT + 10:
            self.kill()

class Shield(pygame.sprite.Sprite):
    sprite = None
    def __init__(self, game):
        super().__init__()
        self.game = game
        if Shield.sprite is None:
            img = pygame.image.load("images/buffs/shield.png")
            Shield.sprite = pygame.transform.scale(img, (sx(80), sy(40)))
        self.image = Shield.sprite
        self.rect = self.image.get_rect()
        x, y = self.game.get_safe_position(54)
        self.rect.x = x
        self.rect.y = y
        self.speed_y = sy(2)
    def update(self):
        self.rect.y += self.speed_y
        if self.rect.top > HEIGHT + 10:
            self.kill()

class AutoFirePack(pygame.sprite.Sprite):
    """Новый предмет для автопушки."""
    sprite = None
    def __init__(self, game):
        super().__init__()
        self.game = game
        if AutoFirePack.sprite is None:
            img = pygame.image.load("images/buffs/blast.png")
            AutoFirePack.sprite = pygame.transform.scale(img, (sx(80), sy(40)))
        self.image = AutoFirePack.sprite
        self.rect = self.image.get_rect()
        x, y = self.game.get_safe_position(54)
        self.rect.x = x
        self.rect.y = y
        self.speed_y = sy(2)
    def update(self):
        self.rect.y += self.speed_y
        if self.rect.top > HEIGHT + 10:
            self.kill()

# ================================================
#  Основной класс игры
# ================================================
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Shooter: 6 уровней")
        self.current_music = None
        self.music_folder = "sounds"
        self.shoot_sound = pygame.mixer.Sound("sounds/shot.mp3")
        self.shoot_sound.set_volume(0.7)
        self.autofire_sound = pygame.mixer.Sound("sounds/autofire.wav")
        self.autofire_sound.set_volume(0.4) 
        self.shoot_start_time = 0 
        self.game_over_sound = pygame.mixer.Sound("sounds/death.mp3")
        self.game_over_sound_played = False
        pygame.mixer.music.set_volume(1)
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("fonts/PressStart2P-vaV7.ttf", 24)
        self.running = True
        self.state = "MENU" 
        self.all_sprites    = pygame.sprite.Group()
        self.set_background(0)
        self.level = 1
        self.score = 0
        self.player_health = 10

        # Level 1
        self.spawned_asteroids_lvl1 = 0
        self.total_asteroids_lvl1   = 40
        self.killed_asteroids_lvl1  = 0
        # Level 2
        self.spawned_asteroids_lvl2 = 0
        self.spawned_fighters_lvl2  = 0
        self.total_asteroids_lvl2   = 25
        self.total_fighters_lvl2    = 25
        self.killed_asteroids_lvl2  = 0
        self.killed_fighters_lvl2   = 0
        # Level 3
        self.spawned_asteroids_lvl3 = 0
        self.spawned_fighters_lvl3  = 0
        self.spawned_aliens_lvl3    = 0
        self.total_asteroids_lvl3   = 30
        self.total_fighters_lvl3    = 25
        self.total_aliens_lvl3      = 15
        self.killed_asteroids_lvl3  = 0
        self.killed_fighters_lvl3   = 0
        self.killed_aliens_lvl3     = 0
        # Level 4
        self.spawned_asteroids_lvl4   = 0
        self.spawned_fighters_lvl4    = 0
        self.spawned_aliens_lvl4      = 0
        self.killed_asteroids_lvl4    = 0
        self.killed_fighters_lvl4     = 0
        self.killed_aliens_lvl4       = 0
        self.killed_for_intruder      = 0
        self.spawned_intruders_lvl4   = 0
        self.killed_intruders_lvl4    = 0

        # Level 5 — босс
        self.boss = None
        self.boss_phase2_started = False

        # Level 6 — бесконечный
        self.spawned_intruders_lvl6   = 0   
        self.last_pack_spawn_lvl6     = 0   
        self.last_shield_spawn_lvl6   = 0
        self.last_autofire_spawn_lvl6 = 0

        # Пакеты/щит/авто‑огонь 
        self.spawned_packs_lvl2 = 0;  self.total_packs_lvl2 = 3; self.last_pack_spawn_lvl2 = 0

        self.spawned_packs_lvl3 = 0;  self.total_packs_lvl3 = 4; self.last_pack_spawn_lvl3 = 0
        self.spawned_shields_lvl3 = 0; self.total_shields_lvl3 = 3; self.last_shield_spawn_lvl3 = 0

        self.spawned_packs_lvl4 = 0;  self.total_packs_lvl4 = 5; self.last_pack_spawn_lvl4 = 0
        self.spawned_shields_lvl4 = 0; self.total_shields_lvl4 = 3; self.last_shield_spawn_lvl4 = 0
        self.spawned_autofire_lvl4 = 0; self.total_autofire_lvl4 = 2; self.last_autofire_spawn_lvl4 = 0

        # уровень 5 (босс) 
        self.last_pack_spawn_lvl5    = 0   # аптечка   (15 с)
        self.last_shield_spawn_lvl5  = 0   # щит       (20 с)
        self.last_autofire_spawn_lvl5 = 0  # супер-пушка (30 с)

        # Группы спрайтов
        self.enemies        = pygame.sprite.Group()
        self.bullets        = pygame.sprite.Group()
        self.enemy_bullets  = pygame.sprite.Group()
        self.health_packs   = pygame.sprite.Group()
        self.shields        = pygame.sprite.Group()
        self.autofires      = pygame.sprite.Group()
        self.intruders      = pygame.sprite.Group()

        self.player = None
        # Таймер спавна врагов
        self.last_enemy_spawn = 0

        # Кнопки меню / паузы
        self.menu_buttons  = []
        self.pause_buttons = []
        self.create_menu_buttons()
        self.create_pause_buttons()

    # -----------------------------------------------
    #  Вспомогательные функции (фон, музыка, меню)
    # -----------------------------------------------
    def set_background(self, level):
        #Устанавливает фон в зависимости от уровня
        bg_num = min(level, 6)  
        self.background = Background(bg_num)
        if self.background not in self.all_sprites:
            self.all_sprites.add(self.background)

    def play_music(self, level):
        #Проигрывает соответствующую музыку для уровня или меню.
        if hasattr(self, 'game_over_sound') and self.game_over_sound_played:
            self.game_over_sound.stop()
            self.game_over_sound_played = False 
        if level == "MENU":
            music_file = "sounds/level0.mp3"
        else:
            track = level if isinstance(level, int) and level <= 6 else 6
            music_file = f"sounds/level{track}.mp3"
        try:
            pygame.mixer.music.load(music_file)
            pygame.mixer.music.play(-1) # -1 — бесконечное воспроизведение
            self.current_music = level
        except pygame.error as e:
            print(f"Не могу загрузить музыку: {e}")

    def create_menu_buttons(self):
        self.menu_buttons = []  
        texts = [f"Level {i}" for i in range(1, 7)] + ["Quit"]
        y_start = HEIGHT // 2 - 220
        for idx, text in enumerate(texts):
            rect = pygame.Rect(0, 0, 300, 50)
            rect.centerx = WIDTH // 2
            rect.y = y_start + idx * 70
            self.menu_buttons.append((rect, text))

    def create_pause_buttons(self):
        texts = ["Resume", "Main Menu"]
        y_start = HEIGHT // 2 - 50
        for idx, text in enumerate(texts):
            rect = pygame.Rect(0, 0, 300, 50)
            rect.centerx = WIDTH // 2
            rect.y = y_start + idx * 70
            self.pause_buttons.append((rect, text))

    # -----------------------------------------------
    #  Инициализация нового уровня
    # -----------------------------------------------
    def new_level(self):
        self.all_sprites.empty(); self.enemies.empty(); self.bullets.empty(); self.enemy_bullets.empty()
        self.health_packs.empty(); self.shields.empty(); self.autofires.empty(); self.intruders.empty()

        # Устанавливаем фон для текущего уровня
        self.set_background(self.level)
        self.play_music("MENU")
        self.player_health = 10
        self.player = Player(self.player_health)
        self.all_sprites.add(self.player)

        now = pygame.time.get_ticks()
        self.last_enemy_spawn = now
        self.last_pack_spawn_lvl2 = now
        self.last_pack_spawn_lvl3 = self.last_shield_spawn_lvl3 = now
        self.last_pack_spawn_lvl4 = self.last_shield_spawn_lvl4 = self.last_autofire_spawn_lvl4 = now

        self.score = 0
        self.play_music(self.level)

        # Сброс всех счётчиков по уровням
        if self.level == 1:
            self.spawned_asteroids_lvl1 = 0; self.killed_asteroids_lvl1 = 0
        elif self.level == 2:
            self.spawned_asteroids_lvl2 = 0; self.spawned_fighters_lvl2 = 0
            self.killed_asteroids_lvl2 = 0; self.killed_fighters_lvl2 = 0
            self.spawned_packs_lvl2 = 0
        elif self.level == 3:
            self.spawned_asteroids_lvl3 = 0; self.spawned_fighters_lvl3 = 0; self.spawned_aliens_lvl3 = 0
            self.killed_asteroids_lvl3 = 0; self.killed_fighters_lvl3 = 0; self.killed_aliens_lvl3 = 0
            self.spawned_packs_lvl3 = 0; self.spawned_shields_lvl3 = 0
        elif self.level == 4:
            self.spawned_asteroids_lvl4 = 0; self.spawned_fighters_lvl4 = 0; self.spawned_aliens_lvl4 = 0
            self.killed_asteroids_lvl4 = 0; self.killed_fighters_lvl4 = 0; self.killed_aliens_lvl4 = 0
            self.killed_for_intruder = 0; self.spawned_intruders_lvl4 = 0; self.killed_intruders_lvl4 = 0
            self.spawned_packs_lvl4 = 0; self.spawned_shields_lvl4 = 0; self.spawned_autofire_lvl4 = 0
        elif self.level == 5:
            self.boss = Boss(self)
            self.enemies.add(self.boss)
            self.all_sprites.add(self.boss)
            self.last_pack_spawn_lvl5    = now
            self.last_shield_spawn_lvl5  = now
            self.last_autofire_spawn_lvl5 = now
            self.boss_phase2_started = False
        else:
            self.spawned_intruders_lvl6 = 0
            now = pygame.time.get_ticks()
            self.last_pack_spawn_lvl6     = now
            self.last_shield_spawn_lvl6   = now
            self.last_autofire_spawn_lvl6 = now

        self.level_start_time = now

    # -----------------------------------------------
    #  Поддержка безопасного спавна
    # -----------------------------------------------
    def is_position_safe(self, rect):
        """Проверяет, не пересекается ли новый объект с существующими."""
        for sprite in self.all_sprites:
            if hasattr(sprite, 'rect') and rect.colliderect(sprite.rect):
                return False
        return True

    def get_safe_position(self, size):
        """Возвращает безопасную позицию для спавна объекта."""
        for _ in range(10):
            x = random.randint(0, WIDTH - size)
            y = random.randint(-150, -40)
            if self.is_position_safe(pygame.Rect(x, y, size, size)):
                return x, y
        return random.randint(0, WIDTH - size), random.randint(-300, -150)

    #  логика фаз босса
    def boss_phase_logic(self):
        if self.level != 5 or self.boss is None:
            return
        # запуск «волны» после 50 % HP
        if (not self.boss_phase2_started) and self.boss.health <= 100 // 2:
            self.boss_phase2_started = True   
        attempts = 0

        # интрудер каждые 5 потерянных HP
        while self.boss.health <= self.boss.next_intruder_hp and attempts < 10:
            intr = Intruder(self)
            min_y = self.boss.rect.bottom + 10
            max_y = HEIGHT // 2 - 72
            
            if min_y > max_y:
                min_y = max_y - 10  
                if min_y < 0:
                    min_y = 0 
            
            intr.rect.y = random.randint(min_y, max_y)
            intr.rect.x = random.randint(0, WIDTH - 72)
            if not intr.rect.colliderect(self.boss.rect):   
                self.intruders.add(intr); 
                self.all_sprites.add(intr); 
                self.enemies.add(intr)
            self.boss.next_intruder_hp -= 5
            attempts += 1

    # -----------------------------------------------
    #  Задержка спавна врагов
    # -----------------------------------------------
    def compute_spawn_delay(self):
        """Вычисляет текущую задержку (ms) перед спавном нового врага."""
        if self.level == 1:
            base_delay, min_delay = 1000, 600
            steps = self.killed_asteroids_lvl1 // 5
        elif self.level == 2:
            base_delay, min_delay = 1000, 600
            total_kills = self.killed_asteroids_lvl2 + self.killed_fighters_lvl2
            steps = total_kills // 5
        elif self.level == 3:
            base_delay, min_delay = 1000, 750
            total_kills = self.killed_asteroids_lvl3 + self.killed_fighters_lvl3 + self.killed_aliens_lvl3
            steps = total_kills // 5
        elif self.level == 4:
            base_delay, min_delay = 1000, 600
            total_kills = (self.killed_asteroids_lvl4 +
                           self.killed_fighters_lvl4 +
                           self.killed_aliens_lvl4 +
                           self.killed_intruders_lvl4)
            steps = total_kills // 5          # каждые 5 убийств ускоряем спавн
        elif self.level == 5:
            if self.boss and self.boss.health <= 100 // 2:
                base_delay, min_delay = 1000, 1200      # как на уровне-4
                steps = (100 // 2 - self.boss.health) // 3
                return max(base_delay - steps * 100, min_delay)
            return 999_999                             # до 50 % никого
        else:  # уровень 6
            base_delay, min_delay = 1000, 600
            steps = self.score // 10
        return max(base_delay - steps * 100, min_delay)

    # -----------------------------------------------
    #  Логика спавна врагов
    # -----------------------------------------------
    def spawn_enemy(self):
        """Спавн врагов по логике каждого уровня."""
        now = pygame.time.get_ticks()

        if self.level == 1:
            if self.spawned_asteroids_lvl1 < self.total_asteroids_lvl1:
                e = Enemy(level=1, is_fighter=False)
                x, y = self.get_safe_position(96)
                e.rect.x = x
                e.rect.y = y

                self.enemies.add(e)
                self.all_sprites.add(e)
                self.spawned_asteroids_lvl1 += 1

        elif self.level == 2:
            spawn_type = random.choice(["asteroid", "fighter"]) if self.killed_asteroids_lvl2 >= 5 else "asteroid"
            if spawn_type == "fighter" and self.spawned_fighters_lvl2 < self.total_fighters_lvl2:
                f = ShootingEnemy(self)
                x, y = self.get_safe_position(72)
                f.rect.x = x
                f.rect.y = y

                self.enemies.add(f)
                self.all_sprites.add(f)
                self.spawned_fighters_lvl2 += 1
            elif self.spawned_asteroids_lvl2 < self.total_asteroids_lvl2:
                e = Enemy(level=2, is_fighter=False)
                x, y = self.get_safe_position(96)
                e.rect.x = x
                e.rect.y = y

                self.enemies.add(e)
                self.all_sprites.add(e)
                self.spawned_asteroids_lvl2 += 1

        elif self.level == 3:
            spawn_options = []

            if self.spawned_asteroids_lvl3 < self.total_asteroids_lvl3:
                spawn_options.append("asteroid")

            if self.killed_asteroids_lvl3 >= 5 and self.spawned_fighters_lvl3 < self.total_fighters_lvl3:
                spawn_options.append("fighter")

            if self.killed_fighters_lvl3 >= 5 and self.spawned_aliens_lvl3 < self.total_aliens_lvl3:
                spawn_options.append("alien")

            if spawn_options:
                spawn_type = random.choice(spawn_options)
                if spawn_type == "asteroid":
                    e = Enemy(level=3, is_fighter=False)
                    x, y = self.get_safe_position(96)
                    e.rect.x = x
                    e.rect.y = y
                    self.enemies.add(e)
                    self.all_sprites.add(e)
                    self.spawned_asteroids_lvl3 += 1

                elif spawn_type == "fighter":
                    f = ShootingEnemy(self)
                    x, y = self.get_safe_position(72)
                    f.rect.x = x
                    f.rect.y = y
                    self.enemies.add(f)
                    self.all_sprites.add(f)
                    self.spawned_fighters_lvl3 += 1

                elif spawn_type == "alien":
                    a = Alien(self)
                    x, y = self.get_safe_position(72)
                    a.rect.x = x
                    a.rect.y = y
                    self.enemies.add(a)
                    self.all_sprites.add(a)
                    self.spawned_aliens_lvl3 += 1

        elif self.level == 4:
            #  спавним ОДНОГО врага случайного типа 
            options = []
            if self.spawned_asteroids_lvl4 < 25:
                options.append("asteroid")
            if self.spawned_fighters_lvl4 < 25:
                options.append("fighter")
            if self.spawned_aliens_lvl4 < 25:
                options.append("alien")

            if not options:          
                return

            t = random.choice(options)

            if t == "asteroid":
                e = Enemy(level=4, is_fighter=False)
                x, y = self.get_safe_position(96)
                e.rect.x, e.rect.y = x, y
                self.enemies.add(e); self.all_sprites.add(e)
                self.spawned_asteroids_lvl4 += 1

            elif t == "fighter":
                f = ShootingEnemy(self)
                x, y = self.get_safe_position(72)
                f.rect.x, f.rect.y = x, y
                self.enemies.add(f); self.all_sprites.add(f)
                self.spawned_fighters_lvl4 += 1

            else:  
                a = Alien(self)
                x, y = self.get_safe_position(72)
                a.rect.x, a.rect.y = x, y
                self.enemies.add(a); self.all_sprites.add(a)
                self.spawned_aliens_lvl4 += 1

        elif self.level == 5:
            if self.boss and self.boss.health <= 100 // 2:
                t = random.choices(
                        ["asteroid", "fighter", "alien"],
                        weights=[0.4, 0.35, 0.25])[0]
                if t == "asteroid":
                    e = Enemy(level=5)
                    x, y = self.get_safe_position(96)
                    e.rect.x, e.rect.y = x, y
                    self.enemies.add(e); self.all_sprites.add(e)
                elif t == "fighter":
                    f = ShootingEnemy(self)
                    x, y = self.get_safe_position(72)
                    f.rect.x, f.rect.y = x, y
                    self.enemies.add(f); self.all_sprites.add(f)
                else:  
                    a = Alien(self)
                    x, y = self.get_safe_position(72)
                    a.rect.x, a.rect.y = x, y
                    self.enemies.add(a); self.all_sprites.add(a)

        elif self.level == 6:  # уровень 6 
            enemy_type = random.choices(
                ["asteroid", "fighter", "alien"],
                weights=[0.3, 0.4, 0.3],
                k=1
            )[0]
            if enemy_type == "asteroid":
                e = Enemy(level=5, is_fighter=False)
                x, y = self.get_safe_position(96)
                e.rect.x = x
                e.rect.y = y
                self.enemies.add(e)
                self.all_sprites.add(e)
            elif enemy_type == "fighter":
                f = ShootingEnemy(self)
                x, y = self.get_safe_position(72)
                f.rect.x = x
                f.rect.y = y
                self.enemies.add(f)
                self.all_sprites.add(f)
            else:  # alien
                a = Alien(self)
                x, y = self.get_safe_position(72)
                a.rect.x = x
                a.rect.y = y
                self.enemies.add(a)
                self.all_sprites.add(a)

    # --------------------------
    #  Спавн бафов / интрудеров
    # --------------------------
    def spawn_health_pack(self):
        now = pygame.time.get_ticks()
        if self.level == 2 and (now - self.last_pack_spawn_lvl2 > 10000 and self.spawned_packs_lvl2 < self.total_packs_lvl2):
            hp = HealthPack(self); self.health_packs.add(hp); self.all_sprites.add(hp)
            self.spawned_packs_lvl2 += 1; self.last_pack_spawn_lvl2 = now
        elif self.level == 3 and (now - self.last_pack_spawn_lvl3 > 9000 and self.spawned_packs_lvl3 < self.total_packs_lvl3):
            hp = HealthPack(self); self.health_packs.add(hp); self.all_sprites.add(hp)
            self.spawned_packs_lvl3 += 1; self.last_pack_spawn_lvl3 = now
        elif self.level == 4 and (now - self.last_pack_spawn_lvl4 > 8000 and self.spawned_packs_lvl4 < self.total_packs_lvl4):
            hp = HealthPack(self); self.health_packs.add(hp); self.all_sprites.add(hp)
            self.spawned_packs_lvl4 += 1; self.last_pack_spawn_lvl4 = now
        elif self.level == 5 and (now - self.last_pack_spawn_lvl5 > 15000):
            hp = HealthPack(self)
            self.health_packs.add(hp); self.all_sprites.add(hp)
            self.last_pack_spawn_lvl5 = now
        elif self.level == 6 and (now - self.last_pack_spawn_lvl6 > 15000):
            hp = HealthPack(self)
            self.health_packs.add(hp); self.all_sprites.add(hp)
            self.last_pack_spawn_lvl6 = now

    def spawn_shield(self):
        now = pygame.time.get_ticks()
        if self.level == 3 and (now - self.last_shield_spawn_lvl3 > 13000 and self.spawned_shields_lvl3 < self.total_shields_lvl3):
            sh = Shield(self); self.shields.add(sh); self.all_sprites.add(sh)
            self.spawned_shields_lvl3 += 1; self.last_shield_spawn_lvl3 = now
        elif self.level == 4 and (now - self.last_shield_spawn_lvl4 > 12000 and self.spawned_shields_lvl4 < self.total_shields_lvl4):
            sh = Shield(self); self.shields.add(sh); self.all_sprites.add(sh)
            self.spawned_shields_lvl4 += 1; self.last_shield_spawn_lvl4 = now
        elif self.level == 5 and (now - self.last_shield_spawn_lvl5 > 20000):
            sh = Shield(self)
            self.shields.add(sh); self.all_sprites.add(sh)
            self.last_shield_spawn_lvl5 = now
        elif self.level == 6 and (now - self.last_shield_spawn_lvl6 > 20000):
            sh = Shield(self)
            self.shields.add(sh); self.all_sprites.add(sh)
            self.last_shield_spawn_lvl6 = now

    def spawn_autofire(self):
        now = pygame.time.get_ticks()
        if self.level == 4 and (now - self.last_autofire_spawn_lvl4 > 15000 and self.spawned_autofire_lvl4 < self.total_autofire_lvl4):
            af = AutoFirePack(self); self.autofires.add(af); self.all_sprites.add(af)
            self.spawned_autofire_lvl4 += 1; self.last_autofire_spawn_lvl4 = now
        elif self.level == 5 and (now - self.last_autofire_spawn_lvl5 > 30000):
            af = AutoFirePack(self)
            self.autofires.add(af); self.all_sprites.add(af)
            self.last_autofire_spawn_lvl5 = now
        elif self.level == 6 and (now - self.last_autofire_spawn_lvl6 > 30000):
            af = AutoFirePack(self)
            self.autofires.add(af); self.all_sprites.add(af)
            self.last_autofire_spawn_lvl6 = now

    def spawn_intruder(self):
        if self.level == 4 and self.spawned_intruders_lvl4 < 10 and self.killed_for_intruder >= 7:
            intr = Intruder(self); self.intruders.add(intr); self.all_sprites.add(intr); self.enemies.add(intr)
            self.spawned_intruders_lvl4 += 1; self.killed_for_intruder -= 7
        elif (self.level == 6 and self.score // 10 > self.spawned_intruders_lvl6):
            intr = Intruder(self)
            self.intruders.add(intr); self.all_sprites.add(intr); self.enemies.add(intr)
            self.spawned_intruders_lvl6 += 1

    # -----------------------------------------------
    #  Главный цикл run / events (menu click изменён)
    # -----------------------------------------------
    def run(self):
        while self.running:
            if self.state == "MENU" and not pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                self.game_over_sound.stop()
                self.game_over_sound_played = False
                self.play_music("MENU")
            dt = self.clock.tick(60)
            self.events()
            if self.state == "PLAYING":
                self.update()
            self.draw()
        pygame.quit(); sys.exit()

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if self.state == "MENU":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = pygame.mouse.get_pos()
                    for idx, (rect, text) in enumerate(self.menu_buttons):
                        if rect.collidepoint(mx, my):
                            if idx < 6:  
                                self.level = idx + 1
                                self.new_level(); self.state = "PLAYING"
                            else:
                                self.running = False
            elif self.state == "PLAYING":
                keys = pygame.key.get_pressed()
                if keys[pygame.K_ESCAPE]:
                    self.state = "PAUSE"

                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    #  добавляем задержку выстрелов игрока
                    now = pygame.time.get_ticks()
                    # Если автопушка активна, задержки нет
                    if self.player.autofire or now - self.player.last_shot >= 250:
                        bullet = Bullet(self.player.rect.centerx, self.player.rect.top)
                        self.bullets.add(bullet)
                        self.all_sprites.add(bullet)
                        self.player.last_shot = now
                        self.shoot_start_time = now
                        self.shoot_sound.play()

                if event.type == pygame.KEYDOWN and event.key == pygame.K_t:
                    if self.enemies:
                        enemy = self.enemies.sprites()[0]
                        if self.level == 1:
                            self.killed_asteroids_lvl1 += 1
                        elif self.level == 2:
                            if enemy.is_fighter:
                                self.killed_fighters_lvl2 += 1
                            else:
                                self.killed_asteroids_lvl2 += 1
                        elif self.level == 3:
                            if enemy.is_alien:
                                self.killed_aliens_lvl3 += 1
                            elif enemy.is_fighter:
                                self.killed_fighters_lvl3 += 1
                            else:
                                self.killed_asteroids_lvl3 += 1
                        elif self.level == 4:
                            if isinstance(enemy, Intruder):
                                self.killed_intruders_lvl4 += 1
                            elif enemy.is_alien:
                                self.killed_aliens_lvl4 += 1
                            elif enemy.is_fighter:
                                self.killed_fighters_lvl4 += 1
                            else:
                                self.killed_asteroids_lvl4 += 1
                            self.score += 1
                            self.killed_for_intruder += 1
                        elif self.level == 6:
                            self.score += 1
                        enemy.kill()
            elif self.state == "PAUSE":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = pygame.mouse.get_pos()
                    for idx, (rect, text) in enumerate(self.pause_buttons):
                        if rect.collidepoint(mx, my):
                            if idx == 0:
                                self.state = "PLAYING"
                            else:
                                self.state = "MENU"
                                pygame.mixer.music.stop()  
                                self.game_over_sound_played = False  
                                self.set_background(0)
                                self.play_music("MENU")
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = "PLAYING"
            elif self.state == "LEVEL_COMPLETE":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    self.level += 1; self.new_level(); self.state = "PLAYING"
            elif self.state in ("GAME_OVER", "VICTORY"):
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    pygame.mixer.music.stop()            
                    self.game_over_sound.stop()         
                    self.game_over_sound_played = False
                    self.state = "MENU"; self.set_background(0); self.play_music("MENU")

    def update(self):
        now = pygame.time.get_ticks()
        
        if self.level == 5 and self.boss:
            self.boss_phase_logic()
        
        self.level_timer = (now - self.level_start_time) // 1000
        if hasattr(self, 'shoot_channel') and self.shoot_channel.get_busy():
            if pygame.time.get_ticks() - self.shoot_start_time > 250:
                self.shoot_channel.stop()
        spawn_delay = self.compute_spawn_delay()

        if now - self.last_enemy_spawn > spawn_delay:
            self.spawn_enemy()
            self.last_enemy_spawn = now

        self.spawn_health_pack()
        self.spawn_shield()
        self.spawn_autofire()
        self.spawn_intruder()

        self.all_sprites.update()

        # Обработка врагов, ушедших за нижнюю границу
        for enemy in list(self.enemies):
            if enemy.rect.top > HEIGHT:
                enemy.kill()
                # Переподсчёт для уровней
                if self.level == 1:
                    self.spawned_asteroids_lvl1 -= 1
                elif self.level == 2:
                    if enemy.is_fighter:
                        self.spawned_fighters_lvl2 -= 1
                    else:
                        self.spawned_asteroids_lvl2 -= 1
                elif self.level == 3:
                    if enemy.is_alien:
                        self.spawned_aliens_lvl3 -= 1
                    elif enemy.is_fighter:
                        self.spawned_fighters_lvl3 -= 1
                    else:
                        self.spawned_asteroids_lvl3 -= 1
                elif self.level == 4:
                    if isinstance(enemy, Intruder):
                        self.spawned_intruders_lvl4 -= 1
                    elif enemy.is_alien:
                        self.spawned_aliens_lvl4 -= 1
                    elif enemy.is_fighter:
                        self.spawned_fighters_lvl4 -= 1
                    else:
                        self.spawned_asteroids_lvl4 -= 1
                self.player_health -= 1
                if self.player_health <= 0:
                    if not self.game_over_sound_played:
                        pygame.mixer.music.stop()  
                        self.game_over_sound.play()  
                        self.game_over_sound_played = True
                    self.state = "GAME_OVER"
                    return

        # Столкновение игрока с врагом
        hits_player = pygame.sprite.spritecollide(self.player, self.enemies, True)
        if hits_player:
            for enemy in hits_player:
                if self.level == 1:
                    self.spawned_asteroids_lvl1 -= 1
                elif self.level == 2:
                    if enemy.is_fighter:
                        self.spawned_fighters_lvl2 -= 1
                    else:
                        self.spawned_asteroids_lvl2 -= 1
                elif self.level == 3:
                    if enemy.is_alien:
                        self.spawned_aliens_lvl3 -= 1
                    elif enemy.is_fighter:
                        self.spawned_fighters_lvl3 -= 1
                    else:
                        self.spawned_asteroids_lvl3 -= 1
                elif self.level == 4:
                    if isinstance(enemy, Intruder):
                        self.spawned_intruders_lvl4 -= 1
                    elif enemy.is_alien:
                        self.spawned_aliens_lvl4 -= 1
                    elif enemy.is_fighter:
                        self.spawned_fighters_lvl4 -= 1
                    else:
                        self.spawned_asteroids_lvl4 -= 1
                self.player_health -= 1
                if self.player_health <= 0:
                    if not self.game_over_sound_played:
                        pygame.mixer.music.stop() 
                        self.game_over_sound.play()  
                        self.game_over_sound_played = True
                    self.state = "GAME_OVER"
                    return

        # Столкновение игрока с пулей врага
        for bullet in list(self.enemy_bullets):
            if self.player.rect.colliderect(bullet.rect):
                if self.player.shield > 0:
                    self.player.shield -= 1
                    bullet.kill()
                else:
                    bullet.kill()
                    self.player_health -= 1
                    if self.player_health <= 0:
                        pygame.mixer.music.stop()
                        self.game_over_sound.play()
                        self.state = "GAME_OVER"
                        return

        # Касание игрока с аптечкой
        hits_pack = pygame.sprite.spritecollide(self.player, self.health_packs, True)
        if hits_pack:
            for _ in hits_pack:
                self.player_health += 1

        # Касание игрока с щитом
        hits_shield = pygame.sprite.spritecollide(self.player, self.shields, True)
        if hits_shield:
            for _ in hits_shield:
                self.player.shield = 3

        # Касание игрока с автопушкой
        hits_auto = pygame.sprite.spritecollide(self.player, self.autofires, True)
        if hits_auto:
            self.autofire_sound.play()  
            for _ in hits_auto:
                self.player.autofire = True
                self.player.autofire_end_time = now + 3000
                self.player.last_autofire_shot = now

        # Столкновение пули игрока и врага
        hits = pygame.sprite.groupcollide(self.enemies, self.bullets, False, True)
        if hits:
            for enemy, bullets in hits.items():
                if hasattr(enemy, 'health') and enemy.health is not None:
                    enemy.health -= len(bullets)
                if enemy.health <= 0:
                    enemy.kill()
                    #  логика завершения уровней 
                    if self.level == 1:
                        self.killed_asteroids_lvl1 += 1
                        if self.killed_asteroids_lvl1 >= self.total_asteroids_lvl1:
                            self.state = "LEVEL_COMPLETE"; return
                    elif self.level == 2:
                        if enemy.is_fighter: self.killed_fighters_lvl2 += 1
                        else: self.killed_asteroids_lvl2 += 1
                        if self.killed_asteroids_lvl2 + self.killed_fighters_lvl2 >= self.total_asteroids_lvl2 + self.total_fighters_lvl2:
                            self.state = "LEVEL_COMPLETE"; return
                    elif self.level == 3:
                        if enemy.is_alien: self.killed_aliens_lvl3 += 1
                        elif enemy.is_fighter: self.killed_fighters_lvl3 += 1
                        else: self.killed_asteroids_lvl3 += 1
                        if (self.killed_asteroids_lvl3 >= self.total_asteroids_lvl3 and
                            self.killed_fighters_lvl3 >= self.total_fighters_lvl3 and
                            self.killed_aliens_lvl3 >= self.total_aliens_lvl3):
                            self.state = "LEVEL_COMPLETE"; return
                    elif self.level == 4:
                        if isinstance(enemy, Intruder): self.killed_intruders_lvl4 += 1
                        elif enemy.is_alien: self.killed_aliens_lvl4 += 1
                        elif enemy.is_fighter: self.killed_fighters_lvl4 += 1
                        else: self.killed_asteroids_lvl4 += 1
                        self.score += 1; self.killed_for_intruder += 1
                        total_needed = 25 + 25 + 25 + 10
                        total_killed = self.killed_asteroids_lvl4 + self.killed_fighters_lvl4 + self.killed_aliens_lvl4 + self.killed_intruders_lvl4
                        if total_killed >= total_needed:
                            self.state = "LEVEL_COMPLETE"; return
                    elif self.level == 5 and getattr(enemy, 'is_boss', False):
                        self.state = "LEVEL_COMPLETE"; 
                        self.boss = None
                        return
                    elif self.level == 6:
                        self.score += 1

        # Проверки окончания уровней
        if self.level == 4:
            total_killed_lvl4 = (self.killed_asteroids_lvl4 +
                                 self.killed_fighters_lvl4 +
                                 self.killed_aliens_lvl4 +
                                 self.killed_intruders_lvl4)
            total_needed = (25 +
                            25 +
                            25 +
                            10)
            if total_killed_lvl4 >= total_needed:
                self.state = "LEVEL_COMPLETE"
                return

        # обработка автопушки 
        if self.player.autofire:
            if now >= self.player.autofire_end_time:
                self.player.autofire = False
            else:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_SPACE]:
                    if now - self.player.last_autofire_shot >= 100:
                        bullet = Bullet(self.player.rect.centerx, self.player.rect.top)
                        self.bullets.add(bullet)
                        self.all_sprites.add(bullet)
                        self.player.last_autofire_shot = now
    # -----------------------------------------------
    #  Рендеринг
    # -----------------------------------------------
    def draw(self):
        self.screen.blit(self.background.image, (0, 0))
        if self.state == "MENU":
            self.draw_text_center("MAIN MENU", 60, WHITE, y_offset=-260)
            for rect, text in self.menu_buttons:
                pygame.draw.rect(self.screen, LIGHTGRAY, rect)
                self.draw_text(text, 40, BLACK, rect.x +20, rect.y + 10)
        elif self.state == "PLAYING":
            self.all_sprites.draw(self.screen)
            if self.player.shield > 0:
                shield_radius = max(self.player.shield * 5, 20)  # радиус зависит от количества щита
                pygame.draw.circle(
                    self.screen,
                    BLUE,
                    self.player.rect.center,
                    self.player.rect.width // 2 + shield_radius,
                    3
                )
            # Таймер уровня
            self.draw_text(f"Time: {self.level_timer}", 24, WHITE, WIDTH - 160, 10)
            self.draw_text(f"HP: {self.player_health}", 24, WHITE, 10, 10)

            if self.level == 1:
                txt = f"Killed: {self.killed_asteroids_lvl1}/{self.total_asteroids_lvl1}"
                self.draw_text(txt, 24, WHITE, 10, 50)
                self.draw_text(f"Level: {self.level}", 24, WHITE, 10, 90)

            elif self.level == 2:
                txt = f"Killed: {self.killed_asteroids_lvl2 + self.killed_fighters_lvl2}/" \
                      f"{self.total_asteroids_lvl2 + self.total_fighters_lvl2}"
                self.draw_text(txt, 24, WHITE, 10, 50)
                self.draw_text(f"Level: {self.level}", 24, WHITE, 10, 90)
                if self.player.autofire:
                    rem = (self.player.autofire_end_time - pygame.time.get_ticks()) // 1000 + 1
                    self.draw_text(f"Autofire: {rem}s", 24, WHITE, 10, 130)

            elif self.level == 3:
                total_initial = (self.total_asteroids_lvl3 +
                                 self.total_fighters_lvl3 +
                                 self.total_aliens_lvl3)
                killed_initial = (self.killed_asteroids_lvl3 +
                                  self.killed_fighters_lvl3 +
                                  self.killed_aliens_lvl3)
                self.draw_text(f"Killed: {killed_initial}/{total_initial}", 24, WHITE, 10, 50)
                self.draw_text(f"Shield: {self.player.shield}", 24, WHITE, 10, 90)
                self.draw_text(f"Level: {self.level}", 24, WHITE, 10, 130)
                if self.player.autofire:
                    rem = (self.player.autofire_end_time - pygame.time.get_ticks()) // 1000 + 1
                    self.draw_text(f"Autofire: {rem}s", 24, WHITE, 10, 170)

            elif self.level == 4:
                self.draw_text(f"Killed: {self.killed_asteroids_lvl4 + self.killed_fighters_lvl4 + self.killed_aliens_lvl4 + self.killed_intruders_lvl4}/{25 + 25 + 25 + 10}", 24, WHITE, 10, 50)
                self.draw_text(f"Shield: {self.player.shield}", 24, WHITE, 10, 90)
                self.draw_text(f"Level: {self.level}", 24, WHITE, 10, 130)


            elif self.level == 5 and self.boss:
                self.draw_text(f"Boss HP: {self.boss.health}", 24, RED, 10, 50)

            else:  
                self.draw_text("Endless Mode", 24, WHITE, 10, 50)
                self.draw_text(f"Level: {self.level}", 24, WHITE, 10, 90)
                
        elif self.state == "PAUSE":
            self.draw_text_center("PAUSE", 60, WHITE, y_offset=-200)
            for rect, text in self.pause_buttons:
                pygame.draw.rect(self.screen, LIGHTGRAY, rect)
                self.draw_text(text, 40, BLACK, rect.x + 20, rect.y + 10)
        elif self.state == "LEVEL_COMPLETE":
            self.draw_text_center(f"LEVEL {self.level} COMPLETE!", 60, GREEN)
            self.draw_text_center("Press ENTER to continue", 36, WHITE, y_offset=100)
        elif self.state == "GAME_OVER":
            self.screen.fill(BLACK)
            self.draw_text_center("GAME OVER", 60, RED)
            self.draw_text_center("Press ENTER to return to MENU", 36, WHITE, y_offset=100)
        elif self.state == "VICTORY":
            self.draw_text_center("YOU WON!", 60, YELLOW)
            self.draw_text_center("Press ENTER to return to MENU", 36, WHITE, y_offset=100)
        pygame.display.flip()

    # -----------------------------------------------
    #  Утилиты вывода текста
    # -----------------------------------------------
    def draw_text(self, text, size, color, x, y):
        font = pygame.font.SysFont("fonts/PressStart2P-vaV7.ttf", size)
        txt_surface = font.render(text, True, color)
        self.screen.blit(txt_surface, (x, y))

    def draw_text_center(self, text, size, color, y_offset=0):
        font = pygame.font.SysFont("fonts/PressStart2P-vaV7.ttf", size)
        txt_surface = font.render(text, True, color)
        rect = txt_surface.get_rect()
        rect.centerx = WIDTH // 2
        rect.centery = HEIGHT // 2 + y_offset
        self.screen.blit(txt_surface, rect)


if __name__ == "__main__":
    Game().run()
