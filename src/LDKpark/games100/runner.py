import pygame
import random
import os
import math
import tkinter as tk
from tkinter import filedialog
import threading

# --- 游戏配置 ---
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 500
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKY_BLUE = (135, 206, 235)
GROUND_COLOR = (194, 178, 128)
PLAYER_COLOR = (50, 50, 200)
OBSTACLE_COLOR = (200, 50, 50)

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-4, 0)
        self.life = random.randint(20, 40)
        self.size = random.randint(3, 6)
        
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2
        self.life -= 1
        self.size = max(1, self.size - 0.1)
        
    def draw(self, screen):
        if self.life > 0:
            s = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
            alpha = int(255 * (self.life / 40))
            pygame.draw.circle(s, (*self.color, alpha), (self.size, self.size), int(self.size))
            screen.blit(s, (self.x - self.size, self.y - self.size))

class Player:
    def __init__(self):
        self.x = 100
        self.width = 40
        self.height = 60
        self.y = 350
        
        # 物理属性 - 降低跳跃力
        self.gravity = 0.8
        self.jump_power = -13  # 从 -16 改为 -10
        self.vel_y = 0
        self.is_jumping = False
        self.is_ducking = False
        
        self.image = None
        self.animation_count = 0
        
    def jump(self):
        if not self.is_jumping and not self.is_ducking:
            self.vel_y = self.jump_power
            self.is_jumping = True
            
    def duck(self, state):
        if self.is_jumping: return
        self.is_ducking = state
        
    def update(self):
        self.vel_y += self.gravity
        self.y += self.vel_y
        
        ground_level = 410
        target_height = 30 if self.is_ducking else 60
        
        if self.height != target_height:
            self.y = self.y + self.height - target_height
            self.height = target_height
            
        feet_y = self.y + self.height
        
        if feet_y >= ground_level:
            self.y = ground_level - self.height
            self.vel_y = 0
            self.is_jumping = False
            
        self.animation_count += 1
        
    def draw(self, screen):
        current_height = self.height
        current_width = 50 if self.is_ducking else 40
        
        if self.image:
            scaled_img = pygame.transform.scale(self.image, (current_width, current_height))
            screen.blit(scaled_img, (self.x, self.y))
        else:
            self._draw_default(screen, current_width, current_height)
            
    def _draw_default(self, screen, w, h):
        color = PLAYER_COLOR
        pygame.draw.rect(screen, color, (self.x, self.y + 10, w, h - 10))
        head_radius = 12 if not self.is_ducking else 8
        pygame.draw.circle(screen, color, (self.x + w//2, self.y + 10), head_radius)
        
        if not self.is_jumping:
            leg_offset = math.sin(self.animation_count * 0.3) * 5
            pygame.draw.line(screen, color, (self.x + 10, self.y + h), (self.x + 10 - leg_offset, self.y + h + 15), 4)
            pygame.draw.line(screen, color, (self.x + w - 10, self.y + h), (self.x + w - 10 + leg_offset, self.y + h + 15), 4)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width if not self.is_ducking else 50, self.height)

class Obstacle:
    def __init__(self, type, speed, custom_img=None):
        self.type = type
        self.x = SCREEN_WIDTH + 100
        self.speed = speed
        self.image = custom_img
        self.passed = False
        
        if type == 'ground':
            self.width = 30
            self.height = 50
            self.y = 360  # 地面障碍物
        else:  # air
            self.width = 50
            self.height = 50
            # 关键：调整为 Y=320，让站立/跳跃都撞，下蹲能过
            self.y = 320
            
    def update(self, speed):
        self.x -= speed
        if self.type == 'air':
            self.y += math.sin(pygame.time.get_ticks() * 0.01) * 0.5
            
    def draw(self, screen):
        if self.image:
            screen.blit(pygame.transform.scale(self.image, (self.width, self.height)), (self.x, self.y))
        else:
            color = OBSTACLE_COLOR
            if self.type == 'ground':
                pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))
                pygame.draw.rect(screen, (0,0,0), (self.x, self.y, self.width, self.height), 2)
            else:
                # 空中障碍物 - 画成更明显的方块
                pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))
                pygame.draw.rect(screen, (150, 30, 30), (self.x, self.y, self.width, self.height), 3)
                # 添加警示标志
                pygame.draw.line(screen, WHITE, (self.x + 10, self.y + 10), (self.x + 40, self.y + 40), 3)
                pygame.draw.line(screen, WHITE, (self.x + 40, self.y + 10), (self.x + 10, self.y + 40), 3)
                
    def get_rect(self):
        # 稍微缩小碰撞箱增加容错
        return pygame.Rect(self.x + 5, self.y + 5, self.width - 10, self.height - 10)

