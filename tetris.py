"""
俄罗斯方块 — pygame 版（不依赖 tkinter）。
运行：.\venv\Scripts\python.exe tetris.py
"""

from __future__ import annotations

import random
import sys
from typing import List, Optional, Tuple

import pygame

COLS, ROWS = 10, 20
CELL = 32
SIDEBAR = 200
PAD = 12
BOARD_W = COLS * CELL
BOARD_H = ROWS * CELL
WIDTH = PAD * 2 + BOARD_W + SIDEBAR
HEIGHT = PAD * 2 + BOARD_H
FPS = 60

SHAPES: List[Tuple[List[Tuple[int, int]], int]] = [
    ([(0, 0), (0, 1), (0, 2), (0, 3)], 1),
    ([(0, 0), (1, 0), (1, 1), (1, 2)], 2),
    ([(0, 2), (1, 0), (1, 1), (1, 2)], 3),
    ([(0, 0), (0, 1), (1, 0), (1, 1)], 4),
    ([(0, 1), (0, 2), (1, 0), (1, 1)], 5),
    ([(0, 1), (1, 0), (1, 1), (1, 2)], 6),
    ([(0, 0), (0, 1), (1, 1), (1, 2)], 7),
]

COLORS = [
    (20, 20, 28),
    (0, 232, 232),
    (255, 140, 0),
    (60, 120, 255),
    (255, 230, 50),
    (80, 220, 80),
    (180, 80, 220),
    (240, 80, 100),
]

BG = (12, 12, 18)
GRID_LINE = (48, 48, 64)
TEXT = (232, 232, 240)
PAUSE_C = (255, 255, 136)
OVER_C = (255, 100, 100)


