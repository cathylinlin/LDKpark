"""简单的 Google 恐龙跳跃小游戏（基于 pygame 的最小实现）

运行：
	python -m LDKpark.games100.dinosaur

按 空格 或 上箭头 跳跃，按 `s` 蹲下，按 Escape 退出。

功能：使用 `assets/dinosaur/` 中的用户素材（奔跑 GIF、跳跃图、蹲下图、飞行物、障碍），实现：
- 碰撞后显示 Game Over，5 秒自动退出或按 R 重开。
- 记录死亡次数；当死亡次数 > 2 时尝试显示 `deadmoretime.jpg`。
"""

from __future__ import annotations

import random
import os
import glob
from typing import Optional
import pygame


# =====================
# 可调参数（节奏 / 物理 / 生成）
# =====================

# 窗口大小
WIDTH, HEIGHT = 1000, 300

# 地面基准线（角色与地面障碍的“脚底”y 坐标）
GROUND_Y = 220

# 目标帧率（clock.tick 使用）
TARGET_FPS = 60

# 跳跃物理
JUMP_VY = -520          # 起跳初速度（越小越“跳得高”，负数向上）
GRAVITY = 1200          # 重力加速度（越大越“下落快”）

# 最大跳跃段数：2 表示二段跳
MAX_JUMPS = 2

# 蹲跳：按住 S 蹲下时仍可跳跃（倍率>1 会跳得更高；设为 1.0 表示仅“允许蹲下起跳”）
CROUCH_JUMP_MULTIPLIER = 1.08

# 蹲下（高度变化）
CROUCH_HEIGHT_RATIO = 0.6   # 蹲下时高度占站立高度比例
CROUCH_LERP_SPEED = 8.0     # 蹲下/起立的插值速度（越大越快）

# 游戏节奏（速度/生成间隔）
SPEED_BASE = 480            # 初始地面速度（像素/秒）
SPEED_PER_SCORE = 3         # 分数每 +1，速度额外增加多少

SPAWN_FACTOR_MIN = 0.55     # 生成间隔缩放下限（防止快到不可玩）
SPAWN_FACTOR_PER_SCORE = 0.003  # 分数越高，生成越密集的程度
SPAWN_INTERVAL_MIN = 0.7    # 基础最短生成间隔（秒）
SPAWN_INTERVAL_MAX = 1.2    # 基础最长生成间隔（秒）

# 动画帧（奔跑）
MAX_RUN_FRAMES = 30         # 奔跑帧最多使用多少张（避免帧太多导致加载慢）

# 空中按 S 蹲下时的绘制偏移（越大越“更高”）
AIR_CROUCH_Y_OFFSET = 12


class Dino:
	"""恐龙玩家对象：管理跳跃/蹲下状态以及碰撞盒。"""

	def __init__(self):
		self.x = 80
		self.y = GROUND_Y
		self.vy = 0
		self.jumping = False
		self.jumps_used = 0
		self.crouching = False
		self.width = 44
		self.height = 44
		# for smooth crouch animation
		self.current_height = float(self.height)
		self.target_height = float(self.height)

	def rect(self):
		"""当前碰撞矩形（基于平滑高度 current_height）。"""
		h = int(self.current_height)
		return pygame.Rect(self.x, self.y - h, self.width, h)

	def update(self, dt):
		"""更新物理状态（dt 为秒）。"""
		# physics for jump
		if self.jumping:
			self.vy += GRAVITY * dt
			self.y += self.vy * dt
			if self.y >= GROUND_Y:
				self.y = GROUND_Y
				self.vy = 0
				self.jumping = False
				self.jumps_used = 0

		# smooth crouch height interpolation (linear lerp)
		# target_height already set by crouch()
		self.current_height += (self.target_height - self.current_height) * min(1.0, CROUCH_LERP_SPEED * dt)

	def jump(self):
		"""触发跳跃。

		- 支持二段跳：空中允许再跳一次
		- 支持“蹲跳”：按住 S 蹲下时也可以跳
		"""
		if self.jumps_used >= MAX_JUMPS:
			return
		mult = CROUCH_JUMP_MULTIPLIER if self.crouching else 1.0
		self.vy = float(JUMP_VY) * float(mult)
		self.jumping = True
		self.jumps_used += 1

	def crouch(self, on: bool):
		"""切换蹲下状态（on=True 蹲下；False 起立）。"""
		self.crouching = bool(on)
		# set target height for smooth transition
		if self.crouching:
			self.target_height = float(self.height * CROUCH_HEIGHT_RATIO)
		else:
			self.target_height = float(self.height)


