import pygame
import math

def draw_broom(surface, penguin_x, penguin_y, time_ms):
    """Desenha uma vassourinha balançando usando primitivas"""
    # Movimento de balanço usando senóide
    angle = math.sin(time_ms / 200.0) * 15
    
    # Centro de rotação é a "mão" do pinguim
    center_x = penguin_x - 15
    center_y = penguin_y + 5
    
    # Criar uma surface temporária para a vassoura
    broom_surf = pygame.Surface((15, 40), pygame.SRCALPHA)
    
    # Cabo da vassoura
    pygame.draw.rect(broom_surf, (139, 69, 19), (6, 0, 3, 30))
    # Cerdas
    pygame.draw.polygon(broom_surf, (218, 165, 32), [(7, 25), (0, 40), (15, 40)])
    
    # Rotacionar
    rotated_broom = pygame.transform.rotate(broom_surf, angle)
    rect = rotated_broom.get_rect(center=(center_x, center_y))
    
    surface.blit(rotated_broom, rect.topleft)

def draw_zzz(surface, penguin_x, penguin_y, time_ms):
    """Desenha letrinhas Zzz flutuantes"""
    # 3 letrinhas Z em diferentes estágios
    for i in range(3):
        # Deslocamento no tempo para cada Z
        offset = i * 1000
        cycle = (time_ms + offset) % 3000
        
        # Posição baseada no ciclo de vida (sobe aos poucos)
        progress = cycle / 3000.0 # 0.0 a 1.0
        
        if progress < 0.1: continue # Delay inicial
        
        alpha = int(255 * math.sin(progress * math.pi)) # Fade in / Fade out
        
        # Movimento oscilante horizontal enquanto sobe
        x = penguin_x + 10 + math.sin(progress * 10) * 10
        y = penguin_y - 10 - (progress * 30)
        
        # Desenhar o 'Z' usando linhas ou texto, vamos usar font padrão
        font = pygame.font.SysFont("comicsansms", 16 - (i*2))
        
        text_surf = font.render("Z", True, (150, 200, 255))
        text_surf.set_alpha(alpha)
        surface.blit(text_surf, (x, y))

def draw_stethoscope(surface, penguin_x, penguin_y):
    """Desenha um estetoscópio estilizado ao redor do pescoço do pinguim"""
    # Fone (em cima)
    pygame.draw.arc(surface, (40, 40, 40), (penguin_x - 10, penguin_y - 15, 20, 20), 0, math.pi, 2)
    # Fio descendo
    pygame.draw.lines(surface, (40, 40, 40), False, [
        (penguin_x - 10, penguin_y - 5),
        (penguin_x - 5, penguin_y + 5),
        (penguin_x, penguin_y + 10),
        (penguin_x + 5, penguin_y + 10),
        (penguin_x + 10, penguin_y + 5)
    ], 2)
    # Ponta redonda (Sensor)
    pygame.draw.circle(surface, (192, 192, 192), (penguin_x + 10, penguin_y + 5), 4)
    pygame.draw.circle(surface, (40, 40, 40), (penguin_x + 10, penguin_y + 5), 4, 1)
