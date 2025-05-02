import random
import numpy as np
from OpenGL.GL import *
from OpenGL.GLUT import *
import time
import math

# Game configuration
size = 25
cell = 20
maze_size = size * cell
window_width = maze_size + 300
window_height = maze_size + 200
grid = np.zeros((size, size), dtype=int)
player = [0, 0]
goal = [size - 1, size - 1]
dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
gold = []
obstacles = []  # New: list for obstacles
collected_gold = 0
total_gold = 10
total_obstacles = 5  # New: number of obstacles
game_paused = False
start_time = 0
time_limit = 120
game_over = False
game_won = False

# Button configuration
button_width = 100
button_height = 40
restart_button = {"x": window_width - 250, "y": 50, "text": "Restart"}
pause_button = {"x": window_width - 120, "y": 50, "text": "Pause"}


def is_valid(x, y):
    return 0 <= x < size and 0 <= y < size


def generate_maze():
    global grid
    grid = np.zeros((size, size), dtype=int)
    # Ensure starting position is valid
    grid[0, 0] = 1  # Make sure starting position is always a path
    walls = []
    add_walls(0, 0, walls)
    while walls:
        x, y = walls.pop(random.randint(0, len(walls) - 1))
        if count_neighbors(x, y) == 1:
            grid[x, y] = 1
            add_walls(x, y, walls)
    grid[goal[0], goal[1]] = 1


def add_walls(x, y, walls):
    for dx, dy in dirs:
        nx, ny = x + dx, y + dy
        if is_valid(nx, ny) and grid[nx, ny] == 0:
            walls.append((nx, ny))


def count_neighbors(x, y):
    count = 0
    for dx, dy in dirs:
        nx, ny = x + dx, y + dy
        if is_valid(nx, ny) and grid[nx, ny] == 1:
            count += 1
    return count


def place_gold_and_obstacles():
    global gold, obstacles
    gold = []
    obstacles = []
    available_spots = [(i, j) for i in range(size) for j in range(size)
                       if grid[i, j] == 1 and (i, j) != (0, 0) and (i, j) != (size - 1, size - 1)]

    # Place gold
    for _ in range(total_gold):
        if available_spots:
            pos = random.choice(available_spots)
            gold.append(pos)
            available_spots.remove(pos)

    # Place obstacles
    for _ in range(total_obstacles):
        if available_spots:
            pos = random.choice(available_spots)
            obstacles.append(pos)
            available_spots.remove(pos)


def collect_gold():
    global gold, collected_gold, game_over
    pos = tuple(player)
    if pos in gold:
        gold.remove(pos)
        collected_gold += 1
    elif pos in obstacles:
        game_over = True


def remove_obstacle():
    global obstacles
    pos = tuple(player)
    if pos in obstacles:
        obstacles.remove(pos)


def draw_point(x, y):
    glBegin(GL_POINTS)
    glVertex2f(x, y)
    glEnd()


def mcl(x0, y0, r):
    points = []
    x, y = 0, r
    d = 1 - r

    # Collect all points first
    while x <= y:
        points.extend([
            (x + x0, y + y0), (-x + x0, y + y0),
            (-x + x0, -y + y0), (x + x0, -y + y0),
            (y + x0, x + y0), (-y + x0, x + y0),
            (-y + x0, -x + y0), (y + x0, -x + y0)
        ])

        de = ((2 * x) + 3)
        dne = ((2 * x) - (2 * y) + 5)
        if d < 0:
            d += de
            x += 1
        else:
            d += dne
            x += 1
            y -= 1

    # Draw filled circle using triangle fan
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(x0, y0)  # Center point
    for px, py in points:
        glVertex2f(px, py)
    # Connect back to first point
    if points:
        glVertex2f(points[0][0], points[0][1])
    glEnd()


def mpl(x0, y0, x1, y1):
    dx = x1 - x0
    dy = y1 - y0
    steps = dx if dx > dy else dy
    steps = -steps if steps < 0 else steps
    x_inc = dx / steps
    y_inc = dy / steps
    x, y = x0, y0
    for _ in range(steps + 1):
        draw_point(round(x), round(y))
        x += x_inc
        y += y_inc


