import pygame
import sys
import random
import time
import math
import os

# --- Helper function to find asset files ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # If not running in a bundle, use the path of the script file
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# Game Initialization
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.set_num_channels(32)

# --- Game Settings ---
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Dry The Clothes")
clock = pygame.time.Clock()
FPS = 60
font_small = pygame.font.Font(None, 24)
font_medium = pygame.font.Font(None, 32)
font_large = pygame.font.Font(None, 72)

# --- Colors ---
WHITE = (255, 255, 255); BLACK = (0, 0, 0); SKY_BLUE = (135, 206, 235); CLOUD_WHITE = (245, 245, 245)
GREEN = (50, 205, 50); ORANGE = (255, 165, 0); GREY = (128, 128, 128); BROWN = (139, 69, 19)
NEON_YELLOW = (255, 255, 0); NEON_GREEN = (57, 255, 20); DARK_GREEN = (0, 100, 0)
SILVER = (192, 192, 192); GOLD = (255, 215, 0); RED = (220, 20, 60)
INPUT_BOX_ACTIVE_COLOR = (200, 200, 255); INPUT_BOX_INACTIVE_COLOR = (230, 230, 230)
SHOP_BUILDING_COLOR = (100, 100, 150); ITEM_BG_COLOR = (210, 210, 230)
OUTLINE_GREEN = (0, 255, 0); OUTLINE_RED = (255, 0, 0); THUNDER_GREY = (70, 80, 90)
RAIN_GREY = (100, 110, 120); LIGHTNING_FLASH_COLOR = (230, 230, 255)
WINE_PURPLE = (110, 20, 90); OIL_STAIN_PARTICLE = (80, 80, 75); TOMATO_RED = (200, 40, 30)
TOMATO_GREEN_SPECKS = (10, 120, 30); CHOC_BROWN = (94, 57, 31); DIRT_GREY = (139, 125, 107)

# --- Game Configuration ---
STARTING_DRYCKLES = 10; WASH_TIME_SECONDS = 10; DRY_TIME_SECONDS = 5
SHOP_RESTOCK_MINUTES = 1; DOUBLE_CLICK_INTERVAL = 0.5
MUSIC_FADEOUT_MS = 2000; MUSIC_VOLUME = 0.6

# --- Sound Effects ---
def make_sound(freq, duration_ms, waveform="sine", attack_ms=1, decay_ms=None):
    if decay_ms is None: decay_ms = duration_ms
    sample_rate, num_channels = pygame.mixer.get_init()[0], pygame.mixer.get_init()[2]
    max_amp = 2 ** (abs(pygame.mixer.get_init()[1]) - 1) - 1
    num_samples = int(duration_ms / 1000 * sample_rate)
    sound_buffer = bytearray(num_samples * num_channels * 2)
    for i in range(num_samples):
        progress = i / sample_rate; time_ms = (i / sample_rate) * 1000
        if time_ms < attack_ms: amp = max_amp * (time_ms / attack_ms)
        elif time_ms > duration_ms - decay_ms: amp = max_amp * ((duration_ms - time_ms) / decay_ms)
        else: amp = max_amp
        if waveform == "sine": val = amp * math.sin(2 * math.pi * freq * progress)
        elif waveform == "square": val = amp if math.sin(2 * math.pi * freq * progress) > 0 else -amp
        elif waveform == "sawtooth": val = amp * (2 * (progress * freq - math.floor(0.5 + progress * freq)))
        elif waveform == "triangle": val = amp * (2 * abs(2 * (progress * freq - math.floor(progress * freq + 0.5))) - 1)
        else: val = amp * random.uniform(-1, 1) if waveform == "noise" else 0
        val = int(max(-32768, min(32767, val)))
        frame = val.to_bytes(2, byteorder='little', signed=True)
        if num_channels == 1:
            sound_buffer[i*2:i*2+2] = frame
        else:
            offset = i * num_channels * 2; sound_buffer[offset:offset+2] = frame; sound_buffer[offset+2:offset+4] = frame
    return pygame.mixer.Sound(buffer=sound_buffer)

def make_arpeggio(notes, note_duration_ms, waveform="sine"):
    final_buffer = bytearray()
    for freq in notes:
        sound = make_sound(freq, note_duration_ms, waveform, decay_ms=note_duration_ms-1)
        final_buffer += sound.get_raw()
    return pygame.mixer.Sound(buffer=final_buffer)

sounds = {
    'click': make_sound(900, 50, waveform="sine", decay_ms=50),
    'buy': make_arpeggio([523, 659, 784], 70, waveform="sine"),
    'success': make_arpeggio([659, 830, 987], 60, waveform="triangle"),
    'error': make_sound(110, 300, waveform="sawtooth"),
    'drying': make_sound(1200, 200, waveform="triangle", decay_ms=200),
    'rain_loop': pygame.mixer.Sound(resource_path(os.path.join('sounds', 'rain.wav'))),
    'sunny_ambience': pygame.mixer.Sound(resource_path(os.path.join('sounds', 'sunny.wav'))),
    'thunder_clap': pygame.mixer.Sound(resource_path(os.path.join('sounds', 'thunder.wav')))
}
def play_sound(name, loops=0):
    try: sounds[name].play(loops)
    except Exception as e: print(f"Could not play sound '{name}': {e}")


