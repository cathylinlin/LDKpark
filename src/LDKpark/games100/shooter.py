import pygame
import random
import math
import os
import sys

# --- 配置与常量 ---

# 屏幕设置 - 竖屏比例
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 800
FPS = 60

# 颜色定义
COLORS = {
    'bg': (15, 15, 30),
    'bg_star': (40, 40, 60),
    'player': (0, 200, 255),
    'player_engine': (100, 200, 255),
    'bullet': (255, 255, 100),
    'enemy_small': (255, 100, 100),
    'enemy_medium': (255, 150, 50),
    'enemy_large': (255, 50, 150),
    'boss': (200, 50, 255),
    'powerup_health': (0, 255, 100),
    'powerup_weapon': (255, 200, 0),
    'powerup_shield': (100, 100, 255),
    'text': (255, 255, 255),
    'text_highlight': (255, 255, 100),
    'text_dim': (150, 150, 150),
    'ui_bg': (30, 30, 50, 180),
}

# 游戏常量
PLAYER_SPEED = 6
BULLET_SPEED = 12
ENEMY_BULLET_SPEED = 5
POWERUP_SPEED = 2

# 敌机类型配置
ENEMY_TYPES = {
    'small': {'hp': 1, 'score': 10, 'speed': (2, 4), 'size': 30, 'color': COLORS['enemy_small']},
    'medium': {'hp': 3, 'score': 30, 'speed': (1.5, 2.5), 'size': 45, 'color': COLORS['enemy_medium']},
    'large': {'hp': 8, 'score': 100, 'speed': (0.8, 1.5), 'size': 60, 'color': COLORS['enemy_large']},
}

# --- 辅助函数 ---

def draw_triangle(surface, color, center, size, angle=0):
    """绘制三角形，用于飞机形状"""
    points = []
    for i in range(3):
        a = math.radians(angle + i * 120)
        x = center[0] + size * math.cos(a)
        y = center[1] + size * math.sin(a)
        points.append((x, y))
    pygame.draw.polygon(surface, color, points)
    pygame.draw.polygon(surface, (255, 255, 255), points, 2)

def draw_diamond(surface, color, center, size):
    """绘制菱形，用于敌机"""
    points = [
        (center[0], center[1] - size),
        (center[0] + size * 0.8, center[1]),
        (center[0], center[1] + size),
        (center[0] - size * 0.8, center[1]),
    ]
    pygame.draw.polygon(surface, color, points)
    pygame.draw.polygon(surface, (255, 255, 255), points, 2)

def draw_hexagon(surface, color, center, size):
    """绘制六边形，用于大型敌机"""
    points = []
    for i in range(6):
        a = math.radians(i * 60)
        x = center[0] + size * math.cos(a)
        y = center[1] + size * math.sin(a)
        points.append((x, y))
    pygame.draw.polygon(surface, color, points)
    pygame.draw.polygon(surface, (255, 255, 255), points, 2)

def check_collision(obj1, obj2):
    """圆形碰撞检测"""
    dx = obj1.x - obj2.x
    dy = obj1.y - obj2.y
    distance = math.sqrt(dx * dx + dy * dy)
    return distance < (obj1.radius + obj2.radius)

# --- 游戏对象类 ---

class Star:
    """背景星星"""
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        self.size = random.randint(1, 3)
        self.speed = random.uniform(0.5, 2)
        self.brightness = random.randint(100, 255)
    
    def update(self):
        self.y += self.speed
        if self.y > SCREEN_HEIGHT:
            self.y = 0
            self.x = random.randint(0, SCREEN_WIDTH)
    
    def draw(self, screen):
        color = (self.brightness, self.brightness, self.brightness)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.size)

class Particle:
    """粒子效果"""
    def __init__(self, x, y, color, speed=3, life=30):
        self.x = x
        self.y = y
        self.color = color
        angle = random.uniform(0, 2 * math.pi)
        self.vx = math.cos(angle) * random.uniform(1, speed)
        self.vy = math.sin(angle) * random.uniform(1, speed)
        self.life = life
        self.max_life = life
        self.size = random.randint(2, 5)
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        self.size = max(1, self.size - 0.1)
    
    def draw(self, screen):
        if self.life > 0:
            alpha = int(255 * (self.life / self.max_life))
            color = (*self.color[:3], alpha)
            s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (self.size, self.size), int(self.size))
            screen.blit(s, (int(self.x - self.size), int(self.y - self.size)))
    
    def is_dead(self):
        return self.life <= 0

