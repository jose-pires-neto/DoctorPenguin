import pygame
import winsound
import time
from config import (
    BG_COLOR, BORDER_COLOR, TEXT_COLOR, BTN_COLOR, 
    BTN_HOVER_COLOR, BTN_TEXT_COLOR, SHADOW_COLOR
)

class Button:
    def __init__(self, text, x, y, width, height, callback=None):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.callback = callback
        self.is_hovered = False
        self.font = pygame.font.SysFont("Comic Sans MS", 13, bold=True)
        if not pygame.font.match_font("comic sans ms"):
            self.font = pygame.font.SysFont("Arial", 12, bold=True)
        
    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        
    def draw(self, surface):
        # Desenha sombra
        pygame.draw.rect(surface, SHADOW_COLOR, (self.rect.x + 3, self.rect.y + 3, self.rect.width, self.rect.height))
        
        # Cor de fundo baseada no hover
        color = BTN_HOVER_COLOR if self.is_hovered else BTN_COLOR
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, BORDER_COLOR, self.rect, 2) # Borda verde
        
        # Texto centralizado
        text_surf = self.font.render(self.text, True, BTN_TEXT_COLOR)
        tx = self.rect.x + (self.rect.width - text_surf.get_width()) / 2
        ty = self.rect.y + (self.rect.height - text_surf.get_height()) / 2
        surface.blit(text_surf, (int(tx), int(ty)))

    def check_click(self, mouse_pos):
        if self.rect.collidepoint(mouse_pos):
            if self.callback:
                self.callback()
            return True
        return False


