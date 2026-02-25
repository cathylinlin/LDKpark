import pygame
import random
import os
import math
import tkinter as tk
from tkinter import filedialog
import threading
import time

# 初始化 Pygame
pygame.init()
pygame.mixer.init()

# 游戏常量
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
FPS = 60

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKY_BLUE = (135, 206, 235)
GRASS_GREEN = (34, 139, 34)
PIPE_GREEN = (50, 205, 50)
PIPE_DARK_GREEN = (34, 139, 34)
YELLOW = (255, 215, 0)
ORANGE = (255, 165, 0)
RED = (255, 69, 0)

class Bird:
    def __init__(self):
        self.x = 100
        self.y = SCREEN_HEIGHT // 2
        self.velocity = 0
        self.gravity = 0.5
        self.jump_strength = -10
        self.angle = 0
        self.image = None
        self.animation_time = 0
        self.wing_offset = 0
        
    def jump(self):
        self.velocity = self.jump_strength
        
    def update(self):
        self.velocity += self.gravity
        self.velocity = min(self.velocity, 15)
        self.y += self.velocity
        
        if self.velocity < 0:
            self.angle = min(30, self.angle + 3)
        else:
            self.angle = max(-90, self.angle - 5)
        
        self.animation_time += 0.3
        self.wing_offset = math.sin(self.animation_time) * 3
        
    def draw(self, screen):
        if self.image:
            rotated_img = pygame.transform.rotate(self.image, self.angle)
            rect = rotated_img.get_rect(center=(self.x, self.y))
            screen.blit(rotated_img, rect)
        else:
            self._draw_default_bird(screen)
    
    def _draw_default_bird(self, screen):
        pygame.draw.ellipse(screen, (200, 180, 0), (self.x - 20 + 3, self.y - 15 + 3, 40, 30))
        pygame.draw.ellipse(screen, YELLOW, (self.x - 20, self.y - 15, 40, 30))
        pygame.draw.ellipse(screen, (255, 240, 100), (self.x - 18, self.y - 13, 36, 26))
        
        wing_y = self.y + self.wing_offset
        pygame.draw.ellipse(screen, WHITE, (self.x - 10, wing_y - 5, 20, 15))
        pygame.draw.ellipse(screen, (255, 220, 150), (self.x - 8, wing_y - 3, 16, 11))
        
        pygame.draw.circle(screen, WHITE, (self.x + 8, self.y - 5), 8)
        pygame.draw.circle(screen, BLACK, (self.x + 10, self.y - 5), 4)
        
        beak_points = [(self.x + 15, self.y), (self.x + 30, self.y + 5), (self.x + 15, self.y + 8)]
        pygame.draw.polygon(screen, ORANGE, beak_points)
        pygame.draw.polygon(screen, (255, 140, 0), beak_points, 2)
    
    def load_custom_image(self, path):
        try:
            img = pygame.image.load(path)
            self.image = pygame.transform.scale(img, (40, 30))
            return True
        except Exception as e:
            print(f"加载图片失败: {e}")
            return False
    
    def get_rect(self):
        return pygame.Rect(self.x - 15, self.y - 12, 30, 24)

class Pipe:
    def __init__(self, x):
        self.x = x
        self.width = 70
        self.gap = 180
        self.top_height = random.randint(50, SCREEN_HEIGHT - 150 - self.gap)
        self.speed = 4
        self.passed = False
        
    def update(self):
        self.x -= self.speed
        
    def draw(self, screen):
        self._draw_pipe(screen, self.x, 0, self.top_height, True)
        bottom_y = self.top_height + self.gap
        bottom_height = SCREEN_HEIGHT - bottom_y - 100
        self._draw_pipe(screen, self.x, bottom_y, bottom_height, False)
    
    def _draw_pipe(self, screen, x, y, height, is_top):
        pygame.draw.rect(screen, PIPE_GREEN, (x, y, self.width, height))
        pygame.draw.rect(screen, PIPE_DARK_GREEN, (x, y, self.width, height), 4)
        
        cap_height = 30
        cap_width = self.width + 10
        cap_x = x - 5
        
        if is_top:
            cap_y = height - cap_height
        else:
            cap_y = y
            
        pygame.draw.rect(screen, PIPE_GREEN, (cap_x, cap_y, cap_width, cap_height))
        pygame.draw.rect(screen, PIPE_DARK_GREEN, (cap_x, cap_y, cap_width, cap_height), 4)
        pygame.draw.rect(screen, (100, 255, 100), (x + 5, y, 8, height))
        
    def get_rects(self):
        top_rect = pygame.Rect(self.x, 0, self.width, self.top_height)
        bottom_rect = pygame.Rect(self.x, self.top_height + self.gap, 
                                 self.width, SCREEN_HEIGHT - self.top_height - self.gap - 100)
        return top_rect, bottom_rect

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, text_color=WHITE):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False
        self.font = pygame.font.Font(None, 36)
        
    def draw(self, screen):
        color = self.hover_color if self.is_hovered else self.color
        shadow_rect = self.rect.copy()
        shadow_rect.x += 4
        shadow_rect.y += 4
        pygame.draw.rect(screen, (0, 0, 0, 128), shadow_rect, border_radius=10)
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, WHITE, self.rect, 3, border_radius=10)
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered
    
    def is_clicked(self, pos, clicked):
        return clicked and self.rect.collidepoint(pos)

class FlappyBirdGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Flappy Bird")
        self.clock = pygame.time.Clock()
        
        self.state = "HOME"
        self.score = 0
        self.high_score = 0
        
        self.bird = Bird()
        self.pipes = []
        self.ground_x = 0
        
        # 键位设置 (存储整数键值)
        self.jump_key = pygame.K_SPACE
        self.jump_key_name = "SPACE"
        
        self.bgm_path = None
        self.bgm_playing = False
        
        self.setup_buttons()
        self.particles = []
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)
        
    def setup_buttons(self):
        center_x = SCREEN_WIDTH // 2
        self.play_button = Button(center_x - 80, 300, 160, 50, "PLAY", 
                                 (76, 175, 80), (129, 199, 132))
        self.settings_button = Button(center_x - 80, 370, 160, 50, "SETTINGS",
                                     (33, 150, 243), (100, 181, 246))
        
        self.restart_button = Button(center_x - 80, 400, 160, 50, "RESTART",
                                    (255, 152, 0), (255, 183, 77))
        self.home_button = Button(center_x - 80, 470, 160, 50, "HOME",
                                 (156, 39, 176), (186, 104, 200))
        
        # 设置页面按钮
        self.key_button = Button(50, 150, 300, 50, f"Jump Key: {self.jump_key_name}",
                                (96, 125, 139), (144, 164, 174))
        self.bird_image_button = Button(50, 230, 300, 50, "Load Bird Image",
                                       (255, 87, 34), (255, 138, 101))
        self.bgm_button = Button(50, 310, 300, 50, "Load BGM",
                                (0, 150, 136), (77, 182, 172))
        self.back_button = Button(50, 450, 300, 50, "BACK",
                                 (158, 158, 158), (224, 224, 224), BLACK)
    
    def reset_game(self):
        self.bird = Bird()
        # 恢复自定义图片
        if hasattr(self, 'saved_bird_image'):
            self.bird.image = self.saved_bird_image
        self.pipes = []
        self.score = 0
        self.particles = []
        
    def add_score_particle(self, x, y):
        for _ in range(10):
            self.particles.append({
                'x': x, 'y': y,
                'vx': random.uniform(-3, 3),
                'vy': random.uniform(-5, -1),
                'life': 30,
                'color': random.choice([YELLOW, ORANGE, WHITE])
            })
    
    def update_particles(self):
        for p in self.particles[:]:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += 0.2
            p['life'] -= 1
            if p['life'] <= 0:
                self.particles.remove(p)
    
    def draw_particles(self):
        for p in self.particles:
            pygame.draw.circle(self.screen, p['color'], 
                             (int(p['x']), int(p['y'])), 4)
    
    def draw_background(self):
        for y in range(SCREEN_HEIGHT):
            r = int(135 + (100 - 135) * y / SCREEN_HEIGHT)
            g = int(206 + (180 - 206) * y / SCREEN_HEIGHT)
            b = int(235 + (220 - 235) * y / SCREEN_HEIGHT)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        self._draw_clouds()
    
    def _draw_clouds(self):
        cloud_positions = [(50, 80), (250, 150), (150, 100), (320, 200)]
        for x, y in cloud_positions:
            pygame.draw.ellipse(self.screen, WHITE, (x, y, 60, 40))
            pygame.draw.ellipse(self.screen, WHITE, (x + 30, y - 10, 50, 35))
            pygame.draw.ellipse(self.screen, WHITE, (x + 50, y + 5, 40, 30))
    
    def draw_ground(self):
        ground_y = SCREEN_HEIGHT - 100
        pygame.draw.rect(self.screen, (222, 184, 135), (0, ground_y, SCREEN_WIDTH, 100))
        pygame.draw.rect(self.screen, GRASS_GREEN, (0, ground_y, SCREEN_WIDTH, 20))
        for i in range(-1, 15):
            x = i * 30 - (self.ground_x % 30)
            pygame.draw.line(self.screen, (139, 119, 101), (x, ground_y + 30), (x + 15, ground_y + 50), 2)
    
    def draw_score(self):
        score_text = str(self.score)
        shadow = self.font_large.render(score_text, True, BLACK)
        shadow_rect = shadow.get_rect(center=(SCREEN_WIDTH // 2 + 2, 52))
        self.screen.blit(shadow, shadow_rect)
        score_surface = self.font_large.render(score_text, True, WHITE)
        score_rect = score_surface.get_rect(center=(SCREEN_WIDTH // 2, 50))
        self.screen.blit(score_surface, score_rect)
    
    def draw_home_screen(self):
        self.draw_background()
        self.draw_ground()
        title = self.font_large.render("FLAPPY BIRD", True, WHITE)
        title_shadow = self.font_large.render("FLAPPY BIRD", True, BLACK)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(title_shadow, (title_rect.x + 3, title_rect.y + 3))
        self.screen.blit(title, title_rect)
        
        self.bird.y = 250 + math.sin(pygame.time.get_ticks() / 200) * 20
        self.bird.draw(self.screen)
        
        self.play_button.draw(self.screen)
        self.settings_button.draw(self.screen)
        
        if self.high_score > 0:
            high_score_text = self.font_small.render(f"Best: {self.high_score}", True, WHITE)
            self.screen.blit(high_score_text, (SCREEN_WIDTH // 2 - 50, 450))
    
    def draw_game_screen(self):
        self.draw_background()
        for pipe in self.pipes:
            pipe.draw(self.screen)
        self.draw_ground()
        self.bird.draw(self.screen)
        self.draw_score()
        self.draw_particles()
    
    def draw_game_over_screen(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(128)
        self.screen.blit(overlay, (0, 0))
        
        panel_rect = pygame.Rect(50, 150, 300, 300)
        pygame.draw.rect(self.screen, WHITE, panel_rect, border_radius=20)
        pygame.draw.rect(self.screen, ORANGE, panel_rect, 4, border_radius=20)
        
        title = self.font_large.render("GAME OVER", True, RED)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(title, title_rect)
        
        score_text = self.font_medium.render(f"Score: {self.score}", True, BLACK)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 270))
        self.screen.blit(score_text, score_rect)
        
        high_text = self.font_small.render(f"Best: {self.high_score}", True, BLACK)
        high_rect = high_text.get_rect(center=(SCREEN_WIDTH // 2, 320))
        self.screen.blit(high_text, high_rect)
        
        self.restart_button.draw(self.screen)
        self.home_button.draw(self.screen)
    
    def draw_settings_screen(self):
        self.draw_background()
        panel_rect = pygame.Rect(25, 50, 350, 480)
        pygame.draw.rect(self.screen, WHITE, panel_rect, border_radius=20)
        pygame.draw.rect(self.screen, (33, 150, 243), panel_rect, 4, border_radius=20)
        
        title = self.font_medium.render("SETTINGS", True, BLACK)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)
        
        self.key_button.draw(self.screen)
        self.bird_image_button.draw(self.screen)
        self.bgm_button.draw(self.screen)
        self.back_button.draw(self.screen)
        
        self.bird.x = SCREEN_WIDTH // 2
        self.bird.y = 420
        self.bird.draw(self.screen)
    
    def open_key_settings(self):
        def run_dialog():
            root = tk.Tk()
            root.title("Set Jump Key")
            root.geometry("300x120")
            tk.Label(root, text="Press a key to set as jump key", font=("Arial", 12)).pack(pady=30)
            root.focus_set()
            
            def on_key(event):
                tk_key = event.keysym
                # 键名映射转换
                key_map = {'Up': 'up', 'Down': 'down', 'Left': 'left', 'Right': 'right', 'Space': 'space'}
                pg_key_name = key_map.get(tk_key, tk_key.lower())
                
                try:
                    pg_code = pygame.key.key_code(pg_key_name)
                    self.jump_key = pg_code
                    self.jump_key_name = pg_key_name.upper()
                    self.key_button.text = f"Jump Key: {self.jump_key_name}"
                    root.destroy() # 直接关闭，无弹窗
                except:
                    pass
            
            root.bind('<KeyPress>', on_key)
            root.mainloop()
        
        threading.Thread(target=run_dialog, daemon=True).start()
    
    def load_bird_image(self):
        # 移回主线程防止崩溃
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(
            title="Select Bird Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")]
        )
        if file_path:
            if self.bird.load_custom_image(file_path):
                self.saved_bird_image = self.bird.image
        root.destroy()
    
    def load_bgm(self):
        # 移回主线程防止崩溃
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(
            title="Select BGM File",
            filetypes=[("Audio files", "*.mp3 *.wav *.ogg")]
        )
        if file_path:
            self.bgm_path = file_path
        root.destroy()
    
    def play_bgm(self):
        if self.bgm_path and not self.bgm_playing:
            try:
                pygame.mixer.music.load(self.bgm_path)
                pygame.mixer.music.play(-1)
                self.bgm_playing = True
            except Exception as e:
                print(f"BGM error: {e}")
    
    def stop_bgm(self):
        if self.bgm_playing:
            pygame.mixer.music.stop()
            self.bgm_playing = False
    
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
                        self.bird.jump()
                elif self.state == "HOME":
                    if event.key == self.jump_key:
                        self.state = "PLAYING"
                        self.reset_game()
                        self.play_bgm()
        
        if self.state == "HOME":
            self.play_button.check_hover(mouse_pos)
            self.settings_button.check_hover(mouse_pos)
            
            if self.play_button.is_clicked(mouse_pos, clicked):
                self.state = "PLAYING"
                self.reset_game()
                self.play_bgm()
            elif self.settings_button.is_clicked(mouse_pos, clicked):
                self.state = "SETTINGS"
                
        elif self.state == "GAME_OVER":
            self.restart_button.check_hover(mouse_pos)
            self.home_button.check_hover(mouse_pos)
            
            if self.restart_button.is_clicked(mouse_pos, clicked):
                self.state = "PLAYING"
                self.reset_game()
                self.play_bgm()
            elif self.home_button.is_clicked(mouse_pos, clicked):
                self.state = "HOME"
                self.reset_game()
                self.stop_bgm()
                
        elif self.state == "SETTINGS":
            self.key_button.check_hover(mouse_pos)
            self.bird_image_button.check_hover(mouse_pos)
            self.bgm_button.check_hover(mouse_pos)
            self.back_button.check_hover(mouse_pos)
            
            if self.key_button.is_clicked(mouse_pos, clicked):
                self.open_key_settings()
            elif self.bird_image_button.is_clicked(mouse_pos, clicked):
                self.load_bird_image()
            elif self.bgm_button.is_clicked(mouse_pos, clicked):
                self.load_bgm()
            elif self.back_button.is_clicked(mouse_pos, clicked):
                self.state = "HOME"
        
        return True
    
    def update(self):
        if self.state == "PLAYING":
            self.bird.update()
            self.ground_x += 4
            self.update_particles()
            
            if len(self.pipes) == 0 or self.pipes[-1].x < SCREEN_WIDTH - 200:
                self.pipes.append(Pipe(SCREEN_WIDTH + 50))
            
            for pipe in self.pipes[:]:
                pipe.update()
                
                if not pipe.passed and pipe.x + pipe.width < self.bird.x:
                    pipe.passed = True
                    self.score += 1
                    self.add_score_particle(self.bird.x, self.bird.y)
                
                if pipe.x < -pipe.width:
                    self.pipes.remove(pipe)
            
            bird_rect = self.bird.get_rect()
            
            if self.bird.y > SCREEN_HEIGHT - 100 - 15 or self.bird.y < 15:
                self.game_over()
            
            for pipe in self.pipes:
                top_rect, bottom_rect = pipe.get_rects()
                if bird_rect.colliderect(top_rect) or bird_rect.colliderect(bottom_rect):
                    self.game_over()
    
    def game_over(self):
        self.state = "GAME_OVER"
        self.stop_bgm()
        if self.score > self.high_score:
            self.high_score = self.score
    
    def draw(self):
        if self.state == "HOME":
            self.draw_home_screen()
        elif self.state == "PLAYING":
            self.draw_game_screen()
        elif self.state == "GAME_OVER":
            self.draw_game_screen()
            self.draw_game_over_screen()
        elif self.state == "SETTINGS":
            self.draw_settings_screen()
        
        pygame.display.flip()
    
    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()

# --- 模块接口 ---
_game_instance = None

def run():
    global _game_instance
    _game_instance = FlappyBirdGame()
    _game_instance.run()

def close():
    global _game_instance
    if _game_instance:
        pygame.quit()
        _game_instance = None