class Bullet:
    """子弹类"""
    def __init__(self, x, y, speed, is_player=True, damage=1):
        self.x = x
        self.y = y
        self.speed = speed
        self.is_player = is_player
        self.damage = damage
        self.radius = 4
        self.active = True
    
    def update(self):
        self.y += self.speed
        if self.y < -10 or self.y > SCREEN_HEIGHT + 10:
            self.active = False
    
    def draw(self, screen):
        color = COLORS['bullet'] if self.is_player else (255, 100, 100)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.radius)
        # 光晕效果
        glow = pygame.Surface((12, 12), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*color[:3], 100), (6, 6), 5)
        screen.blit(glow, (int(self.x - 6), int(self.y - 6)))

class PowerUp:
    """道具类"""
    TYPES = ['health', 'weapon', 'shield']
    COLORS = {
        'health': COLORS['powerup_health'],
        'weapon': COLORS['powerup_weapon'],
        'shield': COLORS['powerup_shield'],
    }
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.type = random.choice(self.TYPES)
        self.speed = POWERUP_SPEED
        self.radius = 15
        self.active = True
        self.angle = 0
    
    def update(self):
        self.y += self.speed
        self.angle += 3
        if self.y > SCREEN_HEIGHT + 20:
            self.active = False
    
    def draw(self, screen):
        color = self.COLORS[self.type]
        # 旋转效果
        size = 12 + math.sin(math.radians(self.angle)) * 3
        
        if self.type == 'health':
            # 十字形状
            pygame.draw.rect(screen, color, (self.x - size, self.y - 4, size * 2, 8))
            pygame.draw.rect(screen, color, (self.x - 4, self.y - size, 8, size * 2))
        elif self.type == 'weapon':
            # 箭头形状
            points = [
                (self.x, self.y - size),
                (self.x + size * 0.7, self.y + size * 0.5),
                (self.x, self.y),
                (self.x - size * 0.7, self.y + size * 0.5),
            ]
            pygame.draw.polygon(screen, color, points)
        else:  # shield
            # 圆形
            pygame.draw.circle(screen, color, (int(self.x), int(self.y)), int(size))
        
        # 外圈
        pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), int(size + 4), 2)

class Enemy:
    """敌机基类"""
    def __init__(self, enemy_type, x, y):
        self.type = enemy_type
        self.config = ENEMY_TYPES[enemy_type]
        self.x = x
        self.y = y
        self.hp = self.config['hp']
        self.max_hp = self.config['hp']
        self.radius = self.config['size'] // 2
        self.speed_y = random.uniform(*self.config['speed'])
        self.speed_x = 0
        self.active = True
        self.shoot_timer = 0
        self.shoot_interval = random.randint(60, 120)
        self.angle = 0
    
    def update(self):
        self.y += self.speed_y
        self.x += self.speed_x
        self.angle += 2
        
        # 边界检查
        if self.x < self.radius:
            self.x = self.radius
            self.speed_x *= -1
        elif self.x > SCREEN_WIDTH - self.radius:
            self.x = SCREEN_WIDTH - self.radius
            self.speed_x *= -1
        
        if self.y > SCREEN_HEIGHT + 50:
            self.active = False
        
        self.shoot_timer += 1
    
    def draw(self, screen):
        color = self.config['color']
        
        if self.type == 'small':
            draw_diamond(screen, color, (self.x, self.y), self.radius)
        elif self.type == 'medium':
            draw_triangle(screen, color, (self.x, self.y), self.radius, self.angle)
        else:  # large
            draw_hexagon(screen, color, (self.x, self.y), self.radius)
        
        # 血条
        if self.hp < self.max_hp:
            bar_width = self.radius * 1.5
            bar_height = 4
            hp_ratio = self.hp / self.max_hp
            pygame.draw.rect(screen, (100, 100, 100), 
                           (self.x - bar_width/2, self.y - self.radius - 10, bar_width, bar_height))
            pygame.draw.rect(screen, (0, 255, 0), 
                           (self.x - bar_width/2, self.y - self.radius - 10, bar_width * hp_ratio, bar_height))
    
    def take_damage(self, damage):
        self.hp -= damage
        if self.hp <= 0:
            self.active = False
            return True
        return False
    
    def can_shoot(self):
        if self.shoot_timer >= self.shoot_interval:
            self.shoot_timer = 0
            return True
        return False