def draw_cell(x, y, col):
    glColor3f(*col)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + cell, y)
    glVertex2f(x + cell, y + cell)
    glVertex2f(x, y + cell)
    glEnd()


def draw_maze():
    glPushMatrix()
    glTranslatef(50, 100, 0)
    for i in range(size):
        for j in range(size):
            x, y = i * cell, j * cell
            if grid[i, j] == 0:
                draw_cell(x, y, (1.0, 0.7, 0.7))  # Light pink color for walls
    glPopMatrix()


def draw_player():
    glPushMatrix()
    glTranslatef(50, 100, 0)
    glColor3f(0.0, 0.0, 1.0)  # Blue color for player
    x = player[0] * cell + cell // 2
    y = player[1] * cell + cell // 2

    # Body using mcl
    mcl(x, y, 5)

    # Head using mcl
    mcl(x, y + 5, 3)

    # Arms using mpl
    mpl(x - 5, y, x + 5, y)

    # Legs using mpl
    mpl(x - 3, y - 5, x, y)
    mpl(x + 3, y - 5, x, y)

    glPopMatrix()


def draw_goal():
    glPushMatrix()
    glTranslatef(50, 100, 0)
    glColor3f(1, 0, 0)
    x = goal[0] * cell + cell // 2
    y = goal[1] * cell + cell // 2
    glBegin(GL_QUADS)
    glVertex2f(x - 8, y - 8)
    glVertex2f(x + 8, y - 8)
    glVertex2f(x + 8, y + 8)
    glVertex2f(x - 8, y + 8)
    glEnd()
    glPopMatrix()


def draw_gold():
    glPushMatrix()
    glTranslatef(50, 100, 0)
    glColor3f(1.0, 1.0, 0.0)  # Yellow for gold
    for gx, gy in gold:
        px = gx * cell + cell // 2
        py = gy * cell + cell // 2
        mcl(px, py, 6)
    glPopMatrix()


def draw_obstacles():
    glPushMatrix()
    glTranslatef(50, 100, 0)
    glColor3f(1.0, 0.0, 0.0)  # Red for obstacles
    for ox, oy in obstacles:
        px = ox * cell + cell // 2
        py = oy * cell + cell // 2
        mcl(px, py, 6)
    glPopMatrix()


def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glRasterPos2f(x, y)
    for char in text:
        glutBitmapCharacter(font, ord(char))


def draw_fancy_title():
    glColor3f(1.0, 0.84, 0.0)
    draw_text(window_width / 2 - 120, window_height - 50, "MAZE EXPLORER", GLUT_BITMAP_TIMES_ROMAN_24)


def draw_button(button):
    glColor3f(0.5, 0.5, 0.5)
    glBegin(GL_QUADS)
    glVertex2f(button["x"], button["y"])
    glVertex2f(button["x"] + button_width, button["y"])
    glVertex2f(button["x"] + button_width, button["y"] + button_height)
    glVertex2f(button["x"], button["y"] + button_height)
    glEnd()

    glColor3f(1.0, 1.0, 1.0)
    text_width = sum(glutBitmapWidth(GLUT_BITMAP_HELVETICA_18, ord(c)) for c in button["text"])
    text_x = button["x"] + (button_width - text_width) / 2
    text_y = button["y"] + button_height / 2 - 5
    draw_text(text_x, text_y, button["text"])