class Animation:
	"""简单帧动画：按 fps 播放 Surface 列表。"""

	def __init__(self, frames, fps=12):
		self.frames = frames or []
		self.index = 0
		self.timer = 0.0
		self.frame_time = 1.0 / max(1, fps)

	def reset(self):
		"""重置到第 0 帧，常用于状态切换。"""
		self.index = 0
		self.timer = 0.0

	def update(self, dt):
		"""推进动画（dt 为秒）。"""
		if not self.frames:
			return
		self.timer += dt
		while self.timer >= self.frame_time:
			self.timer -= self.frame_time
			self.index = (self.index + 1) % len(self.frames)

	def current(self):
		"""返回当前帧 Surface；无帧时返回 None。"""
		if not self.frames:
			return None
		return self.frames[self.index]


def prepare_surface(surface):
	"""对素材 Surface 做“尽力而为”的预处理：

	- 若无 per-pixel alpha，则尝试用左上角像素设为 colorkey（去背景）
	- 使用 bounding_rect 裁剪空白边缘（减少碰撞误差/缩放浪费）
	"""
	if surface is None:
		return None
	# apply a color key from the top-left pixel only when there is no per-pixel alpha
	# (avoid breaking PNGs that already have transparency)
	try:
		has_srcalpha = bool(surface.get_flags() & pygame.SRCALPHA)
	except Exception:
		has_srcalpha = False
	if not has_srcalpha:
		try:
			colorkey = surface.get_at((0, 0))
			surface.set_colorkey(colorkey)
		except Exception:
			pass
	# crop to bounding rect to reduce empty background
	try:
		rect = surface.get_bounding_rect()
		surface = surface.subsurface(rect).copy()
	except Exception:
		pass
	return surface


def load_frames_from_file(path, default_fps=12):
	"""从单文件读取帧动画。

	优先尝试 Pillow 读取 GIF 等多帧文件；失败则回退为单帧图片。
	返回 (frames, fps)。
	"""
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
	"""按 glob 路径列表加载帧序列（加载失败的文件会被跳过）。"""
	frames = []
	for p in sorted(patterns):
		try:
			frames.append(pygame.image.load(p).convert_alpha())
		except Exception:
			pass
	return frames


def _evenly_pick(seq, k):
	"""在 seq 中均匀取 k 个元素（用于抽帧）。"""
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
	"""从帧序列的前 1/3、中 1/3、后 1/3 分段抽样。

	目的：避免只取中段导致动作变化不明显。
	"""
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
	"""障碍物：地面或空中（飞行）两种类型。"""

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
		"""障碍物碰撞盒（比显示略小一点，减少背景导致误碰）。"""
		pad = 6
		if self.kind == 'ground':
			return pygame.Rect(self.x + pad, GROUND_Y - self.h + pad, self.w - pad * 2, self.h - pad * 2)
		else:
			return pygame.Rect(self.x + pad, self.y - self.h + pad, self.w - pad * 2, self.h - pad * 2)

	def update(self, speed, dt):
		"""按当前速度向左移动（speed: px/s, dt: s）。"""
		self.x -= speed * dt


