import pygame
import random
import math
from entities.drawer import PenguinDrawer

class Egg:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.clicks = 0
        self.required_clicks = 5
        self.active = True
        self.hatched = False
        
        # Shake effect
        self.shake = 0
        self.last_click_time = 0
        
    def draw(self, surface):
        if not self.active: return
        
        # Desenha o ovo
        draw_x = self.x
        if self.shake > 0:
            draw_x += math.sin(pygame.time.get_ticks() * 0.1) * self.shake
            self.shake -= 0.5
            
        rect = pygame.Rect(draw_x - 9, self.y - 12, 18, 24)
        pygame.draw.ellipse(surface, (240, 240, 240), rect)
        # Sombra/Borda do ovo
        pygame.draw.ellipse(surface, (150, 150, 150), rect, 2)
        
        # Se rachando
        if self.clicks > 2:
            pygame.draw.lines(surface, (100, 100, 100), False, [
                (draw_x - 3, self.y - 9),
                (draw_x + 3, self.y - 3),
                (draw_x - 3, self.y + 3),
                (draw_x + 3, self.y + 9)
            ], 1)
            
    def check_click(self, mouse_pos):
        if not self.active: return False
        
        rect = pygame.Rect(self.x - 9, self.y - 12, 18, 24)
        if rect.collidepoint(mouse_pos):
            self.clicks += 1
            self.shake = 5
            self.last_click_time = pygame.time.get_ticks()
            
            if self.clicks >= self.required_clicks:
                self.active = False
                self.hatched = True
            return True
        return False

class BabyPenguin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.direction_idx = 0
        self.color = (random.randint(20, 255), random.randint(20, 255), random.randint(20, 255))
        self.drawer = PenguinDrawer(body_color=self.color)
        
    def update(self, parent_x, parent_y):
        # Segue o pai
        dx = parent_x - self.x
        dy = parent_y - self.y
        dist = math.hypot(dx, dy)
        
        if dist > 80:
            # Move em direção ao pai
            self.vx = (dx / dist) * 2.0
            self.vy = (dy / dist) * 2.0
            self.x += self.vx
            self.y += self.vy
        else:
            self.vx = 0
            self.vy = 0
            
    def draw(self, surface, mouse_pos):
        # Desenha menor que o pai
        state = "WANDERING" if math.hypot(self.vx, self.vy) > 0.5 else "IDLE_STANDING"
        # Calcula direcao apenas se estiver se movendo
        if math.hypot(self.vx, self.vy) > 0.5:
            angle = math.degrees(math.atan2(-self.vy, self.vx))
            if angle < 0: angle += 360
            sector = int(((angle + 22.5) % 360) / 45)
            sector_to_idx = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 0, 7: 7}
            self.direction_idx = sector_to_idx.get(sector, 0)
            
        # Draw scaled down
        temp_surf = pygame.Surface((150, 150), pygame.SRCALPHA)
        self.drawer.draw(temp_surf, 75, 140, state, mouse_pos, self.direction_idx)
        
        # Escala pela metade
        scaled_surf = pygame.transform.scale(temp_surf, (75, 75))
        
        # Blit centrado e com a base no lugar certo (70 é a metade de 140)
        surface.blit(scaled_surf, (self.x - 37, self.y - 70))
