import pygame
import math

def draw_broom(surface, penguin_x, penguin_y, time_ms):
    """Desenha uma vassourinha balançando usando primitivas"""
    # Movimento de balanço usando senóide
    angle = math.sin(time_ms / 200.0) * 15
    
    # Centro de rotação é a "mão" do pinguim
    center_x = penguin_x - 15
    center_y = penguin_y - 35
    
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
        y = penguin_y - 70 - (progress * 30)
        
        # Desenhar o 'Z' usando linhas ou texto, vamos usar font padrão
        font = pygame.font.SysFont("comicsansms", 16 - (i*2))
        
        text_surf = font.render("Z", True, (150, 200, 255))
        text_surf.set_alpha(alpha)
        surface.blit(text_surf, (x, y))

def draw_stethoscope(surface, penguin_x, penguin_y):
    """Desenha um estetoscópio estilizado ao redor do pescoço do pinguim"""
    # Fone (em cima)
    pygame.draw.arc(surface, (40, 40, 40), (penguin_x - 10, penguin_y - 55, 20, 20), 0, math.pi, 2)
    # Fio descendo
    pygame.draw.lines(surface, (40, 40, 40), False, [
        (penguin_x - 10, penguin_y - 45),
        (penguin_x - 5, penguin_y - 35),
        (penguin_x, penguin_y - 30),
        (penguin_x + 5, penguin_y - 30),
        (penguin_x + 10, penguin_y - 35)
    ], 2)
    # Ponta redonda (Sensor)
    pygame.draw.circle(surface, (192, 192, 192), (penguin_x + 10, penguin_y - 35), 4)
    pygame.draw.circle(surface, (40, 40, 40), (penguin_x + 10, penguin_y - 35), 4, 1)

def draw_glasses(surface, penguin_x, penguin_y):
    """Desenha um óculos de leitura na cara do pinguim"""
    # Lente esquerda
    pygame.draw.rect(surface, (20, 20, 20), (penguin_x - 10, penguin_y - 33, 8, 6), 2, border_radius=2)
    # Lente direita
    pygame.draw.rect(surface, (20, 20, 20), (penguin_x + 2, penguin_y - 33, 8, 6), 2, border_radius=2)
    # Ponte do nariz
    pygame.draw.line(surface, (20, 20, 20), (penguin_x - 2, penguin_y - 30), (penguin_x + 2, penguin_y - 30), 2)

def draw_ice_hole(surface, x, y):
    """Desenha um buraco de pesca no gelo no chão"""
    # Borda de gelo/neve
    pygame.draw.ellipse(surface, (200, 230, 255), (x - 25, y - 10, 50, 20))
    # Buraco escuro (água)
    pygame.draw.ellipse(surface, (10, 50, 100), (x - 20, y - 7, 40, 14))

def draw_fishing_rod(surface, penguin_x, penguin_y, direction_idx, time_ms, fishing_state, fishing_start_time):
    """Desenha a vara de pescar, a linha, a boia e o peixe sendo puxado"""
    # Direção leste (6) o buraco estará à direita. Se for outra, adaptamos, mas assumimos que o pinguim está virado para a direita.
    is_right = (direction_idx in [5, 6, 7] or direction_idx == 0) # Assumindo 0 como S/Right também no fallback
    
    offset_x = 40 if is_right else -40
    hole_x = penguin_x + offset_x
    hole_y = penguin_y + 40
    
    # Base da vara (na mão do pinguim)
    rod_base_x = penguin_x + (15 if is_right else -15)
    rod_base_y = penguin_y - 20
    
    # Ponta da vara
    rod_tip_x = penguin_x + (35 if is_right else -35)
    rod_tip_y = penguin_y - 60
    
    # Boia
    bobber_x = hole_x
    bobber_y = hole_y - 5
    
    # Animações
    if fishing_state == "WAITING":
        # Boia subindo e descendo suavemente
        bobber_y += math.sin(time_ms / 200.0) * 2
    elif fishing_state == "TUG":
        # Boia afunda rapidamente
        bobber_y += 5
        rod_tip_y += 10 # Vara enverga
    elif fishing_state == "PULL":
        # Puxando o peixe (vara pra trás)
        rod_tip_x = penguin_x + (-10 if is_right else 10)
        rod_tip_y = penguin_y - 70
        
    # Desenhar a Vara
    pygame.draw.line(surface, (139, 69, 19), (rod_base_x, rod_base_y), (rod_tip_x, rod_tip_y), 3)
    
    if fishing_state in ["WAITING", "TUG"]:
        # Desenhar Linha de Pesca até a boia
        pygame.draw.line(surface, (200, 200, 200), (rod_tip_x, rod_tip_y), (bobber_x, bobber_y), 1)
        # Desenhar Boia
        pygame.draw.circle(surface, (255, 50, 50), (int(bobber_x), int(bobber_y)), 4)
        pygame.draw.circle(surface, (255, 255, 255), (int(bobber_x), int(bobber_y - 2)), 2)
    
    elif fishing_state == "PULL":
        # Calcular posição do peixe voando
        # Progress vai de 0.0 a 1.0 em 2000ms
        elapsed = time_ms - fishing_start_time
        progress = min(1.0, elapsed / 2000.0)
        
        # Trajetória parabólica
        fish_x = hole_x - (80 * progress if is_right else -80 * progress)
        fish_y = hole_y - math.sin(progress * math.pi) * 80 - (20 * progress)
        
        # Desenhar Linha até o peixe
        pygame.draw.line(surface, (200, 200, 200), (rod_tip_x, rod_tip_y), (fish_x, fish_y), 1)
        
        # Desenhar Peixe
        fw, fh = 20, 10
        pygame.draw.ellipse(surface, (0, 150, 255), (fish_x - fw/2, fish_y - fh/2, fw, fh))
        # Rabo
        tail_offset = -10 if is_right else 10
        pygame.draw.polygon(surface, (0, 150, 255), [
            (fish_x + tail_offset, fish_y),
            (fish_x + tail_offset * 1.5, fish_y - 8),
            (fish_x + tail_offset * 1.5, fish_y + 8)
        ])
        # Olho
        eye_offset = 4 if is_right else -4
        pygame.draw.circle(surface, (255, 255, 255), (int(fish_x + eye_offset), int(fish_y - 2)), 2)
