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
    def __init__(self, text, x, y, width, max_height=200):
        """Cria um balão de diálogo estilo hacker terminal.
        x, y representam o canto superior esquerdo do balão."""
        self.full_text = text
        self.current_text = ""
        self.x = x
        self.y = y
        self.width = width
        self.max_height = max_height
        
        # Typewriter effect (máquina de escrever)
        self.char_index = 0
        self.last_char_time = 0
        self.typing_speed = 0.02 # segundos por caractere
        self.is_typing = True
        
        # Fontes HQ
        self.font = pygame.font.SysFont("Comic Sans MS", 14)
        if not pygame.font.match_font("comic sans ms"):
            self.font = pygame.font.SysFont("Arial", 14, bold=True)
        self.title_font = pygame.font.SysFont("Arial", 14, bold=True)
        self.buttons = []
        self.lines = []
        self.finished_typing_sound = False
        
    def set_text(self, text):
        self.full_text = text
        self.current_text = ""
        self.char_index = 0
        self.last_char_time = 0
        self.is_typing = True
        self.lines = []
        self.buttons.clear()
        self.finished_typing_sound = False
        
    def set_text_instant(self, text):
        """Atualiza o texto imediatamente sem o efeito de máquina de escrever"""
        if text != self.full_text:
            self.full_text = text
            self.current_text = text
            self.char_index = len(text)
            self.is_typing = False
            self.last_char_time = 0
            # A conversão para linhas ocorrerá no próximo update()
        
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

    def update(self, mouse_pos):
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
                        try:
                            winsound.Beep(1200, 15)
                        except:
                            pass
                else:
                    self.is_typing = False
                    
        # Converte o texto atual em linhas limitando à largura máxima permitida
        max_allowed_width = 280
        self.lines = self._wrap_text(self.current_text, max_allowed_width - 24)
        
        # Calcula a largura dinâmica com base no que está visível agora
        max_line_width = 0
        for line in self.lines:
            w, _ = self.font.size(line)
            if w > max_line_width:
                max_line_width = w
                
        # Adiciona padding
        new_width = max_line_width + 24
        
        # Garante que tenha largura suficiente para os botões se eles estiverem visíveis
        has_buttons = len(self.buttons) > 0 and not self.is_typing
        if has_buttons:
            min_btn_width = len(self.buttons) * 70 + (len(self.buttons) + 1) * 10
            if new_width < min_btn_width:
                new_width = min_btn_width
                
        # Define largura mínima para não ficar estranho
        if new_width < 60:
            new_width = 60
            
        self.width = new_width
        
        # Altura dinâmica baseada na quantidade de linhas AGORA
        text_height = max(1, len(self.lines)) * 20
        self.max_height = text_height + (45 if has_buttons else 20)
        
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
        pygame.draw.rect(surface, SHADOW_COLOR, shadow_rect, border_radius=15)
        
        # 2. Desenha o fundo do balão (Branco Comic)
        bubble_rect = pygame.Rect(self.x, self.y, self.width, self.max_height)
        pygame.draw.rect(surface, BG_COLOR, bubble_rect, border_radius=15)
        pygame.draw.rect(surface, BORDER_COLOR, bubble_rect, 3, border_radius=15)
        
        # 3. Desenha o ponteiro do balão apontando para o pinguim (centro)
        pointer_pts = [
            (self.x + self.width // 2 - 15, self.y + self.max_height - 3),
            (self.x + self.width // 2 + 15, self.y + self.max_height - 3),
            (self.x + self.width // 2, self.y + self.max_height + 25)
        ]
        
        # Sombra do ponteiro
        pygame.draw.polygon(surface, SHADOW_COLOR, [
            (pt[0] + 3, pt[1] + 3) for pt in pointer_pts
        ])
        
        # Ponteiro real
        pygame.draw.polygon(surface, BG_COLOR, pointer_pts)
        pygame.draw.line(surface, BORDER_COLOR, pointer_pts[0], pointer_pts[2], 3)
        pygame.draw.line(surface, BORDER_COLOR, pointer_pts[1], pointer_pts[2], 3)
        
        # Linha para apagar a borda do balão onde o ponteiro encosta
        pygame.draw.line(surface, BG_COLOR, (pointer_pts[0][0] + 3, pointer_pts[0][1] + 1), 
                         (pointer_pts[1][0] - 3, pointer_pts[1][1] + 1), 5)

        # 4. Desenha o texto digitado linha por linha
        text_y = self.y + 12
        for line in self.lines:
            text_surf = self.font.render(line, True, TEXT_COLOR)
            surface.blit(text_surf, (self.x + 12, text_y))
            text_y += 18
            
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
