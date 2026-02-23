"""简单的 Google 恐龙跳跃小游戏（基于 pygame 的最小实现）

运行：
    python -m LDKpark.games100.dinosaur

按 空格 或 上箭头 跳跃，按 Escape 退出。

"""
import sys
import random
import pygame


WIDTH, HEIGHT = 800, 200
GROUND_Y = 150


class Dino:
    def __init__(self):
        self.x = 50
        self.y = GROUND_Y
        self.vy = 0
        self.jumping = False
        self.size = 40

    def rect(self):
        return pygame.Rect(self.x, self.y - self.size, self.size, self.size)

    def update(self, dt):
        if self.jumping:
            self.vy += 1200 * dt
            self.y += self.vy * dt
            if self.y >= GROUND_Y:
                self.y = GROUND_Y
                self.vy = 0
                self.jumping = False

    def jump(self):
        if not self.jumping:
            self.vy = -450
            self.jumping = True


class Obstacle:
    def __init__(self, x):
        self.x = x
        self.w = random.randint(20, 30)
        self.h = random.randint(30, 50)

    def rect(self):
        return pygame.Rect(self.x, GROUND_Y - self.h, self.w, self.h)

    def update(self, speed, dt):
        self.x -= speed * dt


def run():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)

    dino = Dino()
    obstacles = []
    spawn_timer = 0.0
    speed = 300
    score = 0
    running = True
    game_over = False
    game_over_time = None
    death_count = 0
    dead_image = None

    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_UP):
                    dino.jump()
                elif event.key == pygame.K_ESCAPE:
                    running = False

        if not game_over:
            spawn_timer -= dt
            if spawn_timer <= 0:
                spawn_timer = random.uniform(0.8, 1.6)
                obstacles.append(Obstacle(WIDTH + 20))

            dino.update(dt)
            for ob in obstacles:
                ob.update(speed, dt)

            obstacles = [o for o in obstacles if o.x + o.w > -10]

            # collision
            for ob in obstacles:
                if dino.rect().colliderect(ob.rect()):
                    # enter game over state
                    game_over = True
                    game_over_time = pygame.time.get_ticks()
                    death_count += 1
                    # try load special dead image when death_count > 2
                    if death_count > 2 and dead_image is None:
                        try:
                            dead_image = pygame.image.load("assets/dinosaur/deadmoretime.jpg").convert_alpha()
                        except Exception:
                            dead_image = None
                    break

            score += dt * 10

        screen.fill((240, 240, 240))
        pygame.draw.line(screen, (0, 0, 0), (0, GROUND_Y + 1), (WIDTH, GROUND_Y + 1), 2)

        # draw dino (use image if in special dead state)
        if game_over and death_count > 2 and dead_image is not None:
            # draw dead image at dino position
            img = pygame.transform.smoothscale(dead_image, (dino.size, dino.size))
            img_rect = img.get_rect()
            img_rect.midbottom = (dino.x + dino.size // 2, dino.y)
            screen.blit(img, img_rect)
        else:
            pygame.draw.rect(screen, (40, 40, 40), dino.rect())
        for ob in obstacles:
            pygame.draw.rect(screen, (80, 80, 80), ob.rect())

        text = font.render(f"Score: {int(score)}", True, (10, 10, 10))
        screen.blit(text, (10, 10))

        pygame.display.flip()

        # when game over, show overlay and handle restart/auto-exit
        if game_over:
            # overlay
            go_text = font.render("GAME OVER - Press Space to restart or wait 5s", True, (200, 0, 0))
            go_rect = go_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(go_text, go_rect)
            pygame.display.flip()

            # poll for restart or auto-exit
            now = pygame.time.get_ticks()
            # check for 5 seconds elapsed
            if now - game_over_time >= 5000:
                running = False
                break

            # allow pressing space to restart
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        # restart game state but keep death_count
                        dino = Dino()
                        obstacles = []
                        spawn_timer = 0.0
                        score = 0
                        game_over = False
                        game_over_time = None
                        break
                    elif event.key == pygame.K_ESCAPE:
                        running = False
                        break

    pygame.quit()


if __name__ == "__main__":
    run()
