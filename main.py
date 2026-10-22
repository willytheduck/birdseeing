import copy
import json
import math
import os
import random
import re
import sys
import pygame

from logic import PLACE_BY_STATE
from burds import m_burds
from places import pm_places

# Settings (for tweaking)
W, H = 960, 600
FPS = 60
WHITE = (255, 255, 255)

pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Malaya Peninsula Bird Hunter")
clock = pygame.time.Clock()

ft_big = pygame.font.Font(None, 72)
ft_mid = pygame.font.Font(None, 36)
ft_smol = pygame.font.Font(None, 28)
ft_tiny = pygame.font.Font(None, 22)


def q_game():
    pygame.quit()
    sys.exit()


def draw_txt(surf, txt, ft, color, pos, anchor="topleft"):
    # draw txt; anchor for which point of the txt at (topleft, center,...)
    img = ft.render(txt, True, color)
    surf.blit(img, img.get_rect(**{anchor: pos}))


# map setting
MAP_X, MAP_Y, MAP_W, MAP_H = 270, 100, 420, 480
MAP_BOUND = (1.1, 6.9, 99.5, 104.5)

# 1 clickable marker/state
STATE_MARK = {
    "Perlis": (6.50, 100.20, "L"),
    "Kedah": (6.10, 100.60, "L"),
    "Penang": (5.40, 100.30, "L"),
    "Perak": (4.60, 101.10, "L"),
    "Kelantan": (5.40, 102.05, "R"),
    "Terengganu": (4.85, 103.00, "R"),
    "Pahang": (3.85, 102.60, "R"),
    "Selangor": (3.50, 101.30, "L"),
    "Kuala Lumpur": (3.22, 101.74, "L"),
    "Putrajaya": (2.85, 101.72, "L"),
    "Negeri Sembilan": (2.65, 102.15, "R"),
    "Melaka": (2.25, 102.25, "R"),
    "Johor": (1.95, 103.20, "R"),
}

PM_OL = [
    (6.70, 100.12),
    (6.45, 100.10),
    (6.10, 100.30),
    (5.75, 100.40),
    (5.40, 100.30),
    (4.95, 100.55),
    (4.50, 100.70),
    (4.00, 100.75),
    (3.60, 101.00),
    (3.20, 101.30),
    (2.70, 101.80),
    (2.25, 102.20),
    (1.85, 102.85),
    (1.30, 103.45),
    (1.35, 104.05),
    (1.60, 104.30),
    (2.10, 104.15),
    (2.60, 103.90),
    (3.20, 103.45),
    (4.00, 103.40),
    (4.80, 103.45),
    (5.40, 103.05),
    (6.00, 102.35),
    (6.23, 102.10),
    (5.95, 101.80),
    (5.80, 101.30),
    (5.85, 101.00),
    (6.30, 100.70),
    (6.55, 100.35),
    (6.70, 100.30),
]

BIOME_CLS = {
    "Urban Park": (100, 145, 95),
    "Lowland Forest": (45, 105, 55),
    "Coastal Wetland": (90, 145, 160),
    "Island Forest": (60, 140, 120),
    "Deep Jungle": (30, 80, 45),
    "Montane": (70, 110, 100),
}


def project(lat, lon):
    lat_min, lat_max, lon_min, lon_max = MAP_BOUND
    x = MAP_X + (lon - lon_min) / (lon_max - lon_min) * MAP_W
    y = MAP_Y + (lat_max - lat) / (lat_max - lat_min) * MAP_H
    return (x, y)


