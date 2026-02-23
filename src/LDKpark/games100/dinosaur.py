"""简单的 Google 恐龙跳跃小游戏（基于 pygame 的最小实现）

运行：
	python -m LDKpark.games100.dinosaur

按 空格 或 上箭头 跳跃，按 `s` 蹲下，按 `m` 切换音乐，按 Escape 退出。

功能：使用 `assets/dinosaur/` 中的用户素材（奔跑 GIF、跳跃图、蹲下图、飞行物、障碍、音乐），实现：
- 碰撞后显示 Game Over，5 秒自动退出或按空格重开。
- 记录死亡次数；当死亡次数 > 2 时尝试显示 `deadmoretime.jpg`。
"""
import sys
import random
import os
import pygame


WIDTH, HEIGHT = 1000, 300
GROUND_Y = 220


class Dino:
	def __init__(self):
		self.x = 80
		self.y = GROUND_Y
		self.vy = 0
		self.jumping = False
		self.crouching = False
		self.width = 44
		self.height = 44

	def rect(self):
		h = self.height
		if self.crouching:
			h = int(self.height * 0.6)
		return pygame.Rect(self.x, self.y - h, self.width, h)

	def update(self, dt):
		if self.jumping:
			self.vy += 1200 * dt
			self.y += self.vy * dt
			if self.y >= GROUND_Y:
				self.y = GROUND_Y
				self.vy = 0
				self.jumping = False

	def jump(self):
		if not self.jumping and not self.crouching:
			self.vy = -520
			self.jumping = True

	def crouch(self, on: bool):
		self.crouching = bool(on)


class Obstacle:
	def __init__(self, x, kind='ground'):
		self.x = x
		self.kind = kind
		if kind == 'ground':
			self.w = random.randint(30, 60)
			self.h = random.randint(30, 60)
			self.y = GROUND_Y
		else:
			self.w = 48
			self.h = 32
			# random flying height
			self.y = GROUND_Y - random.randint(80, 130)

	def rect(self):
		if self.kind == 'ground':
			return pygame.Rect(self.x, GROUND_Y - self.h, self.w, self.h)
		else:
			return pygame.Rect(self.x, self.y - self.h, self.w, self.h)

	def update(self, speed, dt):
		self.x -= speed * dt