def rotate_cells(cells: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    return [(c, -r) for r, c in cells]


def normalize(cells: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


class Piece:
    def __init__(self) -> None:
        self.cells, self.color_idx = random.choice(SHAPES)
        self.cells = [tuple(t) for t in self.cells]
        self.x = COLS // 2 - 2
        self.y = 0

    def positions(self) -> List[Tuple[int, int]]:
        return [(self.y + r, self.x + c) for r, c in self.cells]

    def rotated(self) -> List[Tuple[int, int]]:
        return normalize(rotate_cells(self.cells))


def valid(board: List[List[int]], cells: List[Tuple[int, int]], ox: int, oy: int) -> bool:
    for r, c in cells:
        rr, cc = r + oy, c + ox
        if cc < 0 or cc >= COLS or rr >= ROWS:
            return False
        if rr >= 0 and board[rr][cc]:
            return False
    return True


def merge(board: List[List[int]], piece: Piece) -> None:
    for r, c in piece.positions():
        if 0 <= r < ROWS and 0 <= c < COLS:
            board[r][c] = piece.color_idx


def clear_lines(board: List[List[int]]) -> int:
    new_board = [row for row in board if any(x == 0 for x in row)]
    cleared = ROWS - len(new_board)
    board[:] = [[0] * COLS for _ in range(cleared)] + new_board
    return cleared


def ghost_y(board: List[List[int]], piece: Piece) -> int:
    gy = piece.y
    while valid(board, [(gy + 1 + r, piece.x + c) for r, c in piece.cells], 0, 0):
        gy += 1
    return gy


def draw_cell(
    surf: pygame.Surface,
    col: int,
    row: int,
    color_idx: int,
    *,
    outline_only: bool = False,
) -> None:
    x = PAD + col * CELL
    y = PAD + row * CELL
    rect = pygame.Rect(x + 1, y + 1, CELL - 2, CELL - 2)
    color = COLORS[color_idx] if color_idx < len(COLORS) else (128, 128, 128)
    if outline_only:
        pygame.draw.rect(surf, color, rect, 2)
    else:
        pygame.draw.rect(surf, color, rect)
        pygame.draw.rect(surf, (30, 30, 40), rect, 1)


def main() -> None:
    pygame.init()
    pygame.display.set_caption("俄罗斯方块")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    try:
        font = pygame.font.SysFont("microsoftyahei,simsun,arial", 18)
    except Exception:
        font = pygame.font.Font(None, 24)

    board: List[List[int]] = [[0] * COLS for _ in range(ROWS)]
    piece: Optional[Piece] = Piece()
    score = 0
    level = 1
    drop_ms = 800
    paused = False
    game_over = False
    last_drop = pygame.time.get_ticks()
    hard_drop_pending = False

    def tick_level() -> None:
        nonlocal drop_ms, level
        level = 1 + score // 500
        drop_ms = max(120, 800 - (level - 1) * 70)

    def lock_piece() -> None:
        nonlocal piece, score, game_over
        if not piece:
            return
        merge(board, piece)
        n = clear_lines(board)
        mult = [0, 100, 300, 500, 800]
        score += mult[min(n, 4)] * level
        tick_level()
        piece = Piece()
        if not valid(board, piece.positions(), 0, 0):
            game_over = True
            piece = None

    def restart() -> None:
        nonlocal board, piece, score, level, drop_ms, paused, game_over, last_drop
        board = [[0] * COLS for _ in range(ROWS)]
        piece = Piece()
        score = 0
        level = 1
        drop_ms = 800
        paused = False
        game_over = False
        last_drop = pygame.time.get_ticks()

    running = True
    while running:
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and game_over:
                    restart()
                    continue
                if paused or game_over or not piece:
                    if event.key == pygame.K_p and not game_over:
                        paused = not paused
                    continue
                if event.key == pygame.K_p:
                    paused = not paused
                elif event.key == pygame.K_LEFT:
                    if valid(board, piece.positions(), -1, 0):
                        piece.x -= 1
                elif event.key == pygame.K_RIGHT:
                    if valid(board, piece.positions(), 1, 0):
                        piece.x += 1
                elif event.key == pygame.K_DOWN:
                    if valid(board, piece.positions(), 0, 1):
                        piece.y += 1
                        score += 1
                elif event.key == pygame.K_UP:
                    new_cells = piece.rotated()
                    if valid(
                        board,
                        [(piece.y + r, piece.x + c) for r, c in new_cells],
                        0,
                        0,
                    ):
                        piece.cells = new_cells
                elif event.key == pygame.K_SPACE:
                    gy = ghost_y(board, piece)
                    score += (gy - piece.y) * 2
                    piece.y = gy
                    hard_drop_pending = True

        if hard_drop_pending and piece:
            hard_drop_pending = False
            lock_piece()

        if not paused and not game_over and piece and now - last_drop >= drop_ms:
            last_drop = now
            if valid(board, piece.positions(), 0, 1):
                piece.y += 1
            else:
                lock_piece()

        screen.fill(BG)
        board_rect = pygame.Rect(PAD, PAD, BOARD_W, BOARD_H)
        pygame.draw.rect(screen, GRID_LINE, board_rect, 2)

        for r in range(ROWS):
            for c in range(COLS):
                if board[r][c]:
                    draw_cell(screen, c, r, board[r][c])

        if piece and not game_over:
            gy = ghost_y(board, piece)
            for dr, dc in piece.cells:
                rr, cc = gy + dr, piece.x + dc
                if 0 <= rr < ROWS and 0 <= cc < COLS:
                    draw_cell(screen, cc, rr, piece.color_idx, outline_only=True)
            for dr, dc in piece.cells:
                rr, cc = piece.y + dr, piece.x + dc
                if rr >= 0:
                    draw_cell(screen, piece.x + dc, piece.y + dr, piece.color_idx)

        sx = PAD + BOARD_W + 20
        sy = PAD + 8
        for line in (
            "Tetris",
            "",
            "Left/Right move",
            "Up rotate",
            "Down soft drop",
            "Space hard drop",
            "P pause",
            "R restart (game over)",
            "",
            f"Score: {score}",
            f"Level: {level}",
        ):
            screen.blit(font.render(line, True, TEXT), (sx, sy))
            sy += 24

        if paused:
            t = font.render("Paused (P)", True, PAUSE_C)
            screen.blit(t, t.get_rect(center=board_rect.center))
        if game_over:
            t = font.render("Game Over (R)", True, OVER_C)
            screen.blit(t, t.get_rect(center=board_rect.center))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
