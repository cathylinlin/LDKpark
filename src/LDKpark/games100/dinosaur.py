"""简单的 Google 恐龙跳跃小游戏（基于 pygame 的最小实现）

运行：
	python -m LDKpark.games100.dinosaur

按 空格 或 上箭头 跳跃，按 `s` 蹲下，按 Escape 退出。

功能：使用 `assets/dinosaur/` 中的用户素材（奔跑 GIF、跳跃图、蹲下图、飞行物、障碍、音乐），实现：
- 碰撞后显示 Game Over，5 秒自动退出或按空格重开。
- 记录死亡次数；当死亡次数 > 2 时尝试显示 `deadmoretime.jpg`。
"""
import random
import os
import glob
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
		# for smooth crouch animation
		self.current_height = float(self.height)
		self.target_height = float(self.height)

	def rect(self):
		h = int(self.current_height)
		return pygame.Rect(self.x, self.y - h, self.width, h)

	def update(self, dt):
		# physics for jump
		if self.jumping:
			self.vy += 1200 * dt
			self.y += self.vy * dt
			if self.y >= GROUND_Y:
				self.y = GROUND_Y
				self.vy = 0
				self.jumping = False

		# smooth crouch height interpolation (linear lerp)
		# target_height already set by crouch()
		lerp_speed = 8.0  # higher = faster transition
		self.current_height += (self.target_height - self.current_height) * min(1.0, lerp_speed * dt)

	def jump(self):
		if not self.jumping and not self.crouching:
			self.vy = -520
			self.jumping = True

	def crouch(self, on: bool):
		self.crouching = bool(on)
		# set target height for smooth transition
		if self.crouching:
			self.target_height = float(self.height * 0.6)
		else:
			self.target_height = float(self.height)


class Animation:
	def __init__(self, frames, fps=12):
		self.frames = frames or []
		self.index = 0
		self.timer = 0.0
		self.frame_time = 1.0 / max(1, fps)

	def reset(self):
		self.index = 0
		self.timer = 0.0

	def update(self, dt):
		if not self.frames:
			return
		self.timer += dt
		while self.timer >= self.frame_time:
			self.timer -= self.frame_time
			self.index = (self.index + 1) % len(self.frames)

	def current(self):
		if not self.frames:
			return None
		return self.frames[self.index]


def prepare_surface(surface):
	if surface is None:
		return None
	# apply a color key from the top-left pixel if no alpha
	if surface.get_alpha() is None:
		colorkey = surface.get_at((0, 0))
		surface.set_colorkey(colorkey)
	# crop to bounding rect to reduce empty background
	try:
		rect = surface.get_bounding_rect()
		surface = surface.subsurface(rect).copy()
	except Exception:
		pass
	return surface


def load_frames_from_file(path, default_fps=12):
	frames = []
	fps = default_fps
	try:
		from PIL import Image, ImageSequence
		im = Image.open(path)
		durations = []
		for frame in ImageSequence.Iterator(im):
			durations.append(frame.info.get("duration", 100))
			frame = frame.convert("RGBA")
			data = frame.tobytes()
			surf = pygame.image.fromstring(data, frame.size, "RGBA").convert_alpha()
			frames.append(surf)
		if durations:
			avg_ms = sum(durations) / max(1, len(durations))
			fps = max(1, int(1000 / max(1, avg_ms)))
	except Exception:
		# fallback: single frame
		try:
			frames = [pygame.image.load(path).convert_alpha()]
		except Exception:
			frames = []
	return frames, fps


def load_frames_from_glob(patterns):
	frames = []
	for p in sorted(patterns):
		try:
			frames.append(pygame.image.load(p).convert_alpha())
		except Exception:
			pass
	return frames


