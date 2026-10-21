import copy
import json
import math
import os
import random
import re
import sys
import pygame

from burds import m_burds
from places import pm_places

# Settings (for tweaking)
W, H = 960, 600
FPS = 60
WHITE = (255,255,255)

pygame.init()
screen = pygame.display.set_mode((W,H))
pygame.display.set_caption("Malaya Peninsula Bird Hunter")
clock = pygame.time.Clock()

ft_big = pygame.font.Font(None, 72)
ft_mid = pygame.font.Font(None, 36)
ft_smol = pygame.font.Font(None, 28)

def q_game():
    pygame.quit()
    sys.exit()

#button 
class btn:
    def __init__(self,rect,label,on_click):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.on_click = on_click

    def handle_evt(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.on_click()
                return True
            return False

    def draw(self,surf):
        hover = self.rect.collidepoint(pygame.mouse.get_pos())
        color = (70,120,90) if hover else (50,90,70)
        pygame.draw.rect(surf,color,self.rect,border_radius=8)
        pygame.draw.rect(surf, (200,230,210),self.rect,2,border_radius=8)
        text = ft_mid.render(self.label, True, WHITE)
        surf.blit(text, text.get_rect(center=self.rect.center))

#Scenes
now_scene = None

def change_sc(scene):
    global now_scene
    now_scene = scene

class MenuS:
    def __init__(self):
        x,w = W//2 - 130,260
        self.btns =[
            btn((x,200,w,56),"Go Birdwatching", lambda: change_sc(ComingSS("Map"))),
            btn((x,275,w,56),"Collection", lambda: change_sc(ComingSS("Collection"))),
            btn((x,350,w,56),"Shop", lambda: change_sc(ComingSS("Shop"))),
            btn((x,425,w,56),"Quit", q_game),
        ]
    def handle_evt(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            q_game()
        for btn in self.btns:
            if btn.handle_evt(event):
                break
    def draw(self,surf):
        surf.fill((30, 60, 45))
        title = ft_big.render("Malaya Peninsula Bird Hunter", True, (240, 250, 230))
        surf.blit(title, title.get_rect(center=(W//2,100)))
        sub = ft_smol.render("Find them. Photograph them. Collect em all.", True, (180,210,190))
        surf.blit(sub,sub.get_rect(center=(W//2,150)))
        for btn in self.btns:
            btn.draw(surf)

class ComingSS:
    def __init__(self,name):
        self.name = name
        self.back = btn((20,H- 70,140,44),"Back", lambda: change_sc(MenuS()))

    def handle_evt(self,event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            change_sc(MenuS())
        self.back.handle_evt(event)

    def draw(self,surf):
        surf.fill((30,60,45))
        text = ft_big.render(f"{self.name} - coming soon", True, WHITE)
        surf.blit(text, text.get_rect(center=(W//2,H//2)))
        self.back.draw(surf)
        
#main loop
change_sc(MenuS())
while True:
    #event handler (clicks, keys n window close)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            q_game()
        now_scene.handle_evt(event)
    now_scene.draw(screen)

    mouse_x, mouse_y = pygame.mouse.get_pos()
    coords = ft_smol.render(f"mouse: {mouse_x}, {mouse_y}", True, (180,210,190))
    screen.blit(coords,(W- 180, H-30))

    pygame.display.flip()
    clock.tick(FPS)