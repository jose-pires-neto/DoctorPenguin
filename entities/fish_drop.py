import pygame
import math
import random

def draw_fish(surface, x, y, scale=1.0):
    """Desenha um peixe simples usando primitivas do pygame"""
    w = 30 * scale
    h = 15 * scale
    # Corpo
    pygame.draw.ellipse(surface, (0, 150, 255), (x - w/2, y - h/2, w, h))
    # Rabo
    pygame.draw.polygon(surface, (0, 150, 255), [
        (x + w/2 - 5, y),
        (x + w/2 + 10, y - 10),
        (x + w/2 + 10, y + 10)
    ])
    # Olho
    pygame.draw.circle(surface, (255, 255, 255), (x - w/4, y - 2), int(3*scale))
    pygame.draw.circle(surface, (0, 0, 0), (x - w/4 - 1, y - 2), int(1.5*scale))

class FishDrop:
    def __init__(self, screen_width):
        self.x = random.randint(100, screen_width - 100)
        self.y = -50
        self.vx = random.uniform(-2, 2)
        self.vy = 0
        self.active = True
        self.gravity = 0.2
        
        self.width = 40
        self.height = 20
        
        self.expire_time = 0
        self.landed = False
        
    def update(self, screen_height):
        if not self.active: return
        
        if not self.landed:
            self.vy += self.gravity
            self.x += self.vx
            self.y += self.vy
            
            if self.y >= screen_height - 30:
                self.y = screen_height - 30
                self.vy = -self.vy * 0.4
                self.vx *= 0.8
                if abs(self.vy) < 1.0:
                    self.landed = True
                    self.expire_time = pygame.time.get_ticks() + 5000 # 5 segundos pra pegar
        else:
            if pygame.time.get_ticks() > self.expire_time:
                self.active = False
                
    def draw(self, surface):
        if not self.active: return
        
        # Piscar antes de sumir
        if self.landed:
            time_left = self.expire_time - pygame.time.get_ticks()
            if time_left < 2000 and (pygame.time.get_ticks() // 200) % 2 == 0:
                return # Pisca
                
        draw_fish(surface, self.x, self.y)
        
    def check_click(self, mouse_pos):
        if not self.active: return False
        # Area de clique um pouco maior que o peixe
        rect = pygame.Rect(self.x - 25, self.y - 15, 50, 30)
        if rect.collidepoint(mouse_pos):
            self.active = False
            return True
        return False