def display_game_stats():
    glColor3f(1.0, 1.0, 1.0)
    x_pos = maze_size + 70
    y_start = window_height - 150

    spacing = 30
    draw_text(x_pos, y_start, f"Time Limit: {time_limit}s")

    if not game_paused and not game_over and not game_won:
        elapsed_time = time.time() - start_time
        remaining_time = max(0, time_limit - elapsed_time)
        draw_text(x_pos, y_start - spacing, f"Time Left: {int(remaining_time)}s")

    draw_text(x_pos, y_start - spacing * 2, f"Gold Collected: {collected_gold}")
    draw_text(x_pos, y_start - spacing * 3, f"Gold Remaining: {len(gold)}")
    draw_text(x_pos, y_start - spacing * 4, f"Obstacles: {len(obstacles)}")

    # Centered large text messages for game states
    if game_paused:
        glColor3f(1.0, 1.0, 0.0)  # Yellow color for pause
        draw_text(window_width / 2 - 80, window_height / 2, "PAUSED", GLUT_BITMAP_TIMES_ROMAN_24)
    elif game_over:
        glColor3f(1.0, 0.0, 0.0)  # Red color for game over
        draw_text(window_width / 2 - 120, window_height / 2, "GAME OVER!", GLUT_BITMAP_TIMES_ROMAN_24)
        draw_text(window_width / 2 - 160, window_height / 2 - 40, "Press Restart to try again",
                  GLUT_BITMAP_HELVETICA_18)
    elif game_won:
        glColor3f(0.0, 1.0, 0.0)  # Green color for win
        draw_text(window_width / 2 - 180, window_height / 2, "YOU'RE THE WINNER!", GLUT_BITMAP_TIMES_ROMAN_24)
        draw_text(window_width / 2 - 120, window_height / 2 - 40, "Congratulations!", GLUT_BITMAP_HELVETICA_18)


def display():
    glClear(GL_COLOR_BUFFER_BIT)

    draw_fancy_title()
    draw_maze()
    draw_gold()
    draw_obstacles()  # New: draw obstacles
    draw_player()
    draw_goal()

    display_game_stats()

    draw_button(restart_button)
    draw_button(pause_button)

    glutSwapBuffers()


def handle_special_keys(key, x, y):
    global player, game_won
    if not game_paused and not game_over and not game_won:
        new_pos = player[:]
        if key == GLUT_KEY_UP:
            new_pos[1] = min(size - 1, player[1] + 1)
        elif key == GLUT_KEY_DOWN:
            new_pos[1] = max(0, player[1] - 1)
        elif key == GLUT_KEY_LEFT:
            new_pos[0] = max(0, player[0] - 1)
        elif key == GLUT_KEY_RIGHT:
            new_pos[0] = min(size - 1, player[0] + 1)

        if grid[new_pos[0], new_pos[1]] == 1:
            player = new_pos
            # Check for win condition - all gold collected and at goal
            if collected_gold == total_gold and tuple(player) == tuple(goal):
                game_won = True
        glutPostRedisplay()


def handle_keyboard(key, x, y):
    if key == b'\x1b':  # ESC key
        glutLeaveMainLoop()
    elif key == b'\r':  # Enter key
        if not game_paused and not game_over and not game_won:
            collect_gold()
    elif key == b'j':  # J key
        if not game_paused and not game_over and not game_won:
            remove_obstacle()
    glutPostRedisplay()


def handle_mouse(button, state, x, y):
    global game_paused
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        y = window_height - y
        if restart_button["x"] <= x <= restart_button["x"] + button_width and \
                restart_button["y"] <= y <= restart_button["y"] + button_height:
            restart_game()
        elif pause_button["x"] <= x <= pause_button["x"] + button_width and \
                pause_button["y"] <= y <= pause_button["y"] + button_height:
            game_paused = not game_paused
    glutPostRedisplay()


def restart_game():
    global player, collected_gold, start_time, game_over, game_won, game_paused
    generate_maze()
    place_gold_and_obstacles()
    player = [0, 0]
    collected_gold = 0
    start_time = time.time()
    game_over = False
    game_won = False
    game_paused = False


def update_game_state(value):
    global game_over
    if not game_paused and not game_over and not game_won:
        elapsed_time = time.time() - start_time
        if elapsed_time >= time_limit:
            game_over = True
    glutPostRedisplay()
    glutTimerFunc(1000, update_game_state, 0)


def main():
    global grid, start_time
    glutInit()
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE)
    glutInitWindowSize(window_width, window_height)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Maze Explorer")

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, window_width, 0, window_height, -1, 1)
    glMatrixMode(GL_MODELVIEW)

    glClearColor(0.0, 0.0, 0.0, 1.0)

    generate_maze()
    place_gold_and_obstacles()
    start_time = time.time()

    glutDisplayFunc(display)
    glutKeyboardFunc(handle_keyboard)
    glutSpecialFunc(handle_special_keys)
    glutMouseFunc(handle_mouse)
    glutTimerFunc(0, update_game_state, 0)

    glutMainLoop()


if __name__ == "__main__":
    main()