# button
class btn:
    def __init__(self, rect, label, on_click):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.on_click = on_click

    def handle_evt(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.on_click()
                return True
        return False

    def draw(self, surf):
        hovering = self.rect.collidepoint(pygame.mouse.get_pos())
        color = (70, 120, 90) if hovering else (50, 90, 70)
        pygame.draw.rect(surf, color, self.rect, border_radius=8)
        pygame.draw.rect(surf, (200, 230, 210), self.rect, 2, border_radius=8)
        draw_txt(surf, self.label, ft_mid, WHITE, self.rect.center, anchor="center")


# Scenes
now_scene = None


def change_sc(scene):
    global now_scene
    now_scene = scene


class MenuS:
    def __init__(self):
        x, w = W // 2 - 130, 260
        self.btns = [
            btn((x, 200, w, 56), "Go Birdwatching", lambda: change_sc(MapS())),
            btn(
                (x, 275, w, 56), "Collection", lambda: change_sc(ComingSS("Collection"))
            ),
            btn((x, 350, w, 56), "Shop", lambda: change_sc(ComingSS("Shop"))),
            btn((x, 425, w, 56), "Quit", q_game),
        ]

    def handle_evt(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            q_game()
        for btn in self.btns:
            if btn.handle_evt(event):
                break

    def draw(self, surf):
        surf.fill((30, 60, 45))
        draw_txt(
            surf,
            "Peninsula Malaysia Bird Hunter",
            ft_big,
            (240, 250, 230),
            (W // 2, 100),
            "center",
        )
        draw_txt(
            surf,
            "Find em. Photograph em. Collect em all.",
            ft_smol,
            (180, 210, 190),
            (W // 2, 150),
            "center",
        )
        for btn in self.btns:
            btn.draw(surf)


class ComingSS:
    def __init__(self, name, back_to=None):
        self.name = name
        self.back_to = back_to or MenuS
        self.back = btn(
            (20, H - 70, 140, 44), "Back", lambda: change_sc(self.back_to())
        )

    def handle_evt(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            change_sc(self.back_to())
        self.back.handle_evt(event)

    def draw(self, surf):
        surf.fill((30, 60, 45))
        draw_txt(
            surf,
            f"{self.name} - coming soon",
            ft_big,
            WHITE,
            (W // 2, H // 2),
            "center",
        )
        self.back.draw(surf)


class MapS:
    MARK_R = 13

    def __init__(self):
        self.back = btn((20, H - 70, 140, 44), "Back", lambda: change_sc(MenuS()))
        self.positions = {}
        for state, (lat, lon, side) in STATE_MARK.items():
            x, y = project(lat, lon)
            self.positions[state] = (int(x), int(y))

    def state_at(self, pos):
        # clickable state marker (mouse position)
        for state, (x, y) in self.positions.items():
            if state in PLACE_BY_STATE and math.dist(pos, (x, y)) <= self.MARK_R + 4:
                return state
        return None

    def handle_evt(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            change_sc(MenuS())
        if self.back.handle_evt(event):
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            state = self.state_at(event.pos)
            if state:
                change_sc(ComingSS(state, back_to=MapS))

    def draw(self, surf):
        surf.fill((25, 55, 85))
        pts = [project(lat, lon) for lat, lon in PM_OL]
        pygame.draw.polygon(surf, (70, 110, 75), pts)
        pygame.draw.polygon(surf, (150, 190, 150), pts, 2)
        draw_txt(surf, "Peninsular Malaysia", ft_big, WHITE, (20, 20))
        draw_txt(
            surf, "Click a state to choose a spot", ft_smol, (190, 210, 220), (20, 70)
        )
        hovered = self.state_at(pygame.mouse.get_pos())
        for state, (lat, lon, side) in STATE_MARK.items():
            x, y = self.positions[state]
            has_place = state in PLACE_BY_STATE
            rad = self.MARK_R if has_place else 7
            if has_place and state == hovered:
                rad += 3
            if has_place:
                fill = (255, 215, 100) if state == hovered else (240, 185, 60)
                pygame.draw.circle(surf, fill, (x, y), rad)
                pygame.draw.circle(surf, WHITE, (x, y), rad, 2)
                ct = str(len(PLACE_BY_STATE[state]))
                draw_txt(surf, ct, ft_tiny, (30, 30, 30), (x, y), "center")
                lbl_color = WHITE
            else:
                pygame.draw.circle(surf, (100, 110, 120), (x, y), rad)
                lbl_color = (140, 150, 160)
            if side == "L":
                draw_txt(surf, state, ft_tiny, lbl_color, (x - rad - 6, y), "midright")
            else:
                draw_txt(surf, state, ft_tiny, lbl_color, (x + rad + 6, y), "midleft")
        if hovered:
            draw_txt(surf, hovered, ft_mid, WHITE, (725, 110))
            for i, place in enumerate(PLACE_BY_STATE[hovered]):
                row_y = 160 + i * 30
                pygame.draw.circle(
                    surf, BIOME_CLS.get(place["biome"], WHITE), (733, row_y), 7
                )
                draw_txt(
                    surf,
                    place["name"],
                    ft_tiny,
                    (220, 230, 225),
                    (745, row_y),
                    "midleft",
                )
        else:
            draw_txt(
                surf, "Hover a state to preview", ft_tiny, (150, 170, 180), (725, 110)
            )
            draw_txt(
                surf, "its spots. Grey States", ft_tiny, (150, 170, 180), (725, 134)
            )
            draw_txt(surf, "have none yet", ft_tiny, (150, 170, 180), (725, 158))
        self.back.draw(surf)


# main loop
change_sc(MenuS())
while True:
    # event handler (clicks, keys n window close)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            q_game()
        now_scene.handle_evt(event)
    now_scene.draw(screen)

    mouse_x, mouse_y = pygame.mouse.get_pos()
    draw_txt(
        screen,
        f"mouse: {mouse_x}, {mouse_y}",
        ft_smol,
        (180, 210, 190),
        (W - 180, H - 30),
    )

    pygame.display.flip()
    clock.tick(FPS)