class Player:
    """玩家飞机"""
    def __init__(self):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT - 100
        self.radius = 20
        self.speed = PLAYER_SPEED
        self.hp = 3
        self.max_hp = 5
        self.weapon_level = 1
        self.shield = False
        self.shield_time = 0
        self.invincible = 0
        self.shoot_timer = 0
        self.shoot_interval = 8
        self.active = True
    
    def update(self, keys):
        # 移动控制
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.y += self.speed
        
        # 边界限制
        self.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(SCREEN_HEIGHT - self.radius, self.y))
        
        # 护盾倒计时
        if self.shield:
            self.shield_time -= 1
            if self.shield_time <= 0:
                self.shield = False
        
        # 无敌时间
        if self.invincible > 0:
            self.invincible -= 1
        
        self.shoot_timer += 1
    
    def draw(self, screen):
        # 无敌闪烁效果
        if self.invincible > 0 and self.invincible % 6 < 3:
            return
        
        # 护盾效果
        if self.shield:
            shield_radius = self.radius + 15 + math.sin(pygame.time.get_ticks() / 100) * 3
            pygame.draw.circle(screen, (100, 100, 255, 100), (int(self.x), int(self.y)), int(shield_radius), 3)
        
        # 飞机主体 - 三角形
        color = COLORS['player']
        points = [
            (self.x, self.y - self.radius),
            (self.x + self.radius * 0.8, self.y + self.radius * 0.5),
            (self.x, self.y + self.radius * 0.2),
            (self.x - self.radius * 0.8, self.y + self.radius * 0.5),
        ]
        pygame.draw.polygon(screen, color, points)
        pygame.draw.polygon(screen, (255, 255, 255), points, 2)
        
        # 引擎火焰
        flame_height = 15 + random.randint(0, 8)
        flame_points = [
            (self.x - self.radius * 0.3, self.y + self.radius * 0.3),
            (self.x, self.y + self.radius * 0.3 + flame_height),
            (self.x + self.radius * 0.3, self.y + self.radius * 0.3),
        ]
        pygame.draw.polygon(screen, COLORS['player_engine'], flame_points)
    
    def shoot(self):
        if self.shoot_timer >= self.shoot_interval:
            self.shoot_timer = 0
            bullets = []
            
            if self.weapon_level == 1:
                bullets.append(Bullet(self.x, self.y - self.radius, -BULLET_SPEED))
            elif self.weapon_level == 2:
                bullets.append(Bullet(self.x - 10, self.y - self.radius, -BULLET_SPEED))
                bullets.append(Bullet(self.x + 10, self.y - self.radius, -BULLET_SPEED))
            elif self.weapon_level >= 3:
                bullets.append(Bullet(self.x, self.y - self.radius, -BULLET_SPEED))
                bullets.append(Bullet(self.x - 15, self.y - self.radius + 5, -BULLET_SPEED))
                bullets.append(Bullet(self.x + 15, self.y - self.radius + 5, -BULLET_SPEED))
            
            return bullets
        return []
    
    def take_damage(self):
        if self.invincible > 0:
            return False
        
        if self.shield:
            self.shield = False
            self.invincible = 60
            return False
        
        self.hp -= 1
        self.invincible = 120
        self.weapon_level = max(1, self.weapon_level - 1)
        
        if self.hp <= 0:
            self.active = False
        
        return True
    
    def heal(self):
        self.hp = min(self.max_hp, self.hp + 1)
    
    def upgrade_weapon(self):
        self.weapon_level = min(3, self.weapon_level + 1)
    
    def activate_shield(self):
        self.shield = True
        self.shield_time = 600  # 10秒

# --- 游戏主类 ---

