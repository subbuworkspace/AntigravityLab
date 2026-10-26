"""
Snake & Ball Arcade Game
A rich, modern Python arcade game using Tkinter.
Features:
- Smooth fluid snake movement with directional eyes and animations
- 3D-shaded energy balls (Regular Red Ball & Golden Bonus Ball)
- Particle effects & floating score popups
- Optional Bouncing Hazard Ball mode (Snake vs Bouncing Ball!)
- Non-blocking 8-bit retro sound effects (Windows winsound)
- Local high score persistence
- Difficulty presets (Easy, Normal, Hard)
- Pause, restart, and sound toggles
"""

import json
import math
import os
import random
import sys
import threading
import tkinter as tk
from tkinter import font as tkfont

# Optional winsound for retro audio effects
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

# ================= Game Configuration =================
CELL_SIZE = 24
COLS = 28
ROWS = 24
CANVAS_WIDTH = COLS * CELL_SIZE   # 672 px
CANVAS_HEIGHT = ROWS * CELL_SIZE  # 576 px

COLOR_BG = "#13141f"
COLOR_GRID = "#1a1c2d"
COLOR_HEADER_BG = "#0c0d14"
COLOR_SNAKE_HEAD = "#00e676"
COLOR_SNAKE_BODY_1 = "#00c853"
COLOR_SNAKE_BODY_2 = "#009624"
COLOR_FOOD_BALL = "#ff3366"
COLOR_FOOD_GLOW = "#ff6b8b"
COLOR_BONUS_BALL = "#ffd700"
COLOR_BONUS_GLOW = "#fff3a1"
COLOR_HAZARD_BALL = "#a855f7"
COLOR_HAZARD_GLOW = "#c084fc"
COLOR_TEXT_PRIMARY = "#f8fafc"
COLOR_TEXT_MUTED = "#94a3b8"
COLOR_ACCENT = "#38bdf8"

HIGH_SCORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "highscore.json")


class SoundManager:
    """Non-blocking 8-bit sound synthesizer using winsound."""
    def __init__(self, enabled=True):
        self.enabled = enabled and HAS_WINSOUND

    def _play(self, notes):
        if not self.enabled:
            return
        def worker():
            try:
                for freq, duration in notes:
                    if freq > 0:
                        winsound.Beep(int(freq), int(duration))
            except Exception:
                pass
        threading.Thread(target=worker, daemon=True).start()

    def play_eat_regular(self):
        self._play([(880, 45), (1174, 55)])

    def play_eat_bonus(self):
        self._play([(659, 40), (880, 40), (1318, 70)])

    def play_game_over(self):
        self._play([(440, 90), (370, 90), (293, 140), (196, 220)])

    def play_start(self):
        self._play([(523, 50), (659, 50), (784, 80)])

    def play_bounce(self):
        self._play([(440, 25)])


class Particle:
    """Exploding particle effect for ball collection."""
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1.8, 5.2)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.size = random.uniform(3, 6)
        self.life = 1.0  # 1.0 to 0.0
        self.decay = random.uniform(0.04, 0.08)
        self.color = color

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= self.decay
        self.size = max(0, self.size * 0.94)
        return self.life > 0


class FloatingScore:
    """Floating popup score label."""
    def __init__(self, x, y, text, color=COLOR_ACCENT):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.life = 1.0
        self.decay = 0.05

    def update(self):
        self.y -= 1.4
        self.life -= self.decay
        return self.life > 0


