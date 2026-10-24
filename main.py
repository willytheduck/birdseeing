import copy
import json
import math
import os
import random
import re
import sys
import pygame

from logic import PLACE_BY_STATE, spwn_burd
from burds import m_burds
from places import pm_places

# Settings (for tweaking)
W, H = 960, 600
FPS = 60
WHITE = (255, 255, 255)
BASE_D = os.path.dirname(os.path.abspath(__file__))

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
MAP_F = os.path.join(BASE_D, "map.png")
MAP_X, MAP_Y, MAP_H = 270, 100, 480


# 1 clickable marker/state
STATE_MARK = {
    "Perlis": (90, 78),
    "Kedah": (112, 140),
    "Penang": (74, 182),
    "Perak": (125, 232),
    "Kelantan": (205, 158),
    "Terengganu": (285, 228),
    "Pahang": (248, 258),
    "Selangor": (152, 314),
    "Kuala Lumpur": (172, 333),
    "Putrajaya": (174, 357),
    "Negeri Sembilan": (240, 328),
    "Melaka": (232, 378),
    "Johor": (290, 392),
}

BIOME_CLS = {
    "Urban Park": (100, 145, 95),
    "Lowland Forest": (45, 105, 55),
    "Coastal Wetland": (90, 145, 160),
    "Island Forest": (60, 140, 120),
    "Deep Jungle": (30, 80, 45),
    "Montane": (70, 110, 100),
}

# tier color
RARITY_C = {
    "F": (170, 170, 170),
    "D": (90, 190, 90),
    "C": (70, 140, 230),
    "B": (170, 90, 220),
    "A": (240, 170, 40),
    "S": (230, 60, 80),
}

HUNT_T = 40  # second/hunt
BIRD_R = 22  # bird circle on hunting screen
HIT_R = BIRD_R + 8  # how close for click

if not os.path.exists(MAP_F):
    raise SystemExit(f"Map image not found. Save your map as: {MAP_F}")
_raw_map = pygame.image.load(MAP_F).convert()
MAP_S = MAP_H / _raw_map.get_height()
map_i = pygame.transform.smoothscale(
    _raw_map, (round(_raw_map.get_width() * MAP_S), MAP_H)
)

# Hints/Help
_icon_cache = {}