# --- Asset Definitions & Classes ---
def draw_washing_machine(surface, x, y, machine_type="rusty", is_active=False, progress=0, scale=1.0, outline_color=None):
    width, height, radius = int(80 * scale), int(100 * scale), int(25 * scale)
    base_color = {"rusty": GREY, "silver": SILVER, "gold": GOLD}[machine_type]
    shake_x, shake_y = (random.randint(-2, 2), random.randint(-2, 2)) if is_active else (0, 0)
    pygame.draw.rect(surface, base_color, (x + shake_x, y + shake_y, width, height), border_radius=int(10*scale))
    pygame.draw.circle(surface, (50,50,50), (x + width//2 + shake_x, y + int(40*scale) + shake_y), radius)
    pygame.draw.circle(surface, (100,100,100), (x + width//2 + shake_x, y + int(40*scale) + shake_y), radius-int(2*scale), int(3*scale))
    if is_active:
        for _ in range(3):
            bubble_x, bubble_y = x + random.randint(int(20*scale), int(60*scale)) + shake_x, y - random.randint(int(5*scale), int(20*scale)) + shake_y
            pygame.draw.circle(surface, (200, 220, 255, 150), (bubble_x, bubble_y), random.randint(int(3*scale), int(8*scale)))
        pygame.draw.rect(surface, (100, 100, 100), (x, y + height + 5, width, int(10*scale)))
        pygame.draw.rect(surface, GREEN, (x, y + height + 5, width * progress, int(10*scale)))
    if outline_color: pygame.draw.rect(surface, outline_color, (x, y, width, height), 4, border_radius=int(10*scale))

def draw_clothes(surface, x, y, clothes_info, background_color=None):
    stains = clothes_info.get('stains', [])
    color = WHITE if stains or clothes_info['type'] == 'clean' else (230, 230, 230)
    shirt_rect = pygame.Rect(x, y, 30, 40)
    bg_color_map = {"sunny": SKY_BLUE, "thunderstorm": THUNDER_GREY, "chocolate_rain": RAIN_GREY}
    neck_hole_bg = background_color or bg_color_map.get(game.current_weather, SKY_BLUE)
    pygame.draw.rect(surface, color, shirt_rect)
    pygame.draw.rect(surface, color, (shirt_rect.left - 8, shirt_rect.top + 5, 8, 15))
    pygame.draw.rect(surface, color, (shirt_rect.right, shirt_rect.top + 5, 8, 15))
    pygame.draw.circle(surface, neck_hole_bg, (shirt_rect.centerx, shirt_rect.top + 7), 5)
    if clothes_info.get('stain_data'):
        for stain in clothes_info['stain_data']:
            stain_x, stain_y = x + stain['pos'][0], y + stain['pos'][1]
            if stain['shape'] == 'circle': pygame.draw.circle(surface, stain['color'], (stain_x, stain_y), stain['radius'])
            elif stain['shape'] == 'rect': pygame.draw.rect(surface, stain['color'], (stain_x, stain_y, stain['size'][0], stain['size'][1]))
    if stains:
        stain_particle_map = {
            "wine_stained": {'c': WINE_PURPLE, 's': 'c'}, "oil_stained": {'c': OIL_STAIN_PARTICLE, 's': 'r'},
            "tomato_stained": {'c': TOMATO_RED, 's': 'c'}, "dirt_stain": {'c': DIRT_GREY, 's': 'c'},
            "choc_stain": {'c': CHOC_BROWN, 's': 'c'}
        }
        for stain_type in stains:
            if stain_type in stain_particle_map:
                p_info = stain_particle_map[stain_type]
                for _ in range(2): 
                    angle, radius = random.uniform(0, 2 * math.pi), random.uniform(20, 25)
                    p_x, p_y = shirt_rect.centerx + radius * math.cos(angle), shirt_rect.centery + radius * math.sin(angle)
                    if p_info['s'] == 'c': pygame.draw.circle(surface, p_info['c'], (p_x, p_y), 2)
                    elif p_info['s'] == 'r': pygame.draw.rect(surface, p_info['c'], (p_x-1, p_y-1, 3, 3))
    if clothes_info.get('super'):
        super_color = SILVER if clothes_info.get('super_type') == 'silver' else GOLD
        for _ in range(4): pygame.draw.rect(surface, super_color, (x + random.randint(-5, 35), y + random.randint(-5, 45), 3, 8))

def draw_trash_can(surface, rect):
    center, radius = rect.center, rect.width // 2
    pygame.draw.circle(surface, GREY, center, radius); pygame.draw.circle(surface, BLACK, center, radius, 3)
    lid_rect = pygame.Rect(rect.left - 5, rect.top, rect.width + 10, 10)
    pygame.draw.rect(surface, GREY, lid_rect, border_radius=3); pygame.draw.rect(surface, BLACK, lid_rect, 2, border_radius=3)

class Button:
    def __init__(self, x, y, width, height, text, color, text_color=BLACK, font=font_medium):
        self.rect, self.text, self.color = pygame.Rect(x, y, width, height), text, color
        self.text_color, self.font, self.is_hovered = text_color, font, False
    def draw(self, surface):
        draw_color = tuple(min(c + 30, 255) for c in self.color) if self.is_hovered else self.color
        pygame.draw.rect(surface, draw_color, self.rect, border_radius=10)
        pygame.draw.rect(surface, tuple(max(c - 40, 0) for c in self.color), self.rect, 3, border_radius=10)
        text_surf = self.font.render(self.text, True, self.text_color)
        surface.blit(text_surf, text_surf.get_rect(center=self.rect.center))
    def check_hover(self, mouse_pos): self.is_hovered = self.rect.collidepoint(mouse_pos)
    def is_clicked(self, event):
        clicked = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered
        if clicked: play_sound('click')
        return clicked

class Cloud:
    def __init__(self):
        self.x, self.y = random.randint(-200, SCREEN_WIDTH), random.randint(20, 200)
        self.speed, self.size = random.uniform(0.5, 1.5), random.randint(80, 200)
    def update(self):
        self.x += self.speed
        if self.x > SCREEN_WIDTH + 50: self.x, self.y = -200, random.randint(20, 200)
    def draw(self, surface):
        pygame.draw.ellipse(surface, CLOUD_WHITE, (self.x, self.y, self.size, self.size / 2))
        pygame.draw.ellipse(surface, CLOUD_WHITE, (self.x + self.size/4, self.y - self.size/4, self.size, self.size / 2))

class Player:
    def __init__(self):
        self.dryckles = STARTING_DRYCKLES
        self.inventory = {"unwashed": [], "wet": [], "drying": [], "dry": []}
        self.gear = {"washing_machines": [], "clothes_lines": []}
        self.plot = None

class Game:
    def __init__(self):
        self.state = "menu"
        self.clouds = [Cloud() for _ in range(15)]
        self.start_button = Button(SCREEN_WIDTH/2-100, SCREEN_HEIGHT/2-50, 200, 60, "Start", GREEN, WHITE)
        self.tutorial_button = Button(SCREEN_WIDTH/2-100, SCREEN_HEIGHT/2+30, 200, 60, "Tutorial", ORANGE, WHITE)
        self.back_button = Button(20, SCREEN_HEIGHT-80, 150, 60, "Back to Menu", GREY, WHITE)
        self.ingame_back_button = Button(20, SCREEN_HEIGHT - 60, 150, 40, "Main Menu", GREY, WHITE, font=font_small)
        self.player, self.plot, self.clothing_store, self.gear_shop = None, None, None, None
        self.delete_bin_rect, self.dragged_item = None, None
        self.autosell_duration_str, self.autosell_input_active = "5", False
        self.autosell_input_rect = pygame.Rect(SCREEN_WIDTH - 300, 20, 70, 40)
        self.start_autosell_button = Button(SCREEN_WIDTH - 220, 20, 180, 40, "Start Autosell", RED, WHITE, font=font_small)
        self.autosell_active, self.autosell_start_time, self.autosell_duration = False, 0, 5
        self.banner_text, self.banner_start_time, self.BANNER_DURATION = None, 0, 2
        self.active_modal, self.current_weather, self.next_weather_change_time = None, "sunny", 0
        self.next_lightning_time, self.lightning_active, self.lightning_end_time = 0, False, 0
        self.LIGHTNING_DURATION, self.lightning_bolt_points = 0.2, []
        self.hovered_dry_item_index, self.weather_particles, self.stain_animations = None, [], []
        self.weather_ui_rect, self.is_hovering_weather = None, False
        self.weather_tooltips = {"sunny": "Perfect drying weather!", "thunderstorm": "Drying paused. 50% chance of dirt stains!", "chocolate_rain": "A delicious mess! 40% chance of chocolate stains."}
        self.rain_channel, self.sunny_channel = pygame.mixer.Channel(0), pygame.mixer.Channel(1)

    def setup_game(self):
        self.player = Player()
        self.plot = pygame.Rect(10, SCREEN_HEIGHT - 400, SCREEN_WIDTH - 20, 390)
        self.player.plot = self.plot
        self.delete_bin_rect = pygame.Rect(self.plot.right - 80, self.plot.bottom - 80, 60, 70)
        self.player.gear["washing_machines"].clear(); self.player.gear["clothes_lines"].clear()
        self.player.gear["washing_machines"].append(WashingMachine("rusty", (self.plot.centerx - 150, self.plot.centery)))
        self.player.gear["clothes_lines"].append(ClothesLine("wooden", (self.plot.centerx + 50, self.plot.centery)))
        self.clothing_store, self.gear_shop = Shop("clothing"), Shop("gear")
        self.autosell_active, self.autosell_duration_str = False, "5"
        self.dragged_item, self.banner_text, self.current_weather = None, None, "sunny"
        self.set_next_weather_change()
        self.lightning_active, self.lightning_bolt_points, self.weather_particles, self.stain_animations = False, [], [], []
        pygame.mixer.stop()
        self.sunny_channel.play(sounds['sunny_ambience'], loops=-1)

    def run(self):
        while True:
            self.handle_events(); self.update(); self.draw(); pygame.display.flip(); clock.tick(FPS)

    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.dragged_item:
                    item = self.dragged_item; item.is_dragging, item.outline_color, self.dragged_item = False, None, None
                    if self.delete_bin_rect.colliderect(item.rect):
                        play_sound('error')
                        if isinstance(item, WashingMachine): self.player.gear["washing_machines"].remove(item)
                        elif isinstance(item, ClothesLine): self.player.gear["clothes_lines"].remove(item)
                    elif not self.is_placement_valid(item):
                        item.rect.topleft = item.original_pos; self.banner_text, self.banner_start_time = "Object can't be moved here.", time.time(); play_sound('error')
                    continue 
            if self.state == "menu":
                self.start_button.check_hover(mouse_pos); self.tutorial_button.check_hover(mouse_pos)
                if self.start_button.is_clicked(event): self.setup_game(); self.state = "playing"
                if self.tutorial_button.is_clicked(event): self.state = "tutorial"
            elif self.state == "tutorial":
                self.back_button.check_hover(mouse_pos)
                if self.back_button.is_clicked(event): self.state = "menu"
            elif self.state == "playing":
                if self.active_modal and event.type == pygame.MOUSEWHEEL:
                    shop = self.gear_shop if self.active_modal == 'gear_shop' else self.clothing_store
                    shop.scroll_y -= event.y * 30; shop.clamp_scroll(); continue
                if self.dragged_item:
                    if event.type == pygame.MOUSEMOTION:
                        self.dragged_item.rect.center = mouse_pos; self.dragged_item.outline_color = OUTLINE_GREEN if self.is_placement_valid(self.dragged_item) else OUTLINE_RED
                    continue
                if event.type == pygame.KEYDOWN and self.autosell_input_active:
                    if event.key == pygame.K_BACKSPACE: self.autosell_duration_str = self.autosell_duration_str[:-1]
                    elif event.unicode.isdigit(): self.autosell_duration_str += event.unicode
                    continue
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.active_modal:
                        if not self.get_modal_rect().collidepoint(mouse_pos): self.active_modal = None
                        elif self.active_modal == "clothing_store": self.clothing_store.handle_click(event)
                        elif self.active_modal == "gear_shop": self.gear_shop.handle_click(event)
                        continue 
                    self.autosell_input_active = self.autosell_input_rect.collidepoint(mouse_pos)
                    if self.start_autosell_button.is_clicked(event):
                        self.autosell_active = not self.autosell_active
                        if self.autosell_active:
                            try: self.autosell_duration = int(self.autosell_duration_str) if int(self.autosell_duration_str) > 0 else 5
                            except ValueError: self.autosell_duration = 5
                            self.autosell_start_time = time.time()
                    elif self.ingame_back_button.is_clicked(event): self.state, self.active_modal = "menu", None; pygame.mixer.stop()
                    elif self.clothing_store.rect.collidepoint(mouse_pos): self.active_modal = "clothing_store"; play_sound('click')
                    elif self.gear_shop.rect.collidepoint(mouse_pos): self.active_modal = "gear_shop"; play_sound('click')
                    else:
                        for item in self.player.gear["washing_machines"] + self.player.gear["clothes_lines"]:
                            if item.rect.collidepoint(mouse_pos):
                                current_time = time.time()
                                if current_time - item.last_click_time < DOUBLE_CLICK_INTERVAL and not getattr(item, 'is_active', False):
                                    item.is_dragging, self.dragged_item = True, item; item.original_pos, item.outline_color = item.rect.topleft, OUTLINE_GREEN
                                    item.last_click_time = 0 
                                else: item.on_click(self.player); item.last_click_time = current_time
                                self.autosell_input_active = False; break

    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        if self.banner_text and time.time() - self.banner_start_time > self.BANNER_DURATION: self.banner_text = None
        if self.state == "playing":
            self.update_weather()
            for cloud in self.clouds: cloud.update()
            for wm in self.player.gear["washing_machines"]: wm.update(self.player)
            for cl in self.player.gear["clothes_lines"]: cl.update(self.player, self.current_weather)
            self.clothing_store.update(); self.gear_shop.update(); self.update_autosell()
            self.start_autosell_button.check_hover(mouse_pos); self.ingame_back_button.check_hover(mouse_pos)
            if self.active_modal:
                shop = self.gear_shop if self.active_modal == 'gear_shop' else self.clothing_store; shop.check_button_hovers(mouse_pos)
            self.hovered_dry_item_index = None
            for i in range(min(len(self.player.inventory['dry']), 10)):
                item_rect = pygame.Rect(700 + 8 + i * 20, 40, 30, 40)
                if item_rect.collidepoint(mouse_pos): self.hovered_dry_item_index = i; break
            self.is_hovering_weather = bool(self.weather_ui_rect and self.weather_ui_rect.collidepoint(mouse_pos))
        else: 
            for cloud in self.clouds: cloud.update()

    def update_weather(self):
        if time.time() >= self.next_weather_change_time:
            weather_cycle = ["sunny", "thunderstorm", "chocolate_rain"]; current_index = weather_cycle.index(self.current_weather)
            self.current_weather = weather_cycle[(current_index + 1) % len(weather_cycle)]
            self.sunny_channel.stop(); self.rain_channel.stop()
            if self.current_weather == "sunny": self.sunny_channel.play(sounds['sunny_ambience'], loops=-1)
            else: self.rain_channel.play(sounds['rain_loop'], loops=-1)
            if self.current_weather == "thunderstorm": self.set_next_lightning_strike()
            self.set_next_weather_change()
        if self.current_weather in ["thunderstorm", "chocolate_rain"]:
            self.weather_particles = [p for p in self.weather_particles if p[0].y < SCREEN_HEIGHT]
            for _ in range(3):
                color = CHOC_BROWN if self.current_weather == "chocolate_rain" else (180, 190, 200)
                self.weather_particles.append([pygame.Vector2(random.randint(0, SCREEN_WIDTH), -10), color])
        for p in self.weather_particles: p[0].y += 8
        if self.current_weather == "thunderstorm" and time.time() >= self.next_lightning_time:
            self.lightning_active, self.lightning_end_time = True, time.time() + self.LIGHTNING_DURATION
            play_sound('thunder_clap'); self.generate_lightning_bolt(); self.set_next_lightning_strike()
        if self.lightning_active and time.time() >= self.lightning_end_time: self.lightning_active, self.lightning_bolt_points = False, []
        self.stain_animations = [anim for anim in self.stain_animations if anim['timer'] > 0]
        for anim in self.stain_animations:
            anim['timer'] -= 1
            for p in anim['particles']:
                p[0] += p[1]; p[2] -= 0.1
                if p[2] <= 0: anim['particles'].remove(p)

    def set_next_weather_change(self): self.next_weather_change_time = time.time() + random.randint(60, 90)
    def set_next_lightning_strike(self): self.next_lightning_time = time.time() + random.randint(8, 20)

    def generate_lightning_bolt(self):
        self.lightning_bolt_points = []
        start_pos = (random.randint(50, SCREEN_WIDTH - 50), 0); end_pos = (start_pos[0] + random.randint(-80, 80), self.plot.top)
        self.lightning_bolt_points.append(self._create_bolt_segment(start_pos, end_pos, 15, 6))
        for i, point in enumerate(self.lightning_bolt_points[0]['points']):
            if 2 < i < len(self.lightning_bolt_points[0]['points']) - 3 and random.random() < 0.2:
                branch_end = (point[0] + random.randint(-100, 100), point[1] + random.randint(100, 200))
                self.lightning_bolt_points.append(self._create_bolt_segment(point, branch_end, 8, 3))

    def _create_bolt_segment(self, start_pos, end_pos, num_segments, max_offset, width=None):
        points = [start_pos]
        for i in range(1, num_segments):
            t = i / num_segments
            lx, ly = start_pos[0] * (1 - t) + end_pos[0] * t, start_pos[1] * (1 - t) + end_pos[1] * t
            points.append((lx + random.uniform(-max_offset, max_offset), ly))
        points.append(end_pos)
        return {'points': points, 'width': width or random.randint(2, 5)}

    def update_autosell(self):
        if not self.autosell_active or not self.player: return
        if time.time() - self.autosell_start_time >= self.autosell_duration:
            total_value = sum(c['value'] for c in self.player.inventory['dry'])
            if total_value > 0: self.player.dryckles += total_value; self.player.inventory['dry'] = []; play_sound('buy')
            self.autosell_start_time = time.time()

    def draw(self):
        bg_color = SKY_BLUE
        if self.state == "playing":
            if self.current_weather == "thunderstorm": bg_color = THUNDER_GREY
            elif self.current_weather == "chocolate_rain": bg_color = RAIN_GREY
        screen.fill(bg_color)
        for p in self.weather_particles: pygame.draw.line(screen, p[1], p[0], p[0] + pygame.Vector2(0, 5), 2)
        if self.state == "playing" and self.lightning_active:
            screen.fill(LIGHTNING_FLASH_COLOR)
            for bolt in self.lightning_bolt_points: pygame.draw.lines(screen, NEON_YELLOW, False, bolt['points'], bolt['width'])
        for cloud in self.clouds: cloud.draw(screen)
        if self.state == "menu":
            title_surf = font_large.render("Dry The Clothes", True, BLACK); screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/3)))
            self.start_button.draw(screen); self.tutorial_button.draw(screen)
        elif self.state == "tutorial": self.draw_tutorial(); self.back_button.draw(screen)
        elif self.state == "playing":
            self.draw_game_world(); self.draw_ui()
            if self.active_modal:
                shop = self.gear_shop if self.active_modal == 'gear_shop' else self.clothing_store; shop.draw_modal(screen)
        if self.is_hovering_weather: self.draw_weather_tooltip()
        if self.banner_text: self.draw_banner()
        pygame.display.flip()
        
    def draw_weather_tooltip(self):
        text_surf = font_small.render(self.weather_tooltips.get(self.current_weather, ""), True, BLACK)
        bg_rect = text_surf.get_rect(topleft=(pygame.mouse.get_pos()[0] + 15, pygame.mouse.get_pos()[1] + 15)); bg_rect.inflate_ip(10, 10)
        pygame.draw.rect(screen, WHITE, bg_rect, border_radius=5); pygame.draw.rect(screen, BLACK, bg_rect, 1, border_radius=5)
        screen.blit(text_surf, (bg_rect.x + 5, bg_rect.y + 5))

    def draw_banner(self):
        banner_surf = font_medium.render(self.banner_text, True, WHITE)
        bg_rect = banner_surf.get_rect(center=(SCREEN_WIDTH/2, 120)); bg_rect.inflate_ip(40, 20)
        s = pygame.Surface(bg_rect.size, pygame.SRCALPHA); s.fill((220, 20, 60, 200))
        pygame.draw.rect(s, BLACK, s.get_rect(), 3, border_radius=10)
        screen.blit(s, bg_rect.topleft); screen.blit(banner_surf, banner_surf.get_rect(center=bg_rect.center))

    def is_placement_valid(self, item_to_check):
        if not self.plot.contains(item_to_check.rect): return False
        for other_item in self.player.gear["washing_machines"] + self.player.gear["clothes_lines"]:
            if other_item is not item_to_check and item_to_check.rect.colliderect(other_item.rect): return False
        return True

    def draw_tutorial(self):
        lines = ["How to Play: Dry The Clothes", "", "1. Goal: Earn Dryckles by washing and drying clothes.", "2. Weather: Watch the sky! Clothes only dry when it's sunny.", "3. During a thunderstorm, drying pauses and clothes may get dirty.", "4. During Chocolate Rain, clothes can get valuable chocolate stains!", "5. Newly stained clothes must be re-washed, but are worth more money!", "6. Buy gear from the 'Gear Shop' and clothes from the 'Clothing Store'."]
        for i, line in enumerate(lines):
            font = font_medium if i == 0 else font_small; text_surf = font.render(line, True, BLACK)
            screen.blit(text_surf, text_surf.get_rect(midtop=(SCREEN_WIDTH/2, 100 + i * 40)))

    def draw_game_world(self):
        pygame.draw.rect(screen, (124, 252, 0), (0, SCREEN_HEIGHT - 410, SCREEN_WIDTH, 410))
        pygame.draw.rect(screen, (188, 143, 143), self.plot, 5)
        for wm in self.player.gear["washing_machines"]: wm.draw(screen)
        for cl in self.player.gear["clothes_lines"]: cl.draw(screen)
        for anim in self.stain_animations:
            for p in anim['particles']: pygame.draw.circle(screen, anim['color'], p[0], int(p[2]))
        self.clothing_store.draw_world_object(screen); self.gear_shop.draw_world_object(screen)
        self.ingame_back_button.draw(screen)
        if self.delete_bin_rect: draw_trash_can(screen, self.delete_bin_rect)

    def draw_ui(self):
        s = pygame.Surface((SCREEN_WIDTH, 80), pygame.SRCALPHA); s.fill((0,0,0,150)); screen.blit(s, (0,0))
        pygame.draw.rect(screen, WHITE, (0, 0, SCREEN_WIDTH, 80), 3)
        screen.blit(font_medium.render(f"Dryckles: {self.player.dryckles}", True, NEON_YELLOW), (20, 25))
        weather_text_map = { "sunny": "Sunny", "thunderstorm": "Thunderstorm", "chocolate_rain": "Choc. Rain" }
        weather_text_surf = font_medium.render(f"Weather: {weather_text_map.get(self.current_weather, 'Unknown')}", True, WHITE)
        self.weather_ui_rect = screen.blit(weather_text_surf, (20, 50))
        inv_x_positions = {"unwashed": 300, "wet": 500, "dry": 700}
        for inv_type, start_x in inv_x_positions.items():
            count = len(self.player.inventory[inv_type])
            screen.blit(font_small.render(f"{inv_type.capitalize()}: {count}", True, WHITE), (start_x, 15))
            for i in range(min(count, 10)): draw_clothes(screen, start_x + 8 + i * 20, 40, self.player.inventory[inv_type][i])
        if self.hovered_dry_item_index is not None and self.hovered_dry_item_index < len(self.player.inventory['dry']):
            item_info = self.player.inventory['dry'][self.hovered_dry_item_index]
            if item_info.get('cleaned_stains'):
                stain_colors = { "wine": WINE_PURPLE, "oil": OIL_STAIN_PARTICLE, "tomato": TOMATO_RED, "dirt": DIRT_GREY, "choc": CHOC_BROWN }
                base_x, label_y = inv_x_positions['dry'] + 8 + self.hovered_dry_item_index * 20, 85
                clean_surf = font_small.render("Cleaned: ", True, BLACK); parts, total_width = [], clean_surf.get_width()
                for i, stain in enumerate(item_info['cleaned_stains']):
                    stain_name = stain.split('_')[0].title()
                    parts.append({"text": stain_name, "color": stain_colors.get(stain_name.lower(), BLACK)})
                    total_width += font_small.render(stain_name, True, BLACK).get_width()
                    if i < len(item_info['cleaned_stains']) - 1: parts.append({"text": " + ", "color": BLACK}); total_width += font_small.render(" + ", True, BLACK).get_width()
                bg_rect = pygame.Rect(base_x - 5, label_y - 2, total_width + 10, clean_surf.get_height() + 4)
                pygame.draw.rect(screen, WHITE, bg_rect, border_radius=5); pygame.draw.rect(screen, BLACK, bg_rect, 1, border_radius=5)
                screen.blit(clean_surf, (base_x, label_y))
                current_x = base_x + clean_surf.get_width()
                for part in parts:
                    text_surf = font_small.render(part['text'], True, part['color']); screen.blit(text_surf, (current_x, label_y)); current_x += text_surf.get_width()
        self.start_autosell_button.text = "Stop Autosell" if self.autosell_active else "Start Autosell"
        self.start_autosell_button.color = ORANGE if self.autosell_active else RED; self.start_autosell_button.draw(screen)
        input_box_color = INPUT_BOX_ACTIVE_COLOR if self.autosell_input_active else INPUT_BOX_INACTIVE_COLOR
        pygame.draw.rect(screen, input_box_color, self.autosell_input_rect, border_radius=8); pygame.draw.rect(screen, BLACK, self.autosell_input_rect, 2, border_radius=8)
        screen.blit(font_medium.render(self.autosell_duration_str, True, BLACK), (self.autosell_input_rect.x + 5, self.autosell_input_rect.y + 5))
        if self.autosell_active:
            remaining_time = self.autosell_duration - (time.time() - self.autosell_start_time)
            screen.blit(font_small.render(f"Selling in: {max(0, remaining_time):.1f}s", True, WHITE), (self.start_autosell_button.rect.left, self.start_autosell_button.rect.bottom + 5))
    
    def get_modal_rect(self): return pygame.Rect(SCREEN_WIDTH/2 - 300, SCREEN_HEIGHT/2 - 200, 600, 400)

class Shop:
    ITEM_HEIGHT = 100
    def __init__(self, shop_type):
        self.type, self.stock, self.restock_timer, self.buy_buttons, self.scroll_y, self.preview_stain_data = shop_type, {}, 0, [], 0, {}
        if self.type == "clothing":
            self.name, self.rect = "Clothing Store", pygame.Rect(SCREEN_WIDTH/2 - 200, SCREEN_HEIGHT - 410 - 100, 100, 70)
            self.definitions = { "normal": {"cost": 2, "value": 3}, "wine_stained": {"cost": 5, "value": 8}, "oil_stained": {"cost": 7, "value": 11}, "tomato_stained": {"cost": 10, "value": 16}}
        else:
            self.name, self.rect = "Gear Shop", pygame.Rect(SCREEN_WIDTH/2 + 100, SCREEN_HEIGHT - 410 - 100, 100, 70)
            self.definitions = { "silver_wm": {"cost": 50, "type": "washing_machine"}, "gold_wm": {"cost": 150, "type": "washing_machine"}, "silver_cl": {"cost": 40, "type": "clothes_line"}, "gold_cl": {"cost": 120, "type": "clothes_line"}}
        self.restock()
    def generate_stain_data(self, stain_types):
        stain_data, x_range, y_range = [], (5, 25), (10, 35)
        defs = { "wine_stained": [{'shape': 'circle', 'color': WINE_PURPLE, 'radius': random.randint(3,7)} for _ in range(3)], "oil_stained": [{'shape': 'circle', 'color': OIL_STAIN_PARTICLE, 'radius': random.randint(2,5)} for _ in range(2)] + [{'shape': 'rect', 'color': OIL_STAIN_PARTICLE, 'size': (2, random.randint(5,10))} for _ in range(2)], "tomato_stained": [{'shape': 'circle', 'color': TOMATO_RED, 'radius': random.randint(4,8)} for _ in range(3)] + [{'shape': 'circle', 'color': TOMATO_GREEN_SPECKS, 'radius': 1} for _ in range(4)], "dirt_stain": [{'shape': 'circle', 'color': DIRT_GREY, 'radius': random.randint(2,4)} for _ in range(5)], "choc_stain": [{'shape': 'circle', 'color': CHOC_BROWN, 'radius': random.randint(3,6)} for _ in range(3)] + [{'shape': 'rect', 'color': CHOC_BROWN, 'size':(2, random.randint(4,8))} for _ in range(2)]}
        for stain_type in stain_types:
            if stain_type in defs:
                for template in defs[stain_type]:
                    stain = template.copy(); stain['pos'] = (random.randint(*x_range), random.randint(*y_range)); stain_data.append(stain)
        return stain_data
    def clamp_scroll(self):
        modal_height = game.get_modal_rect().height - 110; max_scroll = max(0, len(self.stock) * self.ITEM_HEIGHT - modal_height)
        self.scroll_y = max(0, min(self.scroll_y, max_scroll))
    def restock(self):
        self.stock, self.restock_timer = {}, 0
        for item, data in self.definitions.items():
            if random.random() < data.get("restock_chance", 0.5): self.stock[item] = random.randint(*data.get("restock_qty", (1,1)))
        self.create_buttons()
        self.preview_stain_data.clear()
        if self.type == "clothing":
            for item_name in self.stock:
                if "stained" in item_name: self.preview_stain_data[item_name] = self.generate_stain_data([item_name])
    def update(self):
        self.restock_timer += 1/FPS
        if self.restock_timer >= SHOP_RESTOCK_MINUTES * 60: self.restock()
    def create_buttons(self): self.buy_buttons = [Button(0, 0, 100, 40, "Buy", GREEN) for _ in self.stock]
    def buy_item(self, player, item_name):
        if item_name in self.stock and self.stock[item_name] > 0:
            cost = self.definitions[item_name]['cost']
            if player.dryckles >= cost:
                play_sound('buy'); player.dryckles -= cost; self.stock[item_name] -= 1
                if self.type == "clothing":
                    is_stained = "stained" in item_name
                    new_item = {"type": "stained" if is_stained else "normal", "value": self.definitions[item_name]['value'], "super": False, "stains": [item_name] if is_stained else []}
                    if is_stained: new_item['stain_data'] = self.generate_stain_data(new_item['stains'])
                    player.inventory["unwashed"].append(new_item)
                else:
                    gear_type, new_gear_type, spawn_pos = self.definitions[item_name]['type'], item_name.split('_')[0], (player.plot.left + 20, player.plot.top + 20)
                    if gear_type == "washing_machine": player.gear['washing_machines'].append(WashingMachine(new_gear_type, spawn_pos))
                    else: player.gear['clothes_lines'].append(ClothesLine(new_gear_type, spawn_pos))
                if self.stock[item_name] <= 0: del self.stock[item_name]; self.create_buttons()
            else: play_sound('error')
    def get_button_abs_rect(self, index):
        modal_rect, btn, y_pos_relative = game.get_modal_rect(), self.buy_buttons[index], 20 + index * self.ITEM_HEIGHT - self.scroll_y
        abs_btn_rect = btn.rect.copy(); abs_btn_rect.centerx, abs_btn_rect.centery = modal_rect.left + (modal_rect.width - 40) - 70, modal_rect.top + 60 + y_pos_relative + (self.ITEM_HEIGHT - 10) / 2
        return abs_btn_rect
    def check_button_hovers(self, mouse_pos):
        content_area = game.get_modal_rect().inflate(-20, -110)
        for i, btn in enumerate(self.buy_buttons):
            abs_btn_rect = self.get_button_abs_rect(i); btn.is_hovered = content_area.colliderect(abs_btn_rect) and abs_btn_rect.collidepoint(mouse_pos)
    def handle_click(self, event):
        if not (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1): return
        for i, item_name in enumerate(list(self.stock.keys())):
            if self.get_button_abs_rect(i).collidepoint(event.pos): self.buy_item(game.player, item_name); break
    def draw_world_object(self, surface):
        pygame.draw.rect(surface, SHOP_BUILDING_COLOR, self.rect, border_radius=8)
        if self.type == "clothing":
            shirt_rect = pygame.Rect(0, 0, 30, 40); shirt_rect.center = self.rect.center
            draw_clothes(surface, shirt_rect.x, shirt_rect.y, {"type": "normal"}, background_color=SHOP_BUILDING_COLOR)
        else:
            cx, cy, radius = self.rect.centerx, self.rect.centery, 18
            pygame.draw.circle(surface, SILVER, (cx, cy), radius)
            for i in range(8):
                angle = i * (math.pi / 4); x1, y1, x2, y2 = cx+(radius-5)*math.cos(angle), cy+(radius-5)*math.sin(angle), cx+(radius+5)*math.cos(angle), cy+(radius+5)*math.sin(angle)
                pygame.draw.line(surface, SILVER, (x1, y1), (x2, y2), 5)
            pygame.draw.circle(surface, SHOP_BUILDING_COLOR, (cx, cy), radius // 2)
        name_text = font_small.render(self.name.split(" ")[0], True, WHITE)
        surface.blit(name_text, (self.rect.centerx - name_text.get_width()//2, self.rect.bottom + 2))
    def draw_modal(self, surface):
        modal_rect, content_area = game.get_modal_rect(), game.get_modal_rect().inflate(-20, -110); content_area.top = modal_rect.top + 60
        pygame.draw.rect(surface, (200, 200, 220), modal_rect, border_radius=15)
        content_surface = surface.subsurface(content_area)
        title = font_medium.render(self.name, True, BLACK); surface.blit(title, (modal_rect.centerx - title.get_width()//2, modal_rect.top + 20))
        if not self.stock:
            empty_text = font_small.render("Sold out! Check back soon.", True, BLACK); content_surface.blit(empty_text, (content_area.width/2 - empty_text.get_width()/2, content_area.height/2 - empty_text.get_height()/2))
        else:
            for i, (item_name, qty) in enumerate(self.stock.items()):
                y_pos = 20 + i * self.ITEM_HEIGHT - self.scroll_y
                if y_pos + self.ITEM_HEIGHT > 0 and y_pos < content_area.height:
                    item_rect = pygame.Rect(20, y_pos, content_area.width - 40, self.ITEM_HEIGHT - 10)
                    pygame.draw.rect(content_surface, ITEM_BG_COLOR, item_rect, border_radius=10); pygame.draw.rect(content_surface, BLACK, item_rect, 2, border_radius=10)
                    pic_frame_rect = pygame.Rect(item_rect.x + 10, item_rect.y + 10, 150, item_rect.height - 20)
                    cost = self.definitions[item_name]['cost']
                    if self.type == "clothing":
                        preview_item = {"type": "stained", "stains": [item_name]} if "stained" in item_name else {"type": "normal", "stains": []}
                        if "stained" in item_name: preview_item['stain_data'] = self.preview_stain_data.get(item_name)
                        draw_clothes(content_surface, pic_frame_rect.centerx - 15, pic_frame_rect.centery - 20, preview_item, background_color=ITEM_BG_COLOR)
                        text_x = pic_frame_rect.right + 20
                        content_surface.blit(font_medium.render(f"{item_name.replace('_', ' ').title()}", True, BLACK), (text_x, item_rect.y + 15))
                        content_surface.blit(font_small.render(f"In Stock: {qty}", True, BLACK), (text_x, item_rect.y + 45))
                        content_surface.blit(font_small.render(f"Cost: {cost}", True, BLACK), (text_x, item_rect.y + 65))
                    else:
                        gear_name = item_name.split("_")[0]
                        if self.definitions[item_name]["type"] == "washing_machine": draw_washing_machine(content_surface, pic_frame_rect.centerx - 30, pic_frame_rect.centery - 37, gear_name, scale=0.75)
                        else: preview_line = ClothesLine(gear_name, (0, 0)); preview_line.rect.center = pic_frame_rect.center; preview_line.draw(content_surface, scale=0.6, preview_mode=True)
                        text_x = pic_frame_rect.right + 20
                        content_surface.blit(font_medium.render(f"{item_name.replace('_', ' ').title()}", True, BLACK), (text_x, item_rect.y + 15))
                        content_surface.blit(font_small.render(f"Cost: {cost}", True, BLACK), (text_x, item_rect.y + 45))
                    self.buy_buttons[i].rect = self.get_button_abs_rect(i); self.buy_buttons[i].draw(surface)
            total_content_height = len(self.stock) * self.ITEM_HEIGHT
            if total_content_height > content_area.height:
                scrollbar_track_rect = pygame.Rect(modal_rect.right - 25, content_area.top, 15, content_area.height); pygame.draw.rect(surface, (50,50,50), scrollbar_track_rect, border_radius=7)
                handle_height = max(20, content_area.height * (content_area.height / total_content_height)); max_scroll = total_content_height - content_area.height
                scroll_percentage = self.scroll_y / max_scroll if max_scroll > 0 else 0; handle_y = scrollbar_track_rect.y + scroll_percentage * (scrollbar_track_rect.height - handle_height)
                scrollbar_handle_rect = pygame.Rect(scrollbar_track_rect.x, handle_y, 15, handle_height); pygame.draw.rect(surface, (150,150,150), scrollbar_handle_rect, border_radius=7)
        pygame.draw.rect(surface, BLACK, modal_rect, 3, border_radius=15)
        remaining_time = (SHOP_RESTOCK_MINUTES * 60) - self.restock_timer
        timer_text_surf = font_small.render(f"Restocks in: {max(0, int(remaining_time))}s", True, BLACK)
        surface.blit(timer_text_surf, timer_text_surf.get_rect(centerx=modal_rect.centerx, bottom=modal_rect.bottom - 20))

class Draggable:
    def __init__(self, pos, size):
        self.rect = pygame.Rect(pos, size)
        self.is_dragging, self.last_click_time = False, 0
        self.outline_color, self.original_pos = None, None

class WashingMachine(Draggable):
    def __init__(self, machine_type, pos):
        super().__init__(pos, (80, 100))
        self.type, self.is_active, self.wash_start_time, self.washing_items = machine_type, False, 0, []
        attrs = {"rusty": {"capacity": 5, "super_chance": 0}, "silver": {"capacity": 7, "super_chance": 0.3, "super_type": "silver", "multiplier": 2}, "gold": {"capacity": 10, "super_chance": 0.2, "super_type": "gold", "multiplier": 3}}
        self.capacity, self.super_chance = attrs[self.type]["capacity"], attrs[self.type]["super_chance"]
        self.super_type, self.multiplier = attrs[self.type].get("super_type"), attrs[self.type].get("multiplier", 1)
    def on_click(self, player):
        if self.is_active or self.is_dragging: return
        if not self.washing_items and player.inventory["unwashed"]:
            num_to_load = min(self.capacity, len(player.inventory["unwashed"]))
            self.washing_items, player.inventory["unwashed"] = player.inventory["unwashed"][:num_to_load], player.inventory["unwashed"][num_to_load:]
        elif self.washing_items: self.is_active, self.wash_start_time = True, time.time(); play_sound('click') 
    def update(self, player):
        if self.is_active and time.time() - self.wash_start_time >= WASH_TIME_SECONDS:
            for item in self.washing_items:
                if item.get('stains'):
                    if 'cleaned_stains' not in item: item['cleaned_stains'] = []
                    item['cleaned_stains'].extend(item['stains']); item['cleaned_stains'] = sorted(list(set(item['cleaned_stains'])))
                    item['type'], item['stains'] = 'clean', []
                    if 'stain_data' in item: del item['stain_data']
                if self.super_type and random.random() < self.super_chance: item.update({"super": True, "super_type": self.super_type, "value": item["value"] * self.multiplier})
                player.inventory["wet"].append(item)
            self.washing_items, self.is_active = [], False; play_sound('success')
    def get_progress(self): return (time.time() - self.wash_start_time) / WASH_TIME_SECONDS if self.is_active else 0
    def draw(self, surface): draw_washing_machine(surface, self.rect.x, self.rect.y, self.type, self.is_active, self.get_progress(), outline_color=self.outline_color)

class ClothesLine(Draggable):
    def __init__(self, line_type, pos):
        attrs = {"wooden": 3, "silver": 5, "gold": 10}; self.capacity = attrs.get(line_type, 3)
        super().__init__(pos, (20 + self.capacity * 45, 120))
        self.type, self.drying_items, self.next_stain_check_time = line_type, [], 0
    def draw(self, surface, scale=1.0, preview_mode=False):
        width = int((120 if preview_mode else self.rect.width) * scale); height = int(120 * scale)
        temp_rect = self.rect.copy(); temp_rect.size = (width, height)
        if preview_mode: temp_rect.center = self.rect.center
        x, y = temp_rect.topleft
        pole_color = {"wooden": BROWN, "silver": SILVER, "gold": GOLD}[self.type]
        pygame.draw.rect(surface, pole_color, (x, y, int(10*scale), height))
        pygame.draw.rect(surface, pole_color, (x + width - int(10*scale), y, int(10*scale), height))
        pygame.draw.line(surface, (50,50,50), (x + int(5*scale), y + int(20*scale)), (x + width - int(5*scale), y + int(20*scale)), int(3*scale))
        if not preview_mode:
            for i, item_info in enumerate(self.drying_items):
                draw_x, draw_y = self.rect.x + 12 + (i * 45), self.rect.y + 25
                draw_clothes(surface, draw_x, draw_y, item_info['item'])
                progress = item_info['progress'] / DRY_TIME_SECONDS
                bar_x, bar_y, bar_width = draw_x - 5, draw_y + 45, 40
                pygame.draw.rect(surface, (100, 100, 100), (bar_x, bar_y, bar_width, 8))
                pygame.draw.rect(surface, GREEN, (bar_x, bar_y, bar_width * progress, 8))
        if not preview_mode and self.outline_color: pygame.draw.rect(surface, self.outline_color, self.rect, 4, border_radius=8)
    def on_click(self, player):
        if self.is_dragging: return
        space_left = self.capacity - len(self.drying_items)
        if space_left > 0 and player.inventory["wet"]:
            for _ in range(min(space_left, len(player.inventory["wet"]))):
                self.drying_items.append({"item": player.inventory["wet"].pop(0), "progress": 0.0})
                self.next_stain_check_time = time.time() + random.uniform(5, 10)
            play_sound('drying')
    def update(self, player, current_weather):
        finished_drying, newly_stained = [], []
        if current_weather in ["thunderstorm", "chocolate_rain"] and time.time() >= self.next_stain_check_time and self.drying_items:
            self.next_stain_check_time = time.time() + random.uniform(5, 10)
            for item_info in self.drying_items:
                item = item_info['item']
                stain_type, stain_chance, value_mod, anim_color = None, 0, 0, None
                if current_weather == "thunderstorm": stain_type, stain_chance, value_mod, anim_color = "dirt_stain", 0.50, 1.15, DIRT_GREY
                elif current_weather == "chocolate_rain": stain_type, stain_chance, value_mod, anim_color = "choc_stain", 0.40, 1.30, CHOC_BROWN
                if stain_type and random.random() < stain_chance and stain_type not in item['stains']:
                    item['stains'].append(stain_type); item['value'] = round(item['value'] * value_mod)
                    item['stain_data'] = game.clothing_store.generate_stain_data(item['stains'])
                    item['type'] = 'stained'; newly_stained.append(item_info)
                    anim_particles = [[pygame.Vector2(self.rect.left + random.randint(10, self.rect.width-10), self.rect.top), pygame.Vector2(random.uniform(-0.5, 0.5), random.uniform(1,3)), random.randint(3,5)] for _ in range(20)]
                    game.stain_animations.append({'particles': anim_particles, 'color': anim_color, 'timer': 45})
        for item_info in self.drying_items:
            if current_weather == "sunny":
                item_info['progress'] += 1 / FPS
                if item_info['progress'] >= DRY_TIME_SECONDS: finished_drying.append(item_info)
        if newly_stained:
            for item_info in newly_stained: player.inventory['unwashed'].append(item_info['item'])
            self.drying_items = [item for item in self.drying_items if item not in newly_stained]
        if finished_drying:
            play_sound('success')
            for item_info in finished_drying: player.inventory["dry"].append(item_info['item'])
            self.drying_items = [item for item in self.drying_items if item not in finished_drying]

# --- Game Start ---
if __name__ == "__main__":
    game = Game() 
    game.run()