class BouncingHazardBall:
    """A physics bouncing ball obstacle that the snake must dodge."""
    def __init__(self, x, y, radius=14):
        self.x = float(x)
        self.y = float(y)
        self.radius = radius
        angle = random.uniform(0.3, 1.2)
        speed = 3.6
        self.vx = speed * math.cos(angle) * random.choice([-1, 1])
        self.vy = speed * math.sin(angle) * random.choice([-1, 1])

    def update(self, bounds_w, bounds_h, sound_mgr=None):
        self.x += self.vx
        self.y += self.vy
        bounced = False

        if self.x - self.radius <= 0:
            self.x = self.radius
            self.vx = -self.vx
            bounced = True
        elif self.x + self.radius >= bounds_w:
            self.x = bounds_w - self.radius
            self.vx = -self.vx
            bounced = True

        if self.y - self.radius <= 0:
            self.y = self.radius
            self.vy = -self.vy
            bounced = True
        elif self.y + self.radius >= bounds_h:
            self.y = bounds_h - self.radius
            self.vy = -self.vy
            bounced = True

        if bounced and sound_mgr:
            sound_mgr.play_bounce()

    def check_collision(self, cell_x, cell_y, cell_size):
        cx = (cell_x + 0.5) * cell_size
        cy = (cell_y + 0.5) * cell_size
        dist_sq = (self.x - cx) ** 2 + (self.y - cy) ** 2
        hit_radius = self.radius + (cell_size * 0.42)
        return dist_sq < (hit_radius * hit_radius)


class SnakeBallGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Snake & Ball Arcade")
        self.root.resizable(False, False)
        self.root.configure(bg=COLOR_HEADER_BG)

        self.sound = SoundManager(enabled=True)
        self.high_score = self.load_high_score()

        # Difficulties: tick delay in ms
        self.difficulty_speeds = {
            "Easy": 115,
            "Normal": 85,
            "Hard": 60,
        }
        self.current_difficulty = "Normal"
        self.hazard_mode = False  # Bouncing Hazard Ball mode

        # Game state
        self.state = "START"  # START, RUNNING, PAUSED, GAME_OVER
        self.score = 0
        self.snake = []
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.grow_counter = 0

        # Balls
        self.food_pos = None
        self.bonus_pos = None
        self.bonus_timer = 0
        self.bonus_max_time = 75  # ~6.5 seconds

        # Hazard Ball
        self.hazard_ball = None

        # Visual Effects
        self.particles = []
        self.floaters = []
        self.shake_frames = 0

        self.setup_ui()
        self.bind_events()
        self.reset_game_state()
        self.draw_start_screen()

        # Center window on screen
        self.root.update_idletasks()
        w = self.root.winfo_reqwidth()
        h = self.root.winfo_reqheight()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

    # ================= UI Setup =================
    def setup_ui(self):
        # Header Panel
        self.header_frame = tk.Frame(self.root, bg=COLOR_HEADER_BG, padx=16, pady=10)
        self.header_frame.pack(fill=tk.X)

        font_large = tkfont.Font(family="Consolas", size=15, weight="bold")
        font_sub = tkfont.Font(family="Segoe UI", size=10)
        font_btn = tkfont.Font(family="Segoe UI", size=9, weight="bold")

        # Score display
        left_box = tk.Frame(self.header_frame, bg=COLOR_HEADER_BG)
        left_box.pack(side=tk.LEFT)
        self.lbl_score = tk.Label(
            left_box, text=f"SCORE: 0", font=font_large,
            fg=COLOR_ACCENT, bg=COLOR_HEADER_BG
        )
        self.lbl_score.pack(anchor="w")
        self.lbl_high = tk.Label(
            left_box, text=f"HIGH SCORE: {self.high_score}", font=font_sub,
            fg=COLOR_TEXT_MUTED, bg=COLOR_HEADER_BG
        )
        self.lbl_high.pack(anchor="w")

        # Control Indicators / Buttons
        right_box = tk.Frame(self.header_frame, bg=COLOR_HEADER_BG)
        right_box.pack(side=tk.RIGHT)

        self.btn_hazard = tk.Button(
            right_box, text="Hazard Ball: OFF", font=font_btn,
            bg="#2a2238", fg="#c084fc", activebackground="#3b2b52", activeforeground="#ffffff",
            bd=0, padx=8, pady=4, cursor="hand2", command=self.toggle_hazard_mode
        )
        self.btn_hazard.pack(side=tk.RIGHT, padx=4)

        self.btn_sound = tk.Button(
            right_box, text="Sound: ON", font=font_btn,
            bg="#1e293b", fg=COLOR_TEXT_PRIMARY, activebackground="#334155", activeforeground="#ffffff",
            bd=0, padx=8, pady=4, cursor="hand2", command=self.toggle_sound
        )
        self.btn_sound.pack(side=tk.RIGHT, padx=4)

        self.btn_diff = tk.Button(
            right_box, text=f"Speed: {self.current_difficulty}", font=font_btn,
            bg="#1e293b", fg=COLOR_ACCENT, activebackground="#334155", activeforeground="#ffffff",
            bd=0, padx=8, pady=4, cursor="hand2", command=self.cycle_difficulty
        )
        self.btn_diff.pack(side=tk.RIGHT, padx=4)

        # Main Arena Canvas
        self.canvas = tk.Canvas(
            self.root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT,
            bg=COLOR_BG, highlightthickness=0
        )
        self.canvas.pack()

        # Footer hints
        footer = tk.Frame(self.root, bg=COLOR_HEADER_BG, pady=6)
        footer.pack(fill=tk.X)
        hints = "Controls: Arrow Keys / WASD = Move | Space = Pause/Resume | R = Restart | H = Hazard Ball | M = Mute"
        tk.Label(footer, text=hints, font=tkfont.Font(family="Segoe UI", size=8),
                 fg=COLOR_TEXT_MUTED, bg=COLOR_HEADER_BG).pack()

    def bind_events(self):
        self.root.bind("<Up>", lambda e: self.change_direction((0, -1)))
        self.root.bind("<Down>", lambda e: self.change_direction((0, 1)))
        self.root.bind("<Left>", lambda e: self.change_direction((-1, 0)))
        self.root.bind("<Right>", lambda e: self.change_direction((1, 0)))

        self.root.bind("w", lambda e: self.change_direction((0, -1)))
        self.root.bind("s", lambda e: self.change_direction((0, 1)))
        self.root.bind("a", lambda e: self.change_direction((-1, 0)))
        self.root.bind("d", lambda e: self.change_direction((1, 0)))

        self.root.bind("<space>", lambda e: self.toggle_pause())
        self.root.bind("<Return>", lambda e: self.handle_action_key())
        self.root.bind("r", lambda e: self.start_game())
        self.root.bind("h", lambda e: self.toggle_hazard_mode())
        self.root.bind("m", lambda e: self.toggle_sound())
        self.root.bind("<Escape>", lambda e: self.root.destroy())

    # ================= State Management =================
    def load_high_score(self):
        try:
            if os.path.exists(HIGH_SCORE_FILE):
                with open(HIGH_SCORE_FILE, "r") as f:
                    data = json.load(f)
                    return data.get("high_score", 0)
        except Exception:
            pass
        return 0

    def save_high_score(self):
        try:
            with open(HIGH_SCORE_FILE, "w") as f:
                json.dump({"high_score": self.high_score}, f)
        except Exception:
            pass

    def reset_game_state(self):
        mid_x = COLS // 2
        mid_y = ROWS // 2
        self.snake = [
            (mid_x, mid_y),
            (mid_x - 1, mid_y),
            (mid_x - 2, mid_y),
            (mid_x - 3, mid_y),
        ]
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.grow_counter = 0
        self.score = 0
        self.particles.clear()
        self.floaters.clear()
        self.bonus_pos = None
        self.bonus_timer = 0
        self.shake_frames = 0

        self.spawn_food()

        if self.hazard_mode:
            self.hazard_ball = BouncingHazardBall(
                x=random.randint(40, CANVAS_WIDTH - 40),
                y=random.randint(40, CANVAS_HEIGHT - 40),
                radius=14
            )
        else:
            self.hazard_ball = None

        self.update_header()

    def update_header(self):
        self.lbl_score.config(text=f"SCORE: {self.score}")
        self.lbl_high.config(text=f"HIGH SCORE: {self.high_score}")
        self.btn_diff.config(text=f"Speed: {self.current_difficulty}")
        self.btn_sound.config(text="Sound: ON" if self.sound.enabled else "Sound: OFF")
        self.btn_hazard.config(
            text="Hazard Ball: ON" if self.hazard_mode else "Hazard Ball: OFF",
            fg="#e879f9" if self.hazard_mode else "#c084fc"
        )

    def change_direction(self, new_dir):
        if self.state != "RUNNING":
            if self.state in ("START", "GAME_OVER"):
                self.start_game()
            return
        # Disallow 180-degree immediate reversal
        cur_dx, cur_dy = self.direction
        new_dx, new_dy = new_dir
        if (cur_dx + new_dx != 0) or (cur_dy + new_dy != 0):
            self.next_direction = new_dir

    def handle_action_key(self):
        if self.state in ("START", "GAME_OVER"):
            self.start_game()
        elif self.state == "PAUSED":
            self.toggle_pause()

    def toggle_pause(self):
        if self.state == "RUNNING":
            self.state = "PAUSED"
            self.draw_screen()
        elif self.state == "PAUSED":
            self.state = "RUNNING"
            self.tick()

    def toggle_sound(self):
        self.sound.enabled = not self.sound.enabled
        self.update_header()

    def toggle_hazard_mode(self):
        self.hazard_mode = not self.hazard_mode
        if self.hazard_mode and self.state == "RUNNING" and not self.hazard_ball:
            self.hazard_ball = BouncingHazardBall(
                x=random.randint(50, CANVAS_WIDTH - 50),
                y=random.randint(50, CANVAS_HEIGHT - 50)
            )
        elif not self.hazard_mode:
            self.hazard_ball = None
        self.update_header()
        if self.state != "RUNNING":
            self.draw_screen()

    def cycle_difficulty(self):
        modes = list(self.difficulty_speeds.keys())
        idx = (modes.index(self.current_difficulty) + 1) % len(modes)
        self.current_difficulty = modes[idx]
        self.update_header()

    def start_game(self):
        self.reset_game_state()
        self.state = "RUNNING"
        self.sound.play_start()
        self.tick()

    # ================= Spawning =================
    def get_empty_cells(self):
        occupied = set(self.snake)
        if self.food_pos:
            occupied.add(self.food_pos)
        if self.bonus_pos:
            occupied.add(self.bonus_pos)
        empty = [
            (c, r) for c in range(COLS) for r in range(ROWS)
            if (c, r) not in occupied
        ]
        return empty

    def spawn_food(self):
        empty = self.get_empty_cells()
        if empty:
            self.food_pos = random.choice(empty)
        else:
            self.food_pos = None

    def maybe_spawn_bonus(self):
        if self.bonus_pos is None and random.random() < 0.04:  # 4% chance each tick
            empty = self.get_empty_cells()
            if empty:
                self.bonus_pos = random.choice(empty)
                self.bonus_timer = self.bonus_max_time

    # ================= Game Loop =================
    def tick(self):
        if self.state != "RUNNING":
            return

        self.direction = self.next_direction
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)

        # 1. Wall Collision Check
        if not (0 <= new_head[0] < COLS and 0 <= new_head[1] < ROWS):
            self.game_over("Hit the arena wall!")
            return

        # 2. Self Collision Check
        if new_head in self.snake[:-1]:
            self.game_over("Ran into your own tail!")
            return

        # Move snake
        self.snake.insert(0, new_head)

        # Check Ball Collisions
        head_cx = (new_head[0] + 0.5) * CELL_SIZE
        head_cy = (new_head[1] + 0.5) * CELL_SIZE

        # Regular Ball
        if new_head == self.food_pos:
            points = 10
            self.score += points
            self.grow_counter += 1
            self.spawn_particles(head_cx, head_cy, COLOR_FOOD_BALL, count=16)
            self.floaters.append(FloatingScore(head_cx, head_cy, f"+{points}", COLOR_FOOD_GLOW))
            self.sound.play_eat_regular()
            self.spawn_food()
            self.maybe_spawn_bonus()
        # Bonus Golden Ball
        elif self.bonus_pos and new_head == self.bonus_pos:
            points = 35
            self.score += points
            self.grow_counter += 2
            self.spawn_particles(head_cx, head_cy, COLOR_BONUS_BALL, count=24)
            self.floaters.append(FloatingScore(head_cx, head_cy, f"+{points} BONUS!", COLOR_BONUS_BALL))
            self.sound.play_eat_bonus()
            self.bonus_pos = None
            self.bonus_timer = 0
        else:
            # Snake didn't eat: remove tail segment unless growing
            if self.grow_counter > 0:
                self.grow_counter -= 1
            else:
                self.snake.pop()

        # Update Bonus Timer
        if self.bonus_pos:
            self.bonus_timer -= 1
            if self.bonus_timer <= 0:
                self.bonus_pos = None

        # Update Bouncing Hazard Ball
        if self.hazard_ball:
            self.hazard_ball.update(CANVAS_WIDTH, CANVAS_HEIGHT, self.sound)
            # Collision check between hazard ball and any snake segment
            for segment in self.snake:
                if self.hazard_ball.check_collision(segment[0], segment[1], CELL_SIZE):
                    self.game_over("Crushed by the Bouncing Hazard Ball!")
                    return

        # Update High Score
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_high_score()

        self.update_header()

        # Update visual effects
        self.particles = [p for p in self.particles if p.update()]
        self.floaters = [f for f in self.floaters if f.update()]

        # Draw frame
        self.draw_screen()

        # Dynamic speed calculation (gets slightly faster as snake grows)
        base_speed = self.difficulty_speeds[self.current_difficulty]
        speed_factor = max(0.65, 1.0 - (len(self.snake) * 0.005))
        delay = int(base_speed * speed_factor)

        self.root.after(delay, self.tick)

    def spawn_particles(self, x, y, color, count=16):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))

    def game_over(self, reason):
        self.state = "GAME_OVER"
        self.sound.play_game_over()
        self.shake_frames = 6
        self.save_high_score()
        self.draw_screen(reason=reason)

    # ================= Drawing Routines =================
    def draw_screen(self, reason=""):
        self.canvas.delete("all")

        # Subtle Arena Grid
        for x in range(0, CANVAS_WIDTH, CELL_SIZE):
            self.canvas.create_line(x, 0, x, CANVAS_HEIGHT, fill=COLOR_GRID, width=1)
        for y in range(0, CANVAS_HEIGHT, CELL_SIZE):
            self.canvas.create_line(0, y, CANVAS_WIDTH, y, fill=COLOR_GRID, width=1)

        # Draw Food Ball (3D shaded red sphere)
        if self.food_pos:
            self.draw_ball(self.food_pos[0], self.food_pos[1], COLOR_FOOD_BALL, COLOR_FOOD_GLOW)

        # Draw Bonus Golden Ball (with countdown ring)
        if self.bonus_pos:
            self.draw_bonus_ball(self.bonus_pos[0], self.bonus_pos[1])

        # Draw Snake
        self.draw_snake()

        # Draw Bouncing Hazard Ball
        if self.hazard_ball:
            self.draw_hazard_ball()

        # Draw Particles
        for p in self.particles:
            alpha_size = p.size * p.life
            self.canvas.create_oval(
                p.x - alpha_size, p.y - alpha_size,
                p.x + alpha_size, p.y + alpha_size,
                fill=p.color, outline=""
            )

        # Draw Floating Score Popups
        for f in self.floaters:
            self.canvas.create_text(
                f.x, f.y, text=f.text,
                font=tkfont.Font(family="Segoe UI", size=11, weight="bold"),
                fill=f.color
            )

        # Overlays
        if self.state == "START":
            self.draw_start_screen()
        elif self.state == "PAUSED":
            self.draw_pause_screen()
        elif self.state == "GAME_OVER":
            self.draw_game_over_screen(reason)

    def draw_ball(self, grid_x, grid_y, primary_color, glow_color):
        pad = 2
        x1 = grid_x * CELL_SIZE + pad
        y1 = grid_y * CELL_SIZE + pad
        x2 = (grid_x + 1) * CELL_SIZE - pad
        y2 = (grid_y + 1) * CELL_SIZE - pad

        # Glow / Shadow outline
        self.canvas.create_oval(x1 - 1, y1 - 1, x2 + 1, y2 + 1, fill="", outline=glow_color, width=1)
        # Main Sphere
        self.canvas.create_oval(x1, y1, x2, y2, fill=primary_color, outline="")
        # 3D Highlight specular reflection
        hl_pad = CELL_SIZE * 0.22
        hl_size = CELL_SIZE * 0.28
        self.canvas.create_oval(
            x1 + hl_pad, y1 + hl_pad,
            x1 + hl_pad + hl_size, y1 + hl_pad + hl_size,
            fill="#ffffff", outline=""
        )

    def draw_bonus_ball(self, grid_x, grid_y):
        # Pulsing golden ball
        self.draw_ball(grid_x, grid_y, COLOR_BONUS_BALL, COLOR_BONUS_GLOW)
        # Arc countdown timer around bonus ball
        pct = max(0.0, self.bonus_timer / self.bonus_max_time)
        extent = int(pct * 359)
        pad = 1
        x1 = grid_x * CELL_SIZE + pad
        y1 = grid_y * CELL_SIZE + pad
        x2 = (grid_x + 1) * CELL_SIZE - pad
        y2 = (grid_y + 1) * CELL_SIZE - pad
        self.canvas.create_arc(
            x1, y1, x2, y2,
            start=90, extent=extent, style=tk.ARC,
            outline="#ffffff", width=2
        )

    def draw_hazard_ball(self):
        hb = self.hazard_ball
        r = hb.radius
        # Pulsing outer ring
        self.canvas.create_oval(
            hb.x - r - 3, hb.y - r - 3,
            hb.x + r + 3, hb.y + r + 3,
            fill="", outline=COLOR_HAZARD_GLOW, width=2
        )
        # Core ball
        self.canvas.create_oval(
            hb.x - r, hb.y - r,
            hb.x + r, hb.y + r,
            fill=COLOR_HAZARD_BALL, outline="#ffffff", width=1
        )
        # Specular glint
        self.canvas.create_oval(
            hb.x - r * 0.5, hb.y - r * 0.5,
            hb.x - r * 0.1, hb.y - r * 0.1,
            fill="#ffffff", outline=""
        )

    def draw_snake(self):
        for idx, (gx, gy) in enumerate(self.snake):
            pad = 2
            x1 = gx * CELL_SIZE + pad
            y1 = gy * CELL_SIZE + pad
            x2 = (gx + 1) * CELL_SIZE - pad
            y2 = (gy + 1) * CELL_SIZE - pad

            if idx == 0:
                # Snake Head
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=COLOR_SNAKE_HEAD, outline="#a7f3d0", width=1
                )
                self.draw_snake_eyes(x1, y1, x2, y2)
            else:
                # Snake Body: Alternating emerald/forest green segments
                color = COLOR_SNAKE_BODY_1 if idx % 2 == 0 else COLOR_SNAKE_BODY_2
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color, outline=""
                )

    def draw_snake_eyes(self, x1, y1, x2, y2):
        w = x2 - x1
        h = y2 - y1
        dx, dy = self.direction

        eye_radius = 2.6
        pupil_radius = 1.3

        # Default eye offsets
        if dx == 1:  # Moving Right
            e1 = (x2 - 5, y1 + h * 0.28)
            e2 = (x2 - 5, y2 - h * 0.28)
            pupil_offset = (1, 0)
        elif dx == -1:  # Moving Left
            e1 = (x1 + 5, y1 + h * 0.28)
            e2 = (x1 + 5, y2 - h * 0.28)
            pupil_offset = (-1, 0)
        elif dy == -1:  # Moving Up
            e1 = (x1 + w * 0.28, y1 + 5)
            e2 = (x2 - w * 0.28, y1 + 5)
            pupil_offset = (0, -1)
        else:  # Moving Down
            e1 = (x1 + w * 0.28, y2 - 5)
            e2 = (x2 - w * 0.28, y2 - 5)
            pupil_offset = (0, 1)

        for ex, ey in (e1, e2):
            # Eye White
            self.canvas.create_oval(
                ex - eye_radius, ey - eye_radius,
                ex + eye_radius, ey + eye_radius,
                fill="#ffffff", outline=""
            )
            # Pupil
            px = ex + pupil_offset[0]
            py = ey + pupil_offset[1]
            self.canvas.create_oval(
                px - pupil_radius, py - pupil_radius,
                px + pupil_radius, py + pupil_radius,
                fill="#0f172a", outline=""
            )

    # ================= Overlays =================
    def draw_start_screen(self):
        cx = CANVAS_WIDTH // 2
        cy = CANVAS_HEIGHT // 2

        self.canvas.create_rectangle(
            cx - 220, cy - 130, cx + 220, cy + 130,
            fill="#1e1e2e", outline="#3b4261", width=2
        )

        self.canvas.create_text(
            cx, cy - 70, text="🐍 SNAKE & BALL ⚽",
            font=tkfont.Font(family="Segoe UI", size=22, weight="bold"),
            fill=COLOR_ACCENT
        )
        self.canvas.create_text(
            cx, cy - 25, text="Eat energy balls to grow & earn points!",
            font=tkfont.Font(family="Segoe UI", size=11),
            fill=COLOR_TEXT_PRIMARY
        )
        self.canvas.create_text(
            cx, cy + 5, text="🔴 Red Ball = +10 pts  |  ⭐ Golden Ball = +35 pts",
            font=tkfont.Font(family="Segoe UI", size=10),
            fill=COLOR_TEXT_MUTED
        )
        self.canvas.create_text(
            cx, cy + 30, text="Press 'H' anytime to toggle the Bouncing Hazard Ball!",
            font=tkfont.Font(family="Segoe UI", size=10, weight="bold"),
            fill="#c084fc"
        )
        self.canvas.create_text(
            cx, cy + 85, text="Press SPACE or ENTER to Play",
            font=tkfont.Font(family="Segoe UI", size=14, weight="bold"),
            fill="#4ade80"
        )

    def draw_pause_screen(self):
        cx = CANVAS_WIDTH // 2
        cy = CANVAS_HEIGHT // 2

        self.canvas.create_rectangle(
            cx - 150, cy - 60, cx + 150, cy + 60,
            fill="#1e1e2e", outline="#475569", width=2
        )
        self.canvas.create_text(
            cx, cy - 15, text="PAUSED",
            font=tkfont.Font(family="Segoe UI", size=20, weight="bold"),
            fill=COLOR_TEXT_PRIMARY
        )
        self.canvas.create_text(
            cx, cy + 22, text="Press SPACE to Resume",
            font=tkfont.Font(family="Segoe UI", size=11),
            fill=COLOR_ACCENT
        )

    def draw_game_over_screen(self, reason):
        cx = CANVAS_WIDTH // 2
        cy = CANVAS_HEIGHT // 2

        self.canvas.create_rectangle(
            cx - 210, cy - 110, cx + 210, cy + 120,
            fill="#181825", outline="#ef4444", width=2
        )
        self.canvas.create_text(
            cx, cy - 65, text="GAME OVER",
            font=tkfont.Font(family="Segoe UI", size=24, weight="bold"),
            fill="#ef4444"
        )
        self.canvas.create_text(
            cx, cy - 25, text=reason,
            font=tkfont.Font(family="Segoe UI", size=11, slant="italic"),
            fill=COLOR_TEXT_MUTED
        )
        self.canvas.create_text(
            cx, cy + 12, text=f"Final Score: {self.score}   |   Best: {self.high_score}",
            font=tkfont.Font(family="Segoe UI", size=13, weight="bold"),
            fill=COLOR_TEXT_PRIMARY
        )
        self.canvas.create_text(
            cx, cy + 50, text="Press 'R' or ENTER to Play Again",
            font=tkfont.Font(family="Segoe UI", size=12, weight="bold"),
            fill="#4ade80"
        )
        self.canvas.create_text(
            cx, cy + 85, text="Press 'Esc' to Exit",
            font=tkfont.Font(family="Segoe UI", size=9),
            fill=COLOR_TEXT_MUTED
        )


def main():
    root = tk.Tk()
    game = SnakeBallGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
