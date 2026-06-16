import pygame
import os
import win32api
import win32con
import win32gui
from config import SCREEN_WIDTH, SCREEN_HEIGHT, INVISIBLE_COLOR

def setup_transparent_window(title="DoctorPenguin"):
    """
    Inicializa o Pygame e configura a janela para ser borderless,
    transparente e clicar através (exceto nos elementos desenhados).
    Retorna a surface (screen) e o HWND da janela.
    """
    # Define a posição da janela na tela (canto superior esquerdo)
    os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"
    
    pygame.init()
    
    # Cria a janela sem bordas
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.NOFRAME)
    pygame.display.set_caption(title)
    
    # Obtém o handle (HWND) da janela recém-criada
    hwnd = win32gui.FindWindow(None, title)
    
    # Configura os estilos estendidos (Layered e Topmost)
    # WS_EX_LAYERED permite transparência por chroma key ou alpha
    # WS_EX_TOPMOST mantém a janela sempre no topo
    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    ex_style |= win32con.WS_EX_LAYERED | win32con.WS_EX_TOPMOST
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)
    
    # Configura a cor invisível (chroma key)
    # Todos os pixels desenhados com INVISIBLE_COLOR ficarão totalmente transparentes (buracos na janela)
    # LWA_COLORKEY faz com que o Windows trate a cor como transparente
    color_key = win32api.RGB(INVISIBLE_COLOR[0], INVISIBLE_COLOR[1], INVISIBLE_COLOR[2])
    win32gui.SetLayeredWindowAttributes(hwnd, color_key, 0, win32con.LWA_COLORKEY)
    
    # Mantém a janela visível
    win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
    
    return screen, hwnd

def set_window_interactivity(hwnd, interactive):
    """
    Alterna a janela entre clicar-através (click-through) e interativa.
    interactive=True: O mouse pode interagir com os elementos do Pygame.
    interactive=False: Os cliques atravessam a janela transparente.
    """
    current_ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    
    if interactive:
        # Remove a flag WS_EX_TRANSPARENT para receber eventos do mouse
        new_style = current_ex_style & ~win32con.WS_EX_TRANSPARENT
    else:
        # Adiciona a flag WS_EX_TRANSPARENT para os cliques passarem direto
        new_style = current_ex_style | win32con.WS_EX_TRANSPARENT
        
    if new_style != current_ex_style:
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, new_style)

def get_mouse_pos():
    """
    Retorna a posição do mouse na tela. Como a janela está ancorada em 0,0,
    a posição absoluta do mouse é equivalente à posição no Pygame.
    """
    return win32api.GetCursorPos()