class Button:
    def __init__(self, x, y, w, h, text, color, hover_color):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.font = pygame.font.Font(None, 32)
        
    def draw(self, screen):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=8)
        text_surf = self.font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
        
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        
    def is_clicked(self, pos, clicked):
        return clicked and self.rect.collidepoint(pos)

class RunnerGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Parkour Runner")
        self.clock = pygame.time.Clock()
        
        self.state = "MENU"
        self.score = 0
        self.high_score = 0
        self.game_speed = 7
        
        self.player = Player()
        self.obstacles = []
        self.particles = []
        
        self.bg_scroll = 0
        self.clouds = [[SCREEN_WIDTH + random.randint(0, 200), random.randint(50, 150), random.randint(30, 60)] for _ in range(5)]
        self.mountains = [[SCREEN_WIDTH + random.randint(0, 500), random.randint(200, 300), random.randint(100, 300)] for _ in range(4)]
        
        self.jump_key = pygame.K_SPACE
        self.duck_key = pygame.K_DOWN
        
        self.bgm_path = None
        self.custom_player_img = None
        self.custom_ground_obs_img = None
        self.custom_air_obs_img = None
        
        self.font = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 72)
        
        self.setup_buttons()
        
    def setup_buttons(self):
        cx = SCREEN_WIDTH // 2
        self.start_btn = Button(cx - 100, 250, 200, 50, "START", (76, 175, 80), (100, 200, 100))
        self.settings_btn = Button(cx - 100, 320, 200, 50, "SETTINGS", (33, 150, 243), (100, 181, 246))
        
        self.retry_btn = Button(cx - 100, 280, 200, 50, "RETRY", (255, 152, 0), (255, 183, 77))
        self.menu_btn = Button(cx - 100, 350, 200, 50, "MENU", (156, 39, 176), (186, 104, 200))
        
        self.key_jump_btn = Button(50, 80, 300, 40, f"Jump Key: {pygame.key.name(self.jump_key)}", (96, 125, 139), (144, 164, 174))
        self.key_duck_btn = Button(50, 130, 300, 40, f"Duck Key: {pygame.key.name(self.duck_key)}", (96, 125, 139), (144, 164, 174))
        self.player_img_btn = Button(50, 190, 300, 40, "Load Player Image", (255, 87, 34), (255, 138, 101))
        self.ground_obs_btn = Button(50, 240, 300, 40, "Load Ground Obstacle", (200, 50, 50), (220, 100, 100))
        self.air_obs_btn = Button(50, 290, 300, 40, "Load Air Obstacle", (150, 50, 150), (180, 100, 180))
        self.bgm_btn = Button(50, 340, 300, 40, "Load BGM", (0, 150, 136), (77, 182, 172))
        self.back_btn = Button(SCREEN_WIDTH//2 - 50, 420, 100, 40, "BACK", (158, 158, 158), (224, 224, 224))

    def reset_game(self):
        self.player = Player()
        if self.custom_player_img:
            self.player.image = self.custom_player_img
            
        self.obstacles = []
        self.particles = []
        self.score = 0
        self.game_speed = 7
        
    def spawn_particles(self, x, y, count=10, color=WHITE):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))

    def update_game(self):
        self.player.update()
        
        self.bg_scroll += self.game_speed
        
        for c in self.clouds:
            c[0] -= self.game_speed * 0.2
            if c[0] < -c[2]:
                c[0] = SCREEN_WIDTH + random.randint(0, 100)
                c[1] = random.randint(50, 150)
        
        for m in self.mountains:
            m[0] -= self.game_speed * 0.5
            if m[0] < -m[2]:
                m[0] = SCREEN_WIDTH + random.randint(0, 200)
        
        if len(self.obstacles) == 0 or self.obstacles[-1].x < SCREEN_WIDTH - random.randint(300, 500):
            if random.random() < 0.4:
                obs_type = 'air'
                img = self.custom_air_obs_img
            else:
                obs_type = 'ground'
                img = self.custom_ground_obs_img
                
            self.obstacles.append(Obstacle(obs_type, self.game_speed, img))
            
        for obs in self.obstacles[:]:
            obs.update(self.game_speed)
            if obs.x < -50:
                self.obstacles.remove(obs)
                self.score += 10
                if self.score % 100 == 0:
                    self.game_speed = min(20, self.game_speed + 0.5)
                    
        player_rect = self.player.get_rect()
        for obs in self.obstacles:
            obs_rect = obs.get_rect()
            if player_rect.colliderect(obs_rect):
                self.game_over()
                return
                
        if not self.player.is_jumping and random.random() < 0.3:
            self.spawn_particles(self.player.x + 10, 410, 1, (150, 140, 100))
            
        for p in self.particles[:]:
            p.update()
            if p.life <= 0:
                self.particles.remove(p)

    def game_over(self):
        self.state = "GAME_OVER"
        if self.score > self.high_score:
            self.high_score = self.score
        self.spawn_particles(self.player.x, self.player.y, 30, (255, 100, 0))
        self.stop_bgm()

    def draw_background(self):
        for y in range(SCREEN_HEIGHT):
            r = int(135 + (200 - 135) * y / SCREEN_HEIGHT)
            g = int(206 + (220 - 206) * y / SCREEN_HEIGHT)
            b = int(235 + (240 - 235) * y / SCREEN_HEIGHT)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
            
        pygame.draw.circle(self.screen, (255, 255, 200), (700, 100), 40)
        
        for m in self.mountains:
            color = (100, 120, 100)
            points = [(m[0], 400), (m[0] + m[2]//2, 400 - m[1]), (m[0] + m[2], 400)]
            pygame.draw.polygon(self.screen, color, points)
            
        for c in self.clouds:
            pygame.draw.ellipse(self.screen, WHITE, (c[0], c[1], c[2], c[2]//2))
            
        pygame.draw.rect(self.screen, GROUND_COLOR, (0, 410, SCREEN_WIDTH, 90))
        pygame.draw.line(self.screen, (170, 150, 100), (0, 410), (SCREEN_WIDTH, 410), 3)
        
    def draw_ui(self):
        score_text = self.font.render(f"Score: {self.score}", True, BLACK)
        self.screen.blit(score_text, (20, 20))
        
        speed_text = self.font.render(f"Speed: {self.game_speed:.1f}", True, BLACK)
        self.screen.blit(speed_text, (20, 50))

    def draw_menu(self):
        self.draw_background()
        title = self.big_font.render("PARKOUR RUNNER", True, (50, 50, 50))
        rect = title.get_rect(center=(SCREEN_WIDTH//2, 120))
        self.screen.blit(title, rect)
        self.player.x = SCREEN_WIDTH//2 - 50
        self.player.y = 350
        self.player.is_ducking = False
        self.player.height = 60
        self.player.draw(self.screen)
        self.start_btn.draw(self.screen)
        self.settings_btn.draw(self.screen)

    def draw_game_over(self):
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        s.set_alpha(150)
        s.fill(BLACK)
        self.screen.blit(s, (0,0))
        
        text = self.big_font.render("GAME OVER", True, (255, 50, 50))
        rect = text.get_rect(center=(SCREEN_WIDTH//2, 180))
        self.screen.blit(text, rect)
        
        score_text = self.font.render(f"Score: {self.score}  Best: {self.high_score}", True, WHITE)
        rect = score_text.get_rect(center=(SCREEN_WIDTH//2, 230))
        self.screen.blit(score_text, rect)
        
        self.retry_btn.draw(self.screen)
        self.menu_btn.draw(self.screen)

    def draw_settings(self):
        self.screen.fill((240, 240, 240))
        title = self.big_font.render("SETTINGS", True, (50, 50, 50))
        self.screen.blit(title, (SCREEN_WIDTH//2 - 100, 20))
        
        self.key_jump_btn.draw(self.screen)
        self.key_duck_btn.draw(self.screen)
        self.player_img_btn.draw(self.screen)
        self.ground_obs_btn.draw(self.screen)
        self.air_obs_btn.draw(self.screen)
        self.bgm_btn.draw(self.screen)
        self.back_btn.draw(self.screen)
        
        self.player.x = 700
        self.player.y = 300
        self.player.draw(self.screen)
        
        hint = self.font.render("Custom images will be scaled", True, (100,100,100))
        self.screen.blit(hint, (50, 390))

    # --- 资源加载 ---

    def open_key_dialog(self, type):
        def run():
            root = tk.Tk()
            root.title("Key Setting")
            root.geometry("300x120")
            tk.Label(root, text=f"Press key for {type.upper()}...", font=("Arial", 12)).pack(pady=30)
            root.focus_set()
            
            def on_key(e):
                tk_key = e.keysym
                key_map = {'Up': 'up', 'Down': 'down', 'Left': 'left', 'Right': 'right', 'Space': 'space'}
                pg_key_name = key_map.get(tk_key, tk_key.lower())
                
                try:
                    pg_code = pygame.key.key_code(pg_key_name)
                    
                    if type == "jump":
                        self.jump_key = pg_code
                        self.key_jump_btn.text = f"Jump Key: {pg_key_name}"
                    else:
                        self.duck_key = pg_code
                        self.key_duck_btn.text = f"Duck Key: {pg_key_name}"
                    
                    # 移除了 messagebox 提示框，直接关闭窗口
                    root.destroy()
                except:
                    pass  # 忽略不支持的按键
                    
            root.bind('<KeyPress>', on_key)
            root.mainloop()
            
        threading.Thread(target=run, daemon=True).start()

    def load_img_resource(self, type):
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askopenfilename(filetypes=[("Image", "*.png;*.jpg;*.bmp")])
        if path:
            try:
                img = pygame.image.load(path)
                if type == "player":
                    self.custom_player_img = img
                    self.player.image = img
                elif type == "ground_obs":
                    self.custom_ground_obs_img = img
                elif type == "air_obs":
                    self.custom_air_obs_img = img
            except Exception as e:
                print(e)
        root.destroy()

    def load_bgm_resource(self):
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askopenfilename(filetypes=[("Audio", "*.mp3;*.wav")])
        if path:
            self.bgm_path = path
        root.destroy()

    def play_bgm(self):
        if self.bgm_path:
            try:
                pygame.mixer.music.load(self.bgm_path)
                pygame.mixer.music.play(-1)
            except: pass

    def stop_bgm(self):
        pygame.mixer.music.stop()

    # --- 主循环 ---
    
    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        clicked = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.MOUSEBUTTONDOWN:
                clicked = True
            if event.type == pygame.KEYDOWN:
                if self.state == "PLAYING":
                    if event.key == self.jump_key:
                        self.player.jump()
                        self.spawn_particles(self.player.x, 410, 5, (200, 200, 200))
                    if event.key == self.duck_key:
                        self.player.duck(True)
                elif self.state == "MENU":
                    if event.key == self.jump_key:
                        self.state = "PLAYING"; self.reset_game(); self.play_bgm()
            if event.type == pygame.KEYUP:
                if event.key == self.duck_key:
                    self.player.duck(False)
                    
        if self.state == "MENU":
            self.start_btn.check_hover(mouse_pos)
            self.settings_btn.check_hover(mouse_pos)
            if self.start_btn.is_clicked(mouse_pos, clicked):
                self.state = "PLAYING"; self.reset_game(); self.play_bgm()
            if self.settings_btn.is_clicked(mouse_pos, clicked):
                self.state = "SETTINGS"
                
        elif self.state == "GAME_OVER":
            self.retry_btn.check_hover(mouse_pos)
            self.menu_btn.check_hover(mouse_pos)
            if self.retry_btn.is_clicked(mouse_pos, clicked):
                self.state = "PLAYING"; self.reset_game(); self.play_bgm()
            if self.menu_btn.is_clicked(mouse_pos, clicked):
                self.state = "MENU"; self.stop_bgm()
                
        elif self.state == "SETTINGS":
            self.key_jump_btn.check_hover(mouse_pos)
            self.key_duck_btn.check_hover(mouse_pos)
            self.player_img_btn.check_hover(mouse_pos)
            self.ground_obs_btn.check_hover(mouse_pos)
            self.air_obs_btn.check_hover(mouse_pos)
            self.bgm_btn.check_hover(mouse_pos)
            self.back_btn.check_hover(mouse_pos)
            
            if self.key_jump_btn.is_clicked(mouse_pos, clicked): self.open_key_dialog("jump")
            if self.key_duck_btn.is_clicked(mouse_pos, clicked): self.open_key_dialog("duck")
            if self.player_img_btn.is_clicked(mouse_pos, clicked): self.load_img_resource("player")
            if self.ground_obs_btn.is_clicked(mouse_pos, clicked): self.load_img_resource("ground_obs")
            if self.air_obs_btn.is_clicked(mouse_pos, clicked): self.load_img_resource("air_obs")
            if self.bgm_btn.is_clicked(mouse_pos, clicked): self.load_bgm_resource()
            if self.back_btn.is_clicked(mouse_pos, clicked): self.state = "MENU"
            
        return True

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            
            if self.state == "PLAYING":
                self.update_game()
            
            if self.state == "MENU":
                self.draw_menu()
            elif self.state == "PLAYING":
                self.draw_background()
                for obs in self.obstacles:
                    obs.draw(self.screen)
                for p in self.particles:
                    p.draw(self.screen)
                self.player.draw(self.screen)
                self.draw_ui()
            elif self.state == "GAME_OVER":
                self.draw_background()
                for obs in self.obstacles: obs.draw(self.screen)
                for p in self.particles: p.draw(self.screen)
                self.player.draw(self.screen)
                self.draw_game_over()
            elif self.state == "SETTINGS":
                self.draw_settings()
                
            pygame.display.flip()
            self.clock.tick(FPS)
            
        pygame.quit()

# --- 模块接口 ---
_game = None

def run():
    global _game
    _game = RunnerGame()
    _game.run()

def close():
    global _game
    if _game:
        pygame.quit()
        _game = None