class DialogueBubble:
    def __init__(self, text, x, y, width, max_height=200, audio_system=None, voice_system=None):
        """Cria um balão de diálogo estilo hacker terminal.
        x, y representam o canto superior esquerdo do balão."""
        self.full_text = text
        self.current_text = ""
        self.x = x
        self.y = y
        self.width = width
        self.max_height = max_height
        self.audio_system = audio_system
        self.voice_system = voice_system
        
        # Typewriter effect (máquina de escrever)
        self.char_index = 0
        self.last_char_time = 0
        self.typing_speed = 0.02 # segundos por caractere
        self.is_typing = True
        
        # Fontes HQ - Tamanho reduzido
        self.font = pygame.font.SysFont("Comic Sans MS", 12)
        if not pygame.font.match_font("comic sans ms"):
            self.font = pygame.font.SysFont("Arial", 12, bold=True)
        self.title_font = pygame.font.SysFont("Arial", 12, bold=True)
        self.buttons = []
        self.lines = []
        self.finished_typing_sound = False
        self.finished_typing_time = 0
        
    def set_text(self, text):
        self.full_text = text
        self.current_text = ""
        self.char_index = 0
        self.last_char_time = 0
        self.is_typing = True
        self.lines = []
        self.buttons.clear()
        self.finished_typing_sound = False
        
        if self.voice_system:
            self.voice_system.speak(text)
        
    def set_text_instant(self, text):
        """Atualiza o texto imediatamente sem o efeito de máquina de escrever"""
        if text != self.full_text:
            self.full_text = text
            self.current_text = text
            self.char_index = len(text)
            self.is_typing = False
            self.last_char_time = 0
            # A conversão para linhas ocorrerá no próximo update()
            if self.voice_system:
                self.voice_system.speak(text)
        
    def add_buttons(self, button_list):
        """Adiciona botões e os posiciona lado a lado na parte inferior do balão.
        button_list é uma lista de dicionários: [{'text': 'Limpar', 'callback': fn}]"""
        self.buttons.clear()
        
        if not button_list:
            return
            
        num_btns = len(button_list)
        btn_padding = 10
        total_padding = btn_padding * (num_btns + 1)
        btn_width = (self.width - total_padding) // num_btns
        btn_height = 26
        
        # Calcula a posição vertical com base nas linhas de texto
        # Estimamos a altura pelas linhas
        text_height = max(len(self.lines), 3) * 18 + 35
        btn_y = self.y + text_height
        
        # Se for ultrapassar a altura máxima, joga mais para baixo
        if btn_y < self.y + self.max_height - btn_height - 15:
            btn_y = self.y + self.max_height - btn_height - 15
            
        for idx, btn in enumerate(button_list):
            self.buttons.append(Button(btn['text'], 0, 0, btn_width, btn_height, btn['callback']))

    def update(self, mouse_pos, target_x=None, target_y=None):
        self.target_x = target_x
        self.target_y = target_y
        now = time.time()
        
        # Efeito de digitação da fala do pinguim
        if self.is_typing:
            if now - self.last_char_time > self.typing_speed:
                self.char_index += 1
                if self.char_index <= len(self.full_text):
                    self.current_text = self.full_text[:self.char_index]
                    self.last_char_time = now
                    # Bip de digitação
                    if self.char_index % 3 == 0:
                        if not self.audio_system or not self.audio_system.muted:
                            try:
                                winsound.Beep(1200, 15)
                            except:
                                pass
                else:
                    self.is_typing = False
                    self.finished_typing_time = pygame.time.get_ticks()
                    
        # Auto-limpeza do balão após a leitura (8 segundos), exceto se tiver botões pendentes
        if not self.is_typing and self.current_text != "" and not self.buttons:
            if pygame.time.get_ticks() - self.finished_typing_time > 8000:
                self.set_text_instant("")
                    
        # Converte o texto atual em linhas limitando à largura máxima permitida (reduzida de 280 para 220)
        max_allowed_width = 220
        
        # Para evitar que o balão fique mudando de tamanho na animação dos pontinhos, medimos a largura com "..."
        text_for_layout = "..." if self.full_text == "..." else self.current_text
        layout_lines = self._wrap_text(text_for_layout, max_allowed_width - 24)
        
        # Calcula a largura dinâmica com base no que está visível agora
        max_line_width = 0
        for line in layout_lines:
            w, _ = self.font.size(line)
            if w > max_line_width:
                max_line_width = w
                
        # Atualiza self.lines para desenhar o texto real
        if self.full_text == "...":
            self.is_typing = False
            dots_count = int(now * 3) % 4
            self.lines = ["." * dots_count]
        else:
            self.lines = layout_lines
                
        # Adiciona padding
        new_width = max_line_width + 24
        
        # Garante que tenha largura suficiente para os botões se eles estiverem visíveis
        has_buttons = len(self.buttons) > 0 and not self.is_typing
        if has_buttons:
            min_btn_width = len(self.buttons) * 70 + (len(self.buttons) + 1) * 10
            if new_width < min_btn_width:
                new_width = min_btn_width
                
        # Define largura mínima para não ficar estranho
        if self.full_text == "...":
            new_width = 45 # Bem menor para não ficar gigante
        elif new_width < 60:
            new_width = 60
            
        self.width = new_width
        
        # Altura dinâmica baseada na quantidade de linhas AGORA
        text_height = max(1, len(self.lines)) * 18
        self.max_height = text_height + (40 if has_buttons else 15)
        
        self.update_buttons(mouse_pos)
        
    def update_buttons(self, mouse_pos):
        # Atualiza a posição dos botões caso a largura ou x/y do balão tenha mudado
        has_buttons = len(self.buttons) > 0 and not self.is_typing
        if has_buttons:
            btn_padding = 10
            btn_width = (self.width - (btn_padding * (len(self.buttons) + 1))) // len(self.buttons)
            btn_y = self.y + self.max_height - 35
            
            for idx, btn in enumerate(self.buttons):
                btn.rect.x = self.x + btn_padding + idx * (btn_width + btn_padding)
                btn.rect.y = btn_y
                btn.rect.width = btn_width
                btn.update(mouse_pos)
                
    def _wrap_text(self, text, max_w):
        """Algoritmo de Word Wrap clássico para Pygame."""
        words = text.split(' ')
        lines = []
        current_line = []
        
        # Se contiver quebras de linha explícitas (\n), quebra primeiro
        subsections = text.split('\n')
        
        for section in subsections:
            words = section.split(' ')
            current_line = []
            for word in words:
                test_line = ' '.join(current_line + [word])
                # Verifica a largura do texto
                w, _ = self.font.size(test_line)
                if w < max_w:
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
            if current_line:
                lines.append(' '.join(current_line))
                
        return lines

    def draw(self, surface):
        # 1. Desenha a sombra do balão
        shadow_rect = pygame.Rect(self.x + 5, self.y + 5, self.width, self.max_height)
            
        import math
        import time
        now = time.time()
        
        # --- ANIMAÇÕES GLOBAIS DE VIDA (Aplica para ambos os balões) ---
        # Efeito de respiração (pulsa o tamanho) e flutuação (sobe e desce)
        breath = math.sin(now * 4) * 1.0
        float_y = math.sin(now * 2.5) * 2.5
        
        # Salva medidas originais para não quebrar a lógica global
        orig_x, orig_y = self.x, self.y
        orig_w, orig_h = self.width, self.max_height
        
        # Aplica as mutações vitais
        self.x -= breath
        self.y += float_y - breath
        self.width += breath * 2
        self.max_height += breath * 2

        # 3. Desenha o ponteiro do balão dinamicamente apontando para o alvo
        tip_x = self.x + self.width // 2
        tip_y = self.y + self.max_height + 20
        
        # O rabo também ganha um leve "wobble" (movimento independente)
        if hasattr(self, 'target_x') and self.target_x is not None:
            tip_x = self.target_x + math.sin(now * 5) * 2
            
        if hasattr(self, 'target_y') and self.target_y is not None:
            tip_y = self.target_y + math.cos(now * 4) * 2
            
        # Descobre qual borda usar (Top, Bottom, Left, Right)
        margin = 20
        
        is_thought = (self.full_text == "...")
        
        if tip_x > self.x + self.width + 10:
            # Pinguim muito à direita -> Borda DIREITA
            base_cy = max(self.y + margin, min(tip_y, self.y + self.max_height - margin))
            base_cx = self.x + self.width
            pointer_pts = [
                (base_cx - 4, base_cy - 12),
                (base_cx - 4, base_cy + 12),
                (tip_x, tip_y)
            ]
            
        elif tip_x < self.x - 10:
            # Pinguim muito à esquerda -> Borda ESQUERDA
            base_cy = max(self.y + margin, min(tip_y, self.y + self.max_height - margin))
            base_cx = self.x
            pointer_pts = [
                (base_cx + 4, base_cy - 12),
                (base_cx + 4, base_cy + 12),
                (tip_x, tip_y)
            ]
            
        elif tip_y >= self.y + self.max_height:
            # Pinguim está abaixo -> Borda INFERIOR
            base_cx = max(self.x + margin, min(tip_x, self.x + self.width - margin))
            base_cy = self.y + self.max_height
            pointer_pts = [
                (base_cx - 12, base_cy - 4),
                (base_cx + 12, base_cy - 4),
                (tip_x, tip_y)
            ]
            
        else:
            # Pinguim está acima -> Borda SUPERIOR
            base_cx = max(self.x + margin, min(tip_x, self.x + self.width - margin))
            base_cy = self.y
            pointer_pts = [
                (base_cx - 12, base_cy + 4),
                (base_cx + 12, base_cy + 4),
                (tip_x, tip_y)
            ]
        
        # 1. Sombras (Balão e Ponteiro)
        shadow_rect = pygame.Rect(self.x + 5, self.y + 5, self.width, self.max_height)
        pygame.draw.rect(surface, SHADOW_COLOR, shadow_rect, border_radius=15)
        
        if is_thought:
            import math
            now = time.time()
            
            # Animação dos 3 círculos conectores
            dx = tip_x - base_cx
            dy = tip_y - base_cy
            
            # Pulsos e movimentos para as bolhas do rabo
            pulse1 = math.sin(now * 5) * 1
            pulse2 = math.cos(now * 4) * 1
            pulse3 = math.sin(now * 6) * 0.5
            
            circles = [
                (base_cx + dx * 0.25 + math.sin(now)*2, base_cy + dy * 0.25, 5 + pulse1),
                (base_cx + dx * 0.55 + math.cos(now)*2, base_cy + dy * 0.55, 3 + pulse2),
                (base_cx + dx * 0.85, base_cy + dy * 0.85, 2 + pulse3)
            ]
            
            # Bolotas da nuvem (desenhadas ao redor do retângulo)
            bumps = []
            num_bumps = 8
            for i in range(num_bumps):
                angle = (i / num_bumps) * 2 * math.pi
                pulse = math.sin(now * 3 + i) * 1.5
                base_r = 10  # Reduzido de 14 para 10 (nuvem menor)
                r = base_r + pulse
                
                rx = self.width / 2 - 1
                ry = self.max_height / 2 - 1
                
                bx = self.x + self.width/2 + math.cos(angle) * rx
                by = self.y + self.max_height/2 + math.sin(angle) * ry
                bumps.append((bx, by, r))
                
            main_rect = pygame.Rect(self.x, self.y, self.width, self.max_height)
            
            # 1. Sombras (Balão e círculos)
            pygame.draw.rect(surface, SHADOW_COLOR, main_rect.move(4, 4), border_radius=20)
            for bx, by, r in bumps:
                pygame.draw.circle(surface, SHADOW_COLOR, (int(bx)+4, int(by)+4), int(r))
            for cx, cy, cr in circles:
                pygame.draw.circle(surface, SHADOW_COLOR, (int(cx)+4, int(cy)+4), int(cr))
                
            # 2. Bordas Pretas (Tudo desenhado um pouco maior, fundindo a silhueta)
            pygame.draw.rect(surface, BORDER_COLOR, main_rect.inflate(6, 6), border_radius=23)
            for bx, by, r in bumps:
                pygame.draw.circle(surface, BORDER_COLOR, (int(bx), int(by)), int(r + 3))
            for cx, cy, cr in circles:
                pygame.draw.circle(surface, BORDER_COLOR, (int(cx), int(cy)), int(cr + 3))
                
            # 3. Fundo Branco (Por cima do preto, criando o contorno contínuo perfeito!)
            pygame.draw.rect(surface, BG_COLOR, main_rect, border_radius=20)
            for bx, by, r in bumps:
                pygame.draw.circle(surface, BG_COLOR, (int(bx), int(by)), int(r))
            for cx, cy, cr in circles:
                pygame.draw.circle(surface, BG_COLOR, (int(cx), int(cy)), int(cr))
                
        else:
            # Lógica normal do balão de fala
            bubble_rect = pygame.Rect(self.x, self.y, self.width, self.max_height)
            pygame.draw.polygon(surface, SHADOW_COLOR, [
                (pt[0] + 5, pt[1] + 5) for pt in pointer_pts
            ])
            pygame.draw.rect(surface, BG_COLOR, bubble_rect, border_radius=15)
            pygame.draw.rect(surface, BORDER_COLOR, bubble_rect, 3, border_radius=15)
            pygame.draw.polygon(surface, BG_COLOR, pointer_pts)
            pygame.draw.line(surface, BORDER_COLOR, pointer_pts[0], pointer_pts[2], 3)
            pygame.draw.line(surface, BORDER_COLOR, pointer_pts[1], pointer_pts[2], 3)


        # 4. Desenha o texto digitado linha por linha
        text_y = self.y + 8 # Margem superior reduzida
        for line in self.lines:
            text_surf = self.font.render(line, True, TEXT_COLOR)
            surface.blit(text_surf, (self.x + 12, text_y))
            text_y += 18
            
        # Restaura medidas originais
        self.x, self.y = orig_x, orig_y
        self.width, self.max_height = orig_w, orig_h
            
        # 6. Desenha os botões (apenas se terminou de digitar)
        if not self.is_typing:
            for btn in self.buttons:
                btn.draw(surface)

    def handle_event(self, event, mouse_pos):
        """Processa clique nos botões do balão. Retorna True se algum botão foi clicado."""
        if self.is_typing:
            # Pula a digitação se o usuário clicar enquanto digita
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.char_index = len(self.full_text)
                self.current_text = self.full_text
                self.is_typing = False
                # Re-adiciona os botões ajustados na altura correta
                return False
                
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in self.buttons:
                if btn.check_click(mouse_pos):
                    # Som de confirmação do clique
                    if not self.audio_system or not self.audio_system.muted:
                        try:
                            winsound.Beep(800, 80)
                            winsound.Beep(1000, 80)
                        except:
                            pass
                    return True
        return False
        
    def get_hitbox(self):
        """Retorna a caixa de colisão do balão mais a área dos botões para saber se o mouse está sobre a interface."""
        # Adicionamos uma margem de segurança de 15px ao redor
        return pygame.Rect(self.x - 10, self.y - 10, self.width + 30, self.max_height + 30)