def _evenly_pick(seq, k):
	if k <= 0 or not seq:
		return []
	n = len(seq)
	if n <= k:
		return list(seq)
	if k == 1:
		return [seq[n // 2]]
	idxs = [int(round(i * (n - 1) / (k - 1))) for i in range(k)]
	# de-duplicate indices while preserving order
	seen = set()
	uniq_idxs = []
	for idx in idxs:
		if idx not in seen:
			seen.add(idx)
			uniq_idxs.append(idx)
	# If rounding caused duplicates, fill missing indices from left to right.
	if len(uniq_idxs) < k:
		for idx in range(n):
			if idx in seen:
				continue
			seen.add(idx)
			uniq_idxs.append(idx)
			if len(uniq_idxs) >= k:
				break
	return [seq[i] for i in uniq_idxs]


def select_frames_start_middle_end(frames, start_count, middle_count, end_count):
	frames = list(frames or [])
	n = len(frames)
	if n == 0:
		return []
	third = max(1, n // 3)
	start_seg = frames[:third]
	mid_seg = frames[third:max(third + 1, 2 * third)]
	end_seg = frames[max(2 * third, 0):]
	selected = []
	selected.extend(_evenly_pick(start_seg, start_count))
	selected.extend(_evenly_pick(mid_seg, middle_count))
	selected.extend(_evenly_pick(end_seg, end_count))
	# final de-dup preserving order
	uniq = []
	seen_ids = set()
	for f in selected:
		fid = id(f)
		if fid in seen_ids:
			continue
		seen_ids.add(fid)
		uniq.append(f)
	return uniq


class Obstacle:
	def __init__(self, x, kind='ground', image=None):
		self.x = x
		self.kind = kind
		self.image = image
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
		pad = 6
		if self.kind == 'ground':
			return pygame.Rect(self.x + pad, GROUND_Y - self.h + pad, self.w - pad * 2, self.h - pad * 2)
		else:
			return pygame.Rect(self.x + pad, self.y - self.h + pad, self.w - pad * 2, self.h - pad * 2)

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

	# run animation: prefer extracted frames; fallback to gif or static
	frame_patterns = glob.glob(os.path.join(base, 'frames', 'run_*.png')) + glob.glob(os.path.join(base, 'frames', 'frame_*.png'))
	run_frames = load_frames_from_glob(frame_patterns)
	run_fps = 12
	if not run_frames:
		gif_path = os.path.join(base, 'sheets', 'taff-begining.gif')
		if os.path.exists(gif_path):
			run_frames, run_fps = load_frames_from_file(gif_path, default_fps=12)
	# if too many frames, sample from start/middle/end to preserve visible changes
	max_frames = 30
	if len(run_frames) > max_frames:
		base_count = max_frames // 3
		start_count = base_count
		middle_count = base_count
		end_count = max_frames - start_count - middle_count
		run_frames = select_frames_start_middle_end(run_frames, start_count, middle_count, end_count)
	assets['run_anim'] = Animation([prepare_surface(f) for f in run_frames], fps=run_fps)

	# jump and crouch animations (support animated jpg/gif if present)
	jump_path = os.path.join(base, 'sheets', 'mdtaff.jpg')
	jump_frames, jump_fps = load_frames_from_file(jump_path, default_fps=12)
	assets['jump_anim'] = Animation([prepare_surface(f) for f in jump_frames], fps=jump_fps)

	crouch_path = os.path.join(base, 'face', 'taff-laugh.jpg')
	crouch_frames, crouch_fps = load_frames_from_file(crouch_path, default_fps=12)
	assets['crouch_anim'] = Animation([prepare_surface(f) for f in crouch_frames], fps=crouch_fps)

	assets['obstacle_img'] = prepare_surface(try_load(os.path.join(base, 'obstacles', 'xianrenzhang.png')))
	assets['flying_img'] = prepare_surface(try_load(os.path.join(base, 'flying', 'chucaoflying.png')))
	dead_image = prepare_surface(try_load(os.path.join(base, 'deadmoretime.jpg')))

	# music removed by request

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
				if kind == 'ground':
					obstacles.append(Obstacle(WIDTH + 40, kind=kind, image=assets.get('obstacle_img')))
				else:
					obstacles.append(Obstacle(WIDTH + 40, kind=kind, image=assets.get('flying_img')))
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
			if ob.kind == 'ground' and ob.image is not None:
				img = pygame.transform.smoothscale(ob.image, (ob.w, ob.h))
				img_rect = img.get_rect()
				img_rect.midbottom = (int(ob.x + ob.w/2), GROUND_Y)
				screen.blit(img, img_rect)
			elif ob.kind == 'flying' and ob.image is not None:
				img = pygame.transform.smoothscale(ob.image, (ob.w, ob.h))
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
			# run animation frames if available and on ground
			run_anim = assets.get('run_anim')
			if not dino.jumping and not dino.crouching and run_anim:
				run_anim.update(dt)
				frame = run_anim.current()
				if frame is not None:
					f = pygame.transform.smoothscale(frame, (dino.width, int(dino.current_height)))
					fr = f.get_rect()
					fr.midbottom = (dino.x + dino.width // 2, dino.y)
					screen.blit(f, fr)
			else:
				if run_anim:
					run_anim.reset()
			# jumping overlay
			jump_anim = assets.get('jump_anim')
			if dino.jumping and jump_anim:
				jump_anim.update(dt)
				j = jump_anim.current()
				if j is not None:
					j = pygame.transform.smoothscale(j, (dino.width, dino.height))
					jr = j.get_rect()
					jr.midbottom = (dino.x + dino.width // 2, dino.y)
					screen.blit(j, jr)
			else:
				if jump_anim:
					jump_anim.reset()
			# crouch overlay
			crouch_anim = assets.get('crouch_anim')
			if dino.crouching and crouch_anim:
				crouch_anim.update(dt)
				c = crouch_anim.current()
				if c is not None:
					c = pygame.transform.smoothscale(c, (dino.width, int(dino.current_height)))
					cr = c.get_rect()
					cr.midbottom = (dino.x + dino.width // 2, dino.y)
					screen.blit(c, cr)
			else:
				if crouch_anim:
					crouch_anim.reset()

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