def get_i(bird, size):
    key = (bird["name"], size)
    if key not in _icon_cache:
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        color = RARITY_C.get(bird["rarity"], (150, 150, 150))
        pygame.draw.circle(surf, color, (size // 2, size // 2), size // 2)
        initials = "".join(word[0] for word in bird["name"].split()[:2]).upper()
        txt = ft_tiny.render(initials, True, (20, 20, 20))
        surf.blit(txt, txt.get_rect(center=(size // 2, size // 2)))
        _icon_cache[key] = surf
    return _icon_cache[key]


_bg_cache = {}


def make_bg(place):
    name = place["name"]
    if name not in _bg_cache:
        bg = pygame.Surface((W, H))
        base = BIOME_CLS.get(place["biome"], (60, 100, 70))
        bg.fill(base)
        rng = random.Random(name)
        for _ in range(140):
            shade = rng.randint(-25, 25)
            color = tuple(max(0, min(255, c + shade)) for c in base)
            pygame.draw.circle(
                bg, color, (rng.randint(0, W), rng.randint(100, H)), rng.randint(10, 45)
            )
        _bg_cache[name] = bg
    return _bg_cache[name]


def random_st(taken, min_gap=90):
    pos = (W // 2, H // 2)
    for _ in range(200):
        pos = (random.randint(60, W - 60), random.randint(140, H - 60))
        if all(math.dist(pos, other) > min_gap for other in taken):
            break
        return pos


# button
class btn:
    def __init__(self, rect, label, on_click, sub=None, align="center"):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.on_click = on_click
        self.sub = sub
        self.align = align

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
        if self.sub:
            draw_txt(
                surf,
                self.sub,
                ft_tiny,
                (180, 215, 190),
                (self.rect.right - 16, self.rect.centery),
                "midright",
            )
        if self.align == "left":
            draw_txt(
                surf,
                self.label,
                ft_mid,
                WHITE,
                (self.rect.x + 16, self.rect.centery),
                "midleft",
            )
        else:
            draw_txt(surf, self.label, ft_mid, WHITE, self.rect.center, "center")


# Scenes
now_scene = None


def change_sc(scene):
    global now_scene
    now_scene = scene


class Scene:
    # temporary
    def handle_evt(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, surf):
        pass


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
    MARK_R = 9

    def __init__(self):
        self.back = btn((20, H - 70, 140, 44), "Back", lambda: change_sc(MenuS()))
        self.positions = {}
        for state, (img_x, img_y) in STATE_MARK.items():
            self.positions[state] = (
                round(MAP_X + img_x * MAP_S),
                round(MAP_Y + img_y * MAP_S),
            )

    def state_at(self, pos):
        # clickable state marker (mouse position)
        for state, (x, y) in self.positions.items():
            if state in PLACE_BY_STATE and math.dist(pos, (x, y)) <= self.MARK_R + 5:
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
                change_sc(StateS(state))

    def draw(self, surf):
        surf.fill((25, 40, 55))
        surf.blit(map_i, (MAP_X, MAP_Y))
        draw_txt(surf, "Peninsular Malaysia", ft_big, WHITE, (20, 20))
        draw_txt(
            surf, "Click a state to choose a spot", ft_smol, (190, 210, 220), (20, 70)
        )
        hovered = self.state_at(pygame.mouse.get_pos())
        for state, (x, y) in self.positions.items():
            has_place = state in PLACE_BY_STATE
            if has_place:
                rad = self.MARK_R + (3 if state == hovered else 0)
                fill = (40, 150, 110) if state == hovered else (20, 90, 70)
                pygame.draw.circle(surf, fill, (x, y), rad)
                pygame.draw.circle(surf, WHITE, (x, y), rad, 2)
                ct = str(len(PLACE_BY_STATE[state]))
                draw_txt(surf, ct, ft_tiny, WHITE, (x, y), "center")
            else:
                pygame.draw.circle(surf, (110, 120, 130), (x, y), 6)
                pygame.draw.circle(surf, WHITE, (x, y), 6, 2)

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
                surf, "its spots. Grey Marker", ft_tiny, (150, 170, 180), (725, 134)
            )
            draw_txt(surf, "no spots yet :[", ft_tiny, (150, 170, 180), (725, 158))
        self.back.draw(surf)


class StateS:
    # listing the place in 1 state
    def __init__(self, state):
        self.state = state
        self.places = PLACE_BY_STATE[state]

        self.btns = []
        width, height, gap = 600, 56, 8
        x = (W - width) // 2
        for i, place in enumerate(self.places):
            y = 120 + i * (height + gap)
            self.btns.append(
                btn(
                    (x, y, width, height),
                    place["name"],
                    lambda p=place: self.opn_place(p),
                    sub=place["biome"],
                    align="left",
                )
            )
        self.back = btn((20, H - 70, 180, 44), "Back to map", lambda: change_sc(MapS()))

    def opn_place(self, place):
        change_sc(HuntS(place, self.state))

    def handle_evt(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            change_sc(MapS())
        if self.back.handle_evt(event):
            return
        for button in self.btns:
            if button.handle_evt(event):
                break

    def draw(self, surf):
        surf.fill((30, 60, 45))
        draw_txt(surf, self.state, ft_big, WHITE, (20, 16))
        n = len(self.places)
        draw_txt(
            surf,
            f"{n} birdwatching spot{'s' if n != 1 else ''}",
            ft_smol,
            (180, 210, 190),
            (22, 78),
        )
        for button in self.btns:
            button.draw(surf)
        self.back.draw(surf)


class HuntS(Scene):
    def __init__(self, place, back_state):
        self.place = place
        self.back_state = back_state  # state sc to return to
        self.background = make_bg(place)
        self.time_left = float(HUNT_T)
        self.state = "playing"
        self.t = 0.0  # bobbing motion
        self.earned = 0
        self.flash = 0.0  # camera flash, cd to 0
        self.floats = []

        # pick 4-5 burds with fuction and giving random spot
        self.targets = []
        taken = []
        for burd in spwn_burd(place):
            pos = random_st(taken)
            taken.append(pos)
            self.targets.append(
                {
                    "bird": burd,
                    "pos": pos,
                    "found": False,
                    "bob": random.random() * 6.28,
                }
            )

        self.continue_btn = btn(
            (W // 2 - 100, H // 2 + 70, 200, 50), "Continue", self.leave
        )

    def leave(self):
        change_sc(StateS(self.back_state))

    def finish(self):
        self.state = "done"

    def bird_pos(self, target):
        # where burd drawn rn (bobs up n down)
        x, y = target["pos"]
        return (x, y + math.sin(self.t * 2 + target["bob"]) * 3)

    def photograph(self, target):
        burd = target["bird"]
        target["found"] = True
        gain = burd["points"]
        self.earned += gain
        self.flash = 0.25
        x, y = self.burd_pos(target)
        self.floats.append(
            {
                "text": f"+{gain}",
                "x": x,
                "y": y,
                "life": 1.2,
                "color": RARITY_C.get(burd["rarity"], WHITE),
            }
        )
        if all(t["found"] for t in self.targets):
            self.finish()

    def handle_evt(self, event):
        if self.state == "done":
            self.continue_btn.handle_evt(event)
            if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_RETURN,
                pygame.K_SPACE,
                pygame.K_ESCAPE,
            ):
                self.leave()
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.finish()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            best, best_dist = None, HIT_R
            for target in self.targets:
                if target["found"]:
                    continue
                d = math.disc(event.pos, self.bird_pos(target))
                if d <= best_dist:  # closest bird wins
                    best, best_dist = target, d
            if best:
                self.photograph(best)

    def update(self, dt):
        self.t += dt
        self.flash = max(0.0, self.flash - dt)
        for f in self.floats:
            f["life"] -= dt
            f["y"] -= 40 * dt
        self.floats = [f for f in self.floats if f["life"] > 0]

        if self.state == "playing":
            self.time_left -= dt
            if self.time_left >= 0:
                self.time_left = 0
                self.finish()

    def draw(self, surf):
        surf.blit(self.background, (0, 0))

        for target in self.targets:
            x, y = self.bird_pos(target)
            surf.blit(
                get_i(target["bird"], BIRD_R * 2),
                (round(x - BIRD_R), round(y - BIRD_R)),
            )
            if target["found"]:
                pygame.draw.circle(
                    surf, (80, 255, 120), (round(x), round(y)), BIRD_R + 3, 3
                )

        # top for place name, birds to find and time
        pygame.draw.rect(surf, (20, 30, 25), (0, 0, W, 100))
        draw_txt(surf, self.place["name"], ft_mid, WHITE, (16, 10))
        draw_txt(surf, "Find:", ft_smol, (190, 210, 195), (16, 60))
        for i, target in enumerate(self.targets):
            icon_x = 80 + i * 54
            surf.blit(get_i(target["bird"], 44), (icon_x, 42))
            if target["found"]:
                pygame.draw.circle(surf, (80, 255, 120), (icon_x + 22, 64), 25, 3)
        draw_txt(
            surf,
            f"Time: {math.ceil(self.time_left)}",
            ft_mid,
            WHITE,
            (W - 20, 55),
            "topright",
        )

        for f in self.floats:
            draw_txt(
                surf,
                f["text"],
                ft_mid,
                f["color"],
                (round(f["x"]), round(f["y"])),
                "center",
            )

        if self.flash > 0:
            overlay = pygame.Surface((W, H))
            overlay.fill(WHITE)
            overlay.set_alpha(int(160 * self.flash / 0.25))
            surf.blit(overlay, (0, 0))

        if self.state == "done":
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            surf.blit(overlay, (0, 0))
            found = sum(1 for t in self.targets if t["found"])
            draw_txt(
                surf, "Hunt over! :P", ft_big, WHITE, (W // 2, H // 2 - 110), "center"
            )
            draw_txt(
                surf,
                f"Photographed {found}/{len(self.targets)} birds",
                ft_mid,
                WHITE,
                (W // 2, H // 2 - 50),
                "center",
            )
            draw_txt(
                surf,
                f"Points earned: {self.earned}",
                ft_mid,
                (255, 220, 90),
                (W // 2, H // 2 - 10),
                "center",
            )
            self.continue_btn.draw(surf)


# main loop
change_sc(MenuS())
while True:
    dt = clock.tick(FPS)/1000

    # event handler (clicks, keys n window close)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            q_game()
        now_scene.handle_evt(event)
    now_scene.update(dt)
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