def run():
	"""
	启动恐龙小游戏。
	这是一个阻塞函数，会运行 pygame 主循环；窗口关闭/退出后函数才会返回。

	按键：
	- 空格 / 上箭头：跳跃
	- S：蹲下（可在空中触发，用于“空中蹲下更高”的姿态展示）
	- R：Game Over 后重新开始
	- Esc：退出
	"""
	pygame.init()
	screen = pygame.display.set_mode((WIDTH, HEIGHT))
	clock = pygame.time.Clock()
	font = pygame.font.SysFont(None, 28)

	# load assets (best-effort)
	assets = {}  # 资源字典：动画/贴图
	base = os.path.join('assets', 'dinosaur')
	def try_load(path):
		"""尝试加载单张图片（失败返回 None）。"""
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
	max_frames = MAX_RUN_FRAMES
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

	dino = Dino()  # 玩家
	obstacles: list[Obstacle] = []  # 当前屏幕上的障碍物
	spawn_timer = 0.0  # 距离下次生成障碍的倒计时（秒）

	speed_base = SPEED_BASE  # 基础速度（px/s）
	speed = speed_base  # 实时速度（会随分数增长）
	score = 0.0  # 分数（随时间增加）

	running = True  # 主循环开关
	game_over = False  # 是否进入 Game Over
	game_over_time: Optional[int] = None  # Game Over 开始的时间戳（ms）
	death_count = 0  # 本次启动过程中的死亡次数

	last_spawn_type = None

	while running:
		dt = clock.tick(TARGET_FPS) / 1000.0
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
			# speed ramps up with score to increase pacing
			speed = speed_base + int(score) * SPEED_PER_SCORE
			spawn_timer -= dt
			if spawn_timer <= 0:
				# spawn faster over time, clamped to keep it playable
				factor = max(SPAWN_FACTOR_MIN, 1.0 - (score * SPAWN_FACTOR_PER_SCORE))
				spawn_timer = random.uniform(SPAWN_INTERVAL_MIN * factor, SPAWN_INTERVAL_MAX * factor)
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
		screen.fill((255, 255, 255))
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
			# priority: crouch > jump > run
			run_anim = assets.get('run_anim')
			jump_anim = assets.get('jump_anim')
			crouch_anim = assets.get('crouch_anim')

			if dino.crouching and crouch_anim:
				crouch_anim.update(dt)
				c = crouch_anim.current()
				if c is not None:
					c = pygame.transform.smoothscale(c, (dino.width, int(dino.current_height)))
					cr = c.get_rect()
					# when crouching in air, draw slightly higher than the jump pose
					y_offset = AIR_CROUCH_Y_OFFSET if dino.jumping else 0
					cr.midbottom = (dino.x + dino.width // 2, dino.y - y_offset)
					screen.blit(c, cr)
				# reset other animations when crouch is active
				if jump_anim:
					jump_anim.reset()
				if run_anim:
					run_anim.reset()
			elif dino.jumping and jump_anim:
				jump_anim.update(dt)
				j = jump_anim.current()
				if j is not None:
					j = pygame.transform.smoothscale(j, (dino.width, dino.height))
					jr = j.get_rect()
					jr.midbottom = (dino.x + dino.width // 2, dino.y)
					screen.blit(j, jr)
				if run_anim:
					run_anim.reset()
				if crouch_anim:
					crouch_anim.reset()
			else:
				if run_anim:
					run_anim.update(dt)
					frame = run_anim.current()
					if frame is not None:
						f = pygame.transform.smoothscale(frame, (dino.width, int(dino.current_height)))
						fr = f.get_rect()
						fr.midbottom = (dino.x + dino.width // 2, dino.y)
						screen.blit(f, fr)
				if jump_anim:
					jump_anim.reset()
				if crouch_anim:
					crouch_anim.reset()

		text = font.render(f"Score: {int(score)}", True, (10, 10, 10))
		screen.blit(text, (10, 10))

		pygame.display.flip()

		# when game over, show overlay and handle restart/auto-exit
		if game_over:
			go_text = font.render("GAME OVER - Press R to restart or wait 5s", True, (200, 0, 0))
			go_rect = go_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
			screen.blit(go_text, go_rect)
			pygame.display.flip()

			now = pygame.time.get_ticks()
			# type guard: game_over_time may be None in type checker's view
			if game_over_time is None:
				game_over_time = now
			if now - game_over_time >= 5000:
				running = False
				break

			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					running = False
					break
				elif event.type == pygame.KEYDOWN:
					if event.key == pygame.K_r:
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


