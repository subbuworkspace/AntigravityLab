# 🐍 Snake & Ball Arcade Game

An interactive, modern Snake & Ball game built with Python and Tkinter (no external pip dependencies needed).

## 🚀 How to Run

From your terminal or command prompt:

```bash
cd snakeball
python snake_ball_game.py
```
*(or `python main.py`)*

## 🎮 Controls

| Action | Key / Control |
|---|---|
| **Move Snake** | Arrow Keys (`Up`, `Down`, `Left`, `Right`) or `W`, `A`, `S`, `D` |
| **Start / Pause / Resume** | `Space` or `Enter` |
| **Restart Game** | `R` |
| **Toggle Bouncing Hazard Ball** | `H` or Click **Hazard Ball** button |
| **Toggle 8-bit Audio** | `M` or Click **Sound** button |
| **Cycle Difficulty / Speed** | Click **Speed** button (Easy / Normal / Hard) |
| **Quit** | `Esc` |

## ✨ Features

- **Energy Balls to Eat**:
  - 🔴 **Red Energy Ball**: +10 points, lengthens the snake.
  - ⭐ **Golden Bonus Ball**: +35 points with circular timer countdown.
- **Bouncing Hazard Ball Mode**:
  - An optional physics ball bounces off the arena walls. Dodge it while collecting energy balls!
- **Visuals**:
  - Direction-aware snake eyes.
  - 3D specular shine on balls.
  - Particle explosion on eating balls.
  - Floating score indicators (`+10`, `+35 BONUS!`).
- **Sound & Persistence**:
  - Retro 8-bit synthesized sound effects using Windows sound engine.
  - Automatically saves and loads your local **High Score** (`highscore.json`).
