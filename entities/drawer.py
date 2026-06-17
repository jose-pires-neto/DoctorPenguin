import pygame
import math
import random
import os
from config import SPRITESHEET_PATH, SPRITE_COLS, SPRITE_ROWS

class PenguinDrawer:
    def __init__(self, body_color=None):
        self.blink_timer = 0
        self.is_blinking = False
        self.blink_duration = 10 # frames
        self.blink_cooldown = random.randint(120, 300) # frames até piscar de novo
        self.talk_angle = 0
        self.clean_angle = 0
        self.happy_timer = 0
        self.body_color = body_color
        
        # Carrega a spritesheet se disponível
        self.sprites = None
        self.load_spritesheet()

    def load_spritesheet(self):
        """Carrega e fatia a folha de sprites do Club Penguin.
        Se falhar, mantém self.sprites = None para ativar o fallback procedural."""
        import sys
        if hasattr(sys, '_MEIPASS'):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        full_path = os.path.join(base_dir, SPRITESHEET_PATH)
        
        if not os.path.exists(full_path):
            print(f"[Drawer] Arquivo {full_path} não encontrado. Usando renderizador procedural.")
            return

        try:
            sheet = pygame.image.load(full_path).convert_alpha()
            
            # Aplica recoloração se houver uma cor definida
            if self.body_color is not None:
                width, height = sheet.get_size()
                pxarray = pygame.PixelArray(sheet)
                for x in range(width):
                    for y in range(height):
                        c = sheet.unmap_rgb(pxarray[x, y])
                        r, g, b, a = c
                        # Identifica os pixels azuis (onde o canal azul domina os demais)
                        if a > 0 and b > max(r, g) + 15:
                            # Isola a luminosidade para manter o sombreamento intacto
                            lum = (0.299*r + 0.587*g + 0.114*b) / 255.0
                            
                            # Multiplica pela nova cor (com um pequeno boost no brilho base)
                            new_r = min(255, int(self.body_color[0] * lum * 1.8))
                            new_g = min(255, int(self.body_color[1] * lum * 1.8))
                            new_b = min(255, int(self.body_color[2] * lum * 1.8))
                            pxarray[x, y] = sheet.map_rgb((new_r, new_g, new_b, a))
                pxarray.close()
                
            sheet_w, sheet_h = sheet.get_size()
            
            # Dimensões aproximadas de cada frame
            frame_w = sheet_w / SPRITE_COLS
            frame_h = sheet_h / SPRITE_ROWS
            
            self.sprites = []
            for r in range(SPRITE_ROWS):
                row_frames = []
                for c in range(SPRITE_COLS):
                    x = c * 64
                    y = r * 64
                    w = 64
                    h = 64
                    
                    # Corta o frame
                    rect = pygame.Rect(x, y, w, h)
                    sub = sheet.subsurface(rect)
                    
                    row_frames.append(sub)
                self.sprites.append(row_frames)
                
            # --- AUTO-MIRROR PARA FRAMES FALTANTES ---
            # Se alguma célula estiver vazia, tentamos espelhar da direção oposta
            # Direções: 0:S, 1:SW, 2:W, 3:NW, 4:N, 5:NE, 6:E, 7:SE
            mirror_map = {
                5: 3, # NE espelha de NW
                6: 2, # E espelha de W
                7: 1  # SE espelha de SW
            }
            
            for r in range(SPRITE_ROWS):
                for missing_col, source_col in mirror_map.items():
                    # Checa se o frame está vazio (bounding rect width == 0)
                    if self.sprites[r][missing_col].get_bounding_rect().width == 0:
                        # Espelha o frame de origem
                        self.sprites[r][missing_col] = pygame.transform.flip(self.sprites[r][source_col], True, False)
                        print(f"[Drawer] Frame [{r}][{missing_col}] vazio! Gerado automaticamente espelhando [{r}][{source_col}].")

            # Agora aplica a escala em todos
            for r in range(SPRITE_ROWS):
                for c in range(SPRITE_COLS):
                    self.sprites[r][c] = pygame.transform.scale(self.sprites[r][c], (80, 80))
            
            print("[Drawer] Spritesheet fatiada com sucesso em 8 direções.")
        except Exception as e:
            print(f"[Drawer] Falha ao fatiar spritesheet: {e}. Usando renderizador procedural.")
            self.sprites = None

    def update_animation(self, state):
        """Atualiza os temporizadores e estados das animações."""
        # Piscar de olhos (usado apenas no fallback procedural)
        self.blink_timer += 1
        if self.is_blinking:
            if self.blink_timer >= self.blink_duration:
                self.is_blinking = False
                self.blink_timer = 0
                self.blink_cooldown = random.randint(120, 300)
        else:
            if self.blink_timer >= self.blink_cooldown:
                self.is_blinking = True
                self.blink_timer = 0
                
        # Animação de fala
        if state == "TALKING":
            self.talk_angle += 0.2
        else:
            self.talk_angle = 0
            
        # Animação de faxina
        if state == "CLEANING":
            self.clean_angle += 0.15
        else:
            self.clean_angle = 0
            
        # Animação alegre
        if state == "HAPPY":
            self.happy_timer += 0.2
        else:
            self.happy_timer = 0

    def draw(self, surface, x, y, state, mouse_pos, direction_idx=0):
        """Desenha o pinguim. Se a spritesheet foi carregada com sucesso, renderiza o sprite;
        caso contrário, usa o desenho procedural."""
        self.update_animation(state)
        
        # Se os sprites do Club Penguin estiverem carregados, usa eles!
        if self.sprites:
            self.draw_sprite(surface, x, y, state, direction_idx)
        else:
            # Fallback procedural
            self.draw_procedural(surface, x, y, state, mouse_pos)

    def draw_sprite(self, surface, x, y, state, direction_idx):
        """Desenha o sprite correto baseado no estado e direção."""
        now = pygame.time.get_ticks()
        
        # Mapeia o estado para a linha da spritesheet correspondente
        # Linha 0: Idle / Parado
        # Linha 1: Walk Frame 1
        # Linha 2: Walk Frame 2
        # Linha 3: Sitting / Sentado
        
        sprite_to_draw = None
        offset_y = 0
        
        if state == "WANDERING":
            # Ciclo de caminhada de 4 frames: Parado -> Walk1 -> Parado -> Walk2
            frame_idx = (int(now / 150) % 4)
            if frame_idx == 0 or frame_idx == 2:
                sprite_to_draw = self.sprites[0][direction_idx] # Parado
            elif frame_idx == 1:
                sprite_to_draw = self.sprites[1][direction_idx] # Walk 1
            else:
                sprite_to_draw = self.sprites[2][direction_idx] # Walk 2
                
        elif state == "SITTING" or state == "POMODORO":
            sprite_to_draw = self.sprites[3][direction_idx] # Sentado
            
        elif state == "HAPPY":
            # Animação de pulo alegre (alterna entre em pé e sentado, e pula no Y)
            offset_y = -abs(math.sin(self.happy_timer) * 20)
            if offset_y > -5:
                # Efeito de agachamento antes/depois do pulo
                sprite_to_draw = self.sprites[3][direction_idx] # Sentado/Agachado
            else:
                sprite_to_draw = self.sprites[0][direction_idx] # Parado/Em pé
                
        elif state == "CLEANING":
            # Faxina: Caminha muito rápido com tremedeira
            offset_y = random.randint(-2, 2)
            frame_idx = (int(now / 60) % 4)
            if frame_idx == 0 or frame_idx == 2:
                sprite_to_draw = self.sprites[0][direction_idx]
            elif frame_idx == 1:
                sprite_to_draw = self.sprites[1][direction_idx]
            else:
                sprite_to_draw = self.sprites[2][direction_idx]
                
        elif state == "TALKING":
            # Falando: Fica parado mas wiggla o corpo de leve
            offset_y = math.sin(now * 0.01) * 2
            sprite_to_draw = self.sprites[0][direction_idx]
            
        else: # IDLE, GRUMPY, etc.
            sprite_to_draw = self.sprites[0][direction_idx]

        if sprite_to_draw:
            # Centraliza a base do sprite no (x, y)
            rect = sprite_to_draw.get_rect()
            rect.midbottom = (int(x), int(y + offset_y))
            surface.blit(sprite_to_draw, rect)
            
            # Desenha vassoura procedural na mão se estiver faxinando!
            if state == "CLEANING":
                # Desenha a vassoura no lado correspondente à direção do pinguim
                broom_angle = math.sin(self.clean_angle * 3) * 15
                
                # Se estiver virado para a esquerda (direções 5, 6, 7), vassoura fica à esquerda
                if direction_idx in [5, 6, 7]:
                    bx_start, by_start = x - 15, y - 30 + offset_y
                    bx_end, by_end = x - 40 + broom_angle, y - 10 + offset_y
                else:
                    # Caso contrário, à direita
                    bx_start, by_start = x + 15, y - 30 + offset_y
                    bx_end, by_end = x + 40 + broom_angle, y - 10 + offset_y
                    
                pygame.draw.line(surface, (139, 69, 19), (int(bx_start), int(by_start)), (int(bx_end), int(by_end)), 4)
                brush_points = [
                    (int(bx_end), int(by_end)),
                    (int(bx_end - 8), int(by_end + 12)),
                    (int(bx_end + 12), int(by_end + 10))
                ]
                pygame.draw.polygon(surface, (218, 165, 32), brush_points)

    def draw_procedural(self, surface, x, y, state, mouse_pos):
        """Renderizador procedural em vetor para fallback se não carregar a imagem."""
        # --- PARÂMETROS E DEFORMAÇÃO DA ANIMAÇÃO ---
        now = pygame.time.get_ticks()
        
        resp = math.sin(now * 0.003) * 2
        width = 80
        height = 100 + resp
        
        offset_y = 0
        scale_x = 1.0
        
        if state == "HAPPY":
            offset_y = -abs(math.sin(self.happy_timer) * 25)
            if offset_y > -5:
                height -= 8
                width += 4
        elif state == "CLEANING":
            offset_y = random.randint(-2, 2)
            scale_x = abs(math.sin(self.clean_angle * 2.0))
            if scale_x < 0.1:
                scale_x = 0.1
                
        px = x - (width * scale_x) / 2
        py = y - height + offset_y
        
        # --- DESENHO DAS PATAS (PÉS) ---
        foot_color = (255, 140, 0)
        foot_w = int(24 * scale_x)
        foot_h = 12
        foot_y = y - 4 + offset_y
        
        foot_offset_l = 0
        foot_offset_r = 0
        if state == "HAPPY":
            foot_offset_l = math.sin(self.happy_timer * 1.5) * 4
            foot_offset_r = -math.sin(self.happy_timer * 1.5) * 4
        elif state == "CLEANING":
            foot_offset_l = random.randint(-3, 3)
            foot_offset_r = random.randint(-3, 3)

        # Pé Esquerdo
        pygame.draw.ellipse(surface, foot_color, 
                            (int(x - 32 * scale_x), int(foot_y + foot_offset_l), foot_w, foot_h))
        # Pé Direito
        pygame.draw.ellipse(surface, foot_color, 
                            (int(x + 8 * scale_x), int(foot_y + foot_offset_r), foot_w, foot_h))

        # --- CORPO PRINCIPAL ---
        body_color = self.body_color if self.body_color else (15, 15, 15)
        pygame.draw.ellipse(surface, body_color, (int(px), int(py), int(width * scale_x), int(height)))
        
        # --- BARRIGA (BRANCA) ---
        belly_color = (245, 245, 245)
        belly_w = int(width * 0.72 * scale_x)
        belly_h = int(height * 0.75)
        bx = x - belly_w / 2
        by = py + height * 0.22
        pygame.draw.ellipse(surface, belly_color, (int(bx), int(by), int(belly_w), int(belly_h)))
        
        # --- OLHOS (COM RASTREAMENTO DO MOUSE) ---
        eye_color = (255, 255, 255)
        pupil_color = (0, 0, 0)
        
        eye_w = int(14 * scale_x) if scale_x > 0.3 else 3
        eye_h = 18
        eye_y = py + height * 0.2
        
        lex = x - 18 * scale_x - eye_w / 2
        rex = x + 18 * scale_x - eye_w / 2
        
        if self.is_blinking and state != "CLEANING":
            pygame.draw.line(surface, body_color, (int(x - 24 * scale_x), int(eye_y + 9)), 
                             (int(x - 8 * scale_x), int(eye_y + 9)), 2)
            pygame.draw.line(surface, body_color, (int(x + 8 * scale_x), int(eye_y + 9)), 
                             (int(x + 24 * scale_x), int(eye_y + 9)), 2)
        else:
            pygame.draw.ellipse(surface, eye_color, (int(lex), int(eye_y), eye_w, eye_h))
            pygame.draw.ellipse(surface, eye_color, (int(rex), int(eye_y), eye_w, eye_h))
            
            l_center_x = lex + eye_w / 2
            l_center_y = eye_y + eye_h / 2
            
            dx_l = mouse_pos[0] - l_center_x
            dy_l = mouse_pos[1] - l_center_y
            dist_l = math.hypot(dx_l, dy_l) or 1
            
            r_center_x = rex + eye_w / 2
            r_center_y = eye_y + eye_h / 2
            
            dx_r = mouse_pos[0] - r_center_x
            dy_r = mouse_pos[1] - r_center_y
            dist_r = math.hypot(dx_r, dy_r) or 1
            
            max_shift = 3
            shift_x_l = (dx_l / dist_l) * max_shift * scale_x
            shift_y_l = (dy_l / dist_l) * max_shift
            shift_x_r = (dx_r / dist_r) * max_shift * scale_x
            shift_y_r = (dy_r / dist_r) * max_shift
            
            pygame.draw.circle(surface, pupil_color, 
                               (int(l_center_x + shift_x_l), int(l_center_y + shift_y_l)), 4)
            pygame.draw.circle(surface, pupil_color, 
                               (int(r_center_x + shift_x_r), int(r_center_y + shift_y_r)), 4)
            
            pygame.draw.circle(surface, eye_color, 
                               (int(l_center_x + shift_x_l - 1), int(l_center_y + shift_y_l - 1)), 1)
            pygame.draw.circle(surface, eye_color, 
                               (int(r_center_x + shift_x_r - 1), int(r_center_y + shift_y_r - 1)), 1)

        # --- BANDANA HACKER ---
        bandana_color = (200, 10, 10)
        bandana_points = [
            (int(x - 34 * scale_x), int(py + height * 0.18)),
            (int(x + 34 * scale_x), int(py + height * 0.18)),
            (int(x + 28 * scale_x), int(py + height * 0.04)),
            (int(x - 28 * scale_x), int(py + height * 0.04))
        ]
        pygame.draw.polygon(surface, bandana_color, bandana_points)
        knot_points = [
            (int(x - 34 * scale_x), int(py + height * 0.15)),
            (int(x - 44 * scale_x), int(py + height * 0.12)),
            (int(x - 42 * scale_x), int(py + height * 0.22))
        ]
        pygame.draw.polygon(surface, bandana_color, knot_points)

        # --- BICO ---
        beak_color = (255, 165, 0)
        beak_y = py + height * 0.35
        beak_w = int(20 * scale_x)
        beak_h = 14
        
        talking_factor = 0
        if state == "TALKING":
            talking_factor = abs(math.sin(self.talk_angle)) * 8
            
        pt_top = [
            (int(x - beak_w / 2), int(beak_y)),
            (int(x + beak_w / 2), int(beak_y)),
            (int(x), int(beak_y + beak_h / 2))
        ]
        pygame.draw.polygon(surface, beak_color, pt_top)
        
        pt_bottom = [
            (int(x - beak_w * 0.4), int(beak_y + 2)),
            (int(x + beak_w * 0.4), int(beak_y + 2)),
            (int(x), int(beak_y + beak_h / 2 + talking_factor))
        ]
        pygame.draw.polygon(surface, (230, 130, 0), pt_bottom)

        # --- ASAS / NADADEIRAS ---
        flipper_w = int(14 * scale_x) if scale_x > 0.2 else 2
        flipper_h = 45
        flipper_y = py + height * 0.35
        
        flap = 0
        if state == "HAPPY":
            flap = math.sin(self.happy_timer * 2.0) * 15
        elif state == "CLEANING":
            flap = random.randint(-5, 5)

        l_flipper = pygame.Surface((flipper_w or 1, flipper_h), pygame.SRCALPHA)
        pygame.draw.ellipse(l_flipper, body_color, (0, 0, flipper_w or 1, flipper_h))
        rot_l = pygame.transform.rotate(l_flipper, 25 - flap)
        surface.blit(rot_l, (int(x - 40 * scale_x - rot_l.get_width() / 2), int(flipper_y)))
        
        if state == "CLEANING" and scale_x > 0.4:
            broom_angle = math.sin(self.clean_angle * 3) * 20
            broom_start = (int(x + 20), int(flipper_y + 15))
            broom_end = (int(x + 50 + broom_angle), int(flipper_y + 35))
            pygame.draw.line(surface, (139, 69, 19), broom_start, broom_end, 4)
            
            brush_points = [
                broom_end,
                (int(broom_end[0] - 10), int(broom_end[1] + 15)),
                (int(broom_end[0] + 15), int(broom_end[1] + 12))
            ]
            pygame.draw.polygon(surface, (218, 165, 32), brush_points)
            
            r_flipper = pygame.Surface((flipper_w or 1, flipper_h), pygame.SRCALPHA)
            pygame.draw.ellipse(r_flipper, body_color, (0, 0, flipper_w or 1, flipper_h))
            rot_r = pygame.transform.rotate(r_flipper, -45)
            surface.blit(rot_r, (int(x + 30 * scale_x - rot_r.get_width() / 2), int(flipper_y)))
        else:
            r_flipper = pygame.Surface((flipper_w or 1, flipper_h), pygame.SRCALPHA)
            pygame.draw.ellipse(r_flipper, body_color, (0, 0, flipper_w or 1, flipper_h))
            rot_r = pygame.transform.rotate(r_flipper, -25 + flap)
            surface.blit(rot_r, (int(x + 40 * scale_x - rot_r.get_width() / 2), int(flipper_y)))
            
    def get_hitbox(self, x, y):
        """Retorna o retângulo de colisão aproximado do pinguim para detecção de hover/click."""
        # Se os sprites estiverem carregados, a caixa de colisão é ligeiramente maior
        if self.sprites:
            return pygame.Rect(x - 36, y - 90, 72, 90)
        return pygame.Rect(x - 55, y - 105, 110, 110)