class ShooterGame:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Shooter")
        self.clock = pygame.time.Clock()
        
        # 字体
        self.font_large = pygame.font.SysFont('simhei', 48)
        self.font_medium = pygame.font.SysFont('simhei', 32)
        self.font_small = pygame.font.SysFont('simhei', 20)
        
        # 游戏状态
        self.reset_game()
        
        # 背景星星
        self.stars = [Star() for _ in range(50)]
    
    def reset_game(self):
        self.player = Player()
        self.bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.powerups = []
        self.particles = []
        self.score = 0
        self.wave = 1
        self.enemy_spawn_timer = 0
        self.game_over = False
        self.paused = False
        self.boss_fight = False
    
    def spawn_enemy(self):
        """生成敌机"""
        # 根据波数决定敌机类型
        if self.wave % 5 == 0 and not self.boss_fight:
            # Boss战
            self.boss_fight = True
            return
        
        # 随机生成普通敌机
        weights = {'small': 60, 'medium': 30, 'large': 10}
        enemy_type = random.choices(list(weights.keys()), weights=list(weights.values()))[0]
        
        x = random.randint(40, SCREEN_WIDTH - 40)
        y = -50
        
        enemy = Enemy(enemy_type, x, y)
        
        # 添加横向移动
        if enemy_type == 'medium':
            enemy.speed_x = random.choice([-1, 1]) * random.uniform(0.5, 1.5)
        
        self.enemies.append(enemy)
    
    def create_explosion(self, x, y, color, count=15):
        """创建爆炸效果"""
        for _ in range(count):
            self.particles.append(Particle(x, y, color))
    
    def update(self):
        """更新游戏逻辑"""
        if self.game_over or self.paused:
            return
        
        keys = pygame.key.get_pressed()
        self.player.update(keys)
        
        # 自动射击
        new_bullets = self.player.shoot()
        self.bullets.extend(new_bullets)
        
        # 更新背景星星
        for star in self.stars:
            star.update()
        
        # 更新子弹
        for bullet in self.bullets[:]:
            bullet.update()
            if not bullet.active:
                self.bullets.remove(bullet)
        
        for bullet in self.enemy_bullets[:]:
            bullet.update()
            if not bullet.active:
                self.enemy_bullets.remove(bullet)
        
        # 更新敌机
        for enemy in self.enemies[:]:
            enemy.update()
            
            # 敌机射击
            if enemy.can_shoot() and enemy.y > 0:
                self.enemy_bullets.append(
                    Bullet(enemy.x, enemy.y + enemy.radius, ENEMY_BULLET_SPEED, False)
                )
            
            if not enemy.active:
                self.enemies.remove(enemy)
        
        # 更新道具
        for powerup in self.powerups[:]:
            powerup.update()
            if not powerup.active:
                self.powerups.remove(powerup)
        
        # 更新粒子
        for particle in self.particles[:]:
            particle.update()
            if particle.is_dead():
                self.particles.remove(particle)
        
        # 碰撞检测 - 玩家子弹击中敌机
        for bullet in self.bullets[:]:
            for enemy in self.enemies[:]:
                if check_collision(bullet, enemy):
                    bullet.active = False
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    
                    if enemy.take_damage(bullet.damage):
                        self.create_explosion(enemy.x, enemy.y, enemy.config['color'])
                        self.score += enemy.config['score']
                        
                        # 随机掉落道具
                        if random.random() < 0.15:
                            self.powerups.append(PowerUp(enemy.x, enemy.y))
                    break
        
        # 碰撞检测 - 敌机子弹击中玩家
        for bullet in self.enemy_bullets[:]:
            if check_collision(bullet, self.player):
                bullet.active = False
                if bullet in self.enemy_bullets:
                    self.enemy_bullets.remove(bullet)
                
                if self.player.take_damage():
                    self.create_explosion(self.player.x, self.player.y, COLORS['player'], 30)
                
                if not self.player.active:
                    self.game_over = True
                break
        
        # 碰撞检测 - 玩家撞击敌机
        for enemy in self.enemies[:]:
            if check_collision(self.player, enemy):
                if self.player.take_damage():
                    self.create_explosion(self.player.x, self.player.y, COLORS['player'], 30)
                
                enemy.take_damage(10)  # 撞击对敌机造成伤害
                
                if not self.player.active:
                    self.game_over = True
        
        # 碰撞检测 - 玩家拾取道具
        for powerup in self.powerups[:]:
            if check_collision(self.player, powerup):
                powerup.active = False
                if powerup in self.powerups:
                    self.powerups.remove(powerup)
                
                if powerup.type == 'health':
                    self.player.heal()
                elif powerup.type == 'weapon':
                    self.player.upgrade_weapon()
                elif powerup.type == 'shield':
                    self.player.activate_shield()
                
                self.score += 50
        
        # 生成敌机
        self.enemy_spawn_timer += 1
        spawn_interval = max(30, 90 - self.wave * 2)
        if self.enemy_spawn_timer >= spawn_interval:
            self.enemy_spawn_timer = 0
            self.spawn_enemy()
        
        # 波数进度
        if self.score > self.wave * 500:
            self.wave += 1
    
    def draw(self):
        """渲染画面"""
        # 背景
        self.screen.fill(COLORS['bg'])
        
        # 绘制星星
        for star in self.stars:
            star.draw(self.screen)
        
        if not self.game_over:
            # 绘制道具
            for powerup in self.powerups:
                powerup.draw(self.screen)
            
            # 绘制子弹
            for bullet in self.bullets:
                bullet.draw(self.screen)
            for bullet in self.enemy_bullets:
                bullet.draw(self.screen)
            
            # 绘制敌机
            for enemy in self.enemies:
                enemy.draw(self.screen)
            
            # 绘制玩家
            if self.player.active:
                self.player.draw(self.screen)
            
            # 绘制粒子
            for particle in self.particles:
                particle.draw(self.screen)
            
            # UI
            self.draw_ui()
        else:
            self.draw_game_over()
        
        pygame.display.flip()
    
    def draw_ui(self):
        """绘制用户界面"""
        # 半透明背景
        ui_surface = pygame.Surface((SCREEN_WIDTH, 60), pygame.SRCALPHA)
        ui_surface.fill(COLORS['ui_bg'])
        self.screen.blit(ui_surface, (0, 0))
        
        # 分数
        score_text = self.font_medium.render(f"分数: {self.score}", True, COLORS['text'])
        self.screen.blit(score_text, (10, 10))
        
        # 波数
        wave_text = self.font_medium.render(f"波数: {self.wave}", True, COLORS['text_highlight'])
        self.screen.blit(wave_text, (SCREEN_WIDTH // 2 - wave_text.get_width() // 2, 10))
        
        # 生命值
        hp_text = self.font_medium.render(f"生命: {self.player.hp}/{self.player.max_hp}", True, (255, 100, 100))
        self.screen.blit(hp_text, (SCREEN_WIDTH - hp_text.get_width() - 10, 10))
        
        # 武器等级
        weapon_text = self.font_small.render(f"武器 Lv.{self.player.weapon_level}", True, COLORS['powerup_weapon'])
        self.screen.blit(weapon_text, (10, 70))
        
        # 护盾状态
        if self.player.shield:
            shield_text = self.font_small.render("护盾激活", True, COLORS['powerup_shield'])
            self.screen.blit(shield_text, (10, 90))
        
        # 操作提示
        hint_text = self.font_small.render("WASD/方向键移动 | P暂停", True, COLORS['text_dim'])
        self.screen.blit(hint_text, (SCREEN_WIDTH - hint_text.get_width() - 10, SCREEN_HEIGHT - 25))
    
    def draw_game_over(self):
        """绘制游戏结束画面"""
        # 半透明遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # 游戏结束文字
        over_text = self.font_large.render("游戏结束", True, (255, 80, 80))
        self.screen.blit(over_text, 
                        (SCREEN_WIDTH // 2 - over_text.get_width() // 2, SCREEN_HEIGHT // 2 - 100))
        
        # 最终分数
        score_text = self.font_medium.render(f"最终分数: {self.score}", True, COLORS['text'])
        self.screen.blit(score_text, 
                        (SCREEN_WIDTH // 2 - score_text.get_width() // 2, SCREEN_HEIGHT // 2 - 20))
        
        # 波数
        wave_text = self.font_medium.render(f"到达波数: {self.wave}", True, COLORS['text_highlight'])
        self.screen.blit(wave_text, 
                        (SCREEN_WIDTH // 2 - wave_text.get_width() // 2, SCREEN_HEIGHT // 2 + 30))
        
        # 重新开始提示
        restart_text = self.font_small.render("按 R 重新开始 | 按 ESC 退出", True, COLORS['text_dim'])
        self.screen.blit(restart_text, 
                        (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 100))
    
    def handle_events(self):
        """处理输入事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                
                if event.key == pygame.K_p:
                    self.paused = not self.paused
                
                if self.game_over:
                    if event.key == pygame.K_r:
                        self.reset_game()
        
        return True
    
    def run(self):
        """主游戏循环"""
        running = True
        
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
    def close(self):
        """关闭游戏"""
        pygame.quit()

# --- 外部调用接口 ---

def run():
    """外部调用接口"""
    game = ShooterGame()
    try:
        game.run()
    finally:
        game.close()