def run():
	pygame.init()
	screen = pygame.display.set_mode((WIDTH, HEIGHT))
	clock = pygame.time.Clock()
	font = pygame.font.SysFont(None, 28)

	# load assets (best-effort)
	assets = {}
	base = os.path.join('assets', 'dinosaur')
	def try_load(path):
		try:
			return pygame.image.load(path).convert_alpha()
		except Exception:
			return None

	assets['run_gif'] = try_load(os.path.join(base, 'sheets', 'taff-begining.gif'))
	assets['jump_img'] = try_load(os.path.join(base, 'sheets', 'mdtaff.jpg'))
	assets['crouch_img'] = try_load(os.path.join(base, 'face', 'taff-laugh.jpg'))
	assets['obstacle_img'] = try_load(os.path.join(base, 'obstacles', 'xianrenzhang.png'))
	assets['flying_img'] = try_load(os.path.join(base, 'flying', 'chucaoflying.png'))
	dead_image = try_load(os.path.join(base, 'deadmoretime.jpg'))

	# music
	music_on = False
	try:
		pygame.mixer.init()
		music_path = os.path.join(base, 'sfx', 'taff-begining.track-0.m4a')
		if os.path.exists(music_path):
			pygame.mixer.music.load(music_path)
			pygame.mixer.music.set_volume(0.6)
			pygame.mixer.music.play(-1)
			music_on = True
	except Exception:
		music_on = False

	dino = Dino()
	obstacles = []
	spawn_timer = 0.0
	speed = 360
	score = 0
	running = True
	game_over = False
	game_over_time = None
	death_count = 0

	last_spawn_type = None

	while running:
		dt = clock.tick(60) / 1000.0
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			elif event.type == pygame.KEYDOWN:
				if event.key in (pygame.K_SPACE, pygame.K_UP):
					dino.jump()
				elif event.key == pygame.K_s:
					dino.crouch(True)
				elif event.key == pygame.K_m:
					# toggle music pause/unpause
					if music_on and pygame.mixer.get_init():
						if pygame.mixer.music.get_busy():
							pygame.mixer.music.pause()
						else:
							pygame.mixer.music.unpause()
				elif event.key == pygame.K_ESCAPE:
					running = False
			elif event.type == pygame.KEYUP:
				if event.key == pygame.K_s:
					dino.crouch(False)

		if not game_over:
			spawn_timer -= dt
			if spawn_timer <= 0:
				spawn_timer = random.uniform(0.9, 1.6)
				# decide ground or flying, avoid repeating same type
				if last_spawn_type == 'ground':
					kind = 'flying' if random.random() < 0.75 else 'ground'
				elif last_spawn_type == 'flying':
					kind = 'ground' if random.random() < 0.75 else 'flying'
				else:
					kind = 'ground' if random.random() < 0.7 else 'flying'
				obstacles.append(Obstacle(WIDTH + 40, kind=kind))
				last_spawn_type = kind

			dino.update(dt)
			for ob in obstacles:
				ob.update(speed, dt)

			obstacles = [o for o in obstacles if o.x + o.w > -20]

			# collision detection
			for ob in obstacles:
				if dino.rect().colliderect(ob.rect()):
					game_over = True
					game_over_time = pygame.time.get_ticks()
					death_count += 1
					break

			score += dt * 10

		# draw
		screen.fill((240, 240, 240))
		pygame.draw.line(screen, (0, 0, 0), (0, GROUND_Y + 1), (WIDTH, GROUND_Y + 1), 2)

		# draw obstacles with images when available
		for ob in obstacles:
			if ob.kind == 'ground' and assets.get('obstacle_img'):
				img = pygame.transform.smoothscale(assets['obstacle_img'], (ob.w, ob.h))
				img_rect = img.get_rect()
				img_rect.midbottom = (int(ob.x + ob.w/2), GROUND_Y)
				screen.blit(img, img_rect)
			elif ob.kind == 'flying' and assets.get('flying_img'):
				img = pygame.transform.smoothscale(assets['flying_img'], (ob.w, ob.h))
				img_rect = img.get_rect()
				img_rect.midbottom = (int(ob.x + ob.w/2), ob.y)
				screen.blit(img, img_rect)
			else:
				pygame.draw.rect(screen, (80, 80, 80), ob.rect())

		# draw dino: show special images for jump/crouch if available
		if game_over and death_count > 2 and dead_image is not None:
			img = pygame.transform.smoothscale(dead_image, (dino.width, dino.height))
			img_rect = img.get_rect()
			img_rect.midbottom = (dino.x + dino.width // 2, dino.y)
			screen.blit(img, img_rect)
		else:
			# base body
			pygame.draw.rect(screen, (40, 40, 40), dino.rect())
			# jumping overlay
			if dino.jumping and assets.get('jump_img'):
				j = pygame.transform.smoothscale(assets['jump_img'], (dino.width, dino.height))
				jr = j.get_rect()
				jr.midbottom = (dino.x + dino.width // 2, dino.y)
				screen.blit(j, jr)
			# crouch overlay
			if dino.crouching and assets.get('crouch_img'):
				c = pygame.transform.smoothscale(assets['crouch_img'], (dino.width, int(dino.height*0.6)))
				cr = c.get_rect()
				cr.midbottom = (dino.x + dino.width // 2, dino.y)
				screen.blit(c, cr)

		text = font.render(f"Score: {int(score)}", True, (10, 10, 10))
		screen.blit(text, (10, 10))

		pygame.display.flip()

		# when game over, show overlay and handle restart/auto-exit
		if game_over:
			go_text = font.render("GAME OVER - Press Space to restart or wait 5s", True, (200, 0, 0))
			go_rect = go_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
			screen.blit(go_text, go_rect)
			pygame.display.flip()

			now = pygame.time.get_ticks()
			if now - game_over_time >= 5000:
				running = False
				break

			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					running = False
					break
				elif event.type == pygame.KEYDOWN:
					if event.key == pygame.K_SPACE:
						# restart but keep death_count
						dino = Dino()
						obstacles = []
						spawn_timer = 0.0
						score = 0
						game_over = False
						game_over_time = None
						last_spawn_type = None
						break
					elif event.key == pygame.K_ESCAPE:
						running = False
						break

	pygame.quit()


if __name__ == "__main__":
	run()


