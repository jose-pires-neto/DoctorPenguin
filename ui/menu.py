import pygame
from config import BG_COLOR, BORDER_COLOR, SHADOW_COLOR
from ui.components import Button

class ContextMenu:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.width = 200
        self.height = 0
        self.is_open = False
        self.buttons = []
        
    def show(self, x, y, buttons_config):
        """
        Abre o menu na posição (x, y).
        buttons_config: lista de dicts [{'text': 'Label', 'callback': func}]
        """
        self.x = x
        self.y = y
        self.buttons.clear()
        
        padding = 10
        btn_height = 30
        
        self.height = padding + len(buttons_config) * (btn_height + padding)
        
        current_y = self.y + padding
        for config in buttons_config:
            btn = Button(
                config['text'],
                self.x + padding,
                current_y,
                self.width - (padding * 2),
                btn_height,
                config['callback']
            )
            self.buttons.append(btn)
            current_y += btn_height + padding
            
        self.is_open = True
        
    def hide(self):
        self.is_open = False
        self.buttons.clear()
        
    def handle_event(self, event, mouse_pos):
        if not self.is_open:
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Clique esquerdo
                clicked = False
                for btn in self.buttons:
                    if btn.check_click(mouse_pos):
                        clicked = True
                        break
                # Qualquer clique esquerdo (nos botões ou fora) fecha o menu
                self.hide()
                return clicked
            elif event.button == 3: # Clique direito fora do menu também o fecha
                self.hide()
                return False
                
        return False
        
    def update(self, mouse_pos):
        if self.is_open:
            for btn in self.buttons:
                btn.update(mouse_pos)
                
    def draw(self, surface):
        if not self.is_open:
            return
            
        # Sombra
        shadow_rect = pygame.Rect(self.x + 5, self.y + 5, self.width, self.height)
        pygame.draw.rect(surface, SHADOW_COLOR, shadow_rect, border_radius=8)
        
        # Fundo do menu
        menu_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, BG_COLOR, menu_rect, border_radius=8)
        pygame.draw.rect(surface, BORDER_COLOR, menu_rect, 2, border_radius=8)
        
        # Botões
        for btn in self.buttons:
            btn.draw(surface)
            
    def get_hitbox(self):
        if not self.is_open:
            return pygame.Rect(0, 0, 0, 0)
        return pygame.Rect(self.x, self.y, self.width, self.height)
