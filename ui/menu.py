import pygame
from config import BG_COLOR, BORDER_COLOR, SHADOW_COLOR
from ui.components import Button

class ContextMenu:
    def __init__(self, parent=None):
        self.x = 0
        self.y = 0
        self.width = 200
        self.height = 0
        self.is_open = False
        self.buttons_config = []
        self.buttons = []
        self.parent = parent
        self.child_menu = None
        self.active_submenu_idx = -1
        
    def show(self, x, y, buttons_config):
        """
        Abre o menu na posição (x, y).
        buttons_config: lista de dicts [{'text': 'Label', 'callback': func, 'submenu': [...]}]
        """
        self.x = x
        self.y = y
        self.buttons_config = buttons_config
        self.buttons.clear()
        self.child_menu = None
        self.active_submenu_idx = -1
        
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
                config.get('callback')
            )
            self.buttons.append(btn)
            current_y += btn_height + padding
            
        self.is_open = True
        
    def hide(self):
        self.is_open = False
        self.buttons.clear()
        if self.child_menu:
            self.child_menu.hide()
            self.child_menu = None
        self.active_submenu_idx = -1
        
    def handle_event(self, event, mouse_pos):
        if not self.is_open:
            return False
            
        if self.child_menu:
            if self.child_menu.handle_event(event, mouse_pos):
                return True
                
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Clique esquerdo
                clicked = False
                for i, btn in enumerate(self.buttons):
                    if btn.check_click(mouse_pos):
                        if 'submenu' not in self.buttons_config[i]:
                            clicked = True
                        break
                
                if clicked:
                    # Fecha toda a árvore a partir do menu root
                    node = self
                    while node.parent:
                        node = node.parent
                    node.hide()
                    return True
                
                # Se clicou fora de todos os menus (root e filhos), o hide() é gerenciado pelo chamador
        return False
        
    def update(self, mouse_pos):
        if not self.is_open:
            return
            
        hovered_idx = -1
        for i, btn in enumerate(self.buttons):
            btn.update(mouse_pos)
            if btn.is_hovered:
                hovered_idx = i
                
        if hovered_idx != -1:
            if hovered_idx != self.active_submenu_idx:
                if 'submenu' in self.buttons_config[hovered_idx]:
                    self.active_submenu_idx = hovered_idx
                    self.child_menu = ContextMenu(parent=self)
                    # Abre o submenu ligeiramente ao lado e alinhado com o botão
                    self.child_menu.show(self.x + self.width - 5, self.buttons[hovered_idx].rect.y - 10, self.buttons_config[hovered_idx]['submenu'])
                else:
                    if self.child_menu:
                        self.child_menu.hide()
                        self.child_menu = None
                    self.active_submenu_idx = -1
                    
        if self.child_menu:
            self.child_menu.update(mouse_pos)
                
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
            
        # Desenha submenus por cima
        if self.child_menu:
            self.child_menu.draw(surface)
            
    def get_hitbox(self):
        if not self.is_open:
            return pygame.Rect(0, 0, 0, 0)
            
        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        if self.child_menu:
            rect = rect.union(self.child_menu.get_hitbox())
        return rect
