import pygame
import sys
import os
import numpy as np
import scipy.ndimage as ndi
from PIL import Image

# Configurações do Grid
CELL_W = 64
CELL_H = 64
COLS = 8
ROWS = 4

DIRECTIONS = ["South", "SouthWest", "West", "NorthWest", "North", "NorthEast", "East", "SouthEast"]
STATES = ["Idle", "Walk 1", "Walk 2", "Sitting"]

def extract_sprites(image_path):
    img = Image.open(image_path)
    alpha = np.array(img.split()[-1]) > 0

    labels, num_features = ndi.label(alpha)
    slices = ndi.find_objects(labels)

    sprites = []
    bboxes = []
    
    for slc in slices:
        y_slice, x_slice = slc
        cy = (y_slice.start + y_slice.stop) / 2
        cx = (x_slice.start + x_slice.stop) / 2
        b = {
            'y_min': y_slice.start, 'y_max': y_slice.stop,
            'x_min': x_slice.start, 'x_max': x_slice.stop,
            'cy': cy, 'cx': cx
        }
        bboxes.append(b)

    # Sort by Y then X to keep them organized in the palette
    bboxes.sort(key=lambda b: (b['cy'] // 20, b['cx']))
    
    for b in bboxes:
        sprite_img = img.crop((b['x_min'], b['y_min'], b['x_max'], b['y_max']))
        # Convert PIL to Pygame Surface
        mode = sprite_img.mode
        size = sprite_img.size
        data = sprite_img.tobytes()
        pg_img = pygame.image.fromstring(data, size, mode).convert_alpha()
        sprites.append({'surface': pg_img, 'pil': sprite_img, 'bbox': b})
        
    return sprites

def auto_map_grid(sprites):
    grid = [[None for _ in range(COLS)] for _ in range(ROWS)]
    
    # Sort sprites by Y to guess rows
    sorted_by_y = sorted(sprites, key=lambda s: s['bbox']['cy'])
    
    rows_list = []
    current_row = []
    for s in sorted_by_y:
        if not current_row:
            current_row.append(s)
        else:
            avg_cy = sum(cs['bbox']['cy'] for cs in current_row) / len(current_row)
            if abs(s['bbox']['cy'] - avg_cy) < 20:
                current_row.append(s)
            else:
                rows_list.append(current_row)
                current_row = [s]
    if current_row:
        rows_list.append(current_row)

    if len(rows_list) > 0:
        # Reference X from first row
        rows_list[0].sort(key=lambda s: s['bbox']['cx'])
        ref_cx = [s['bbox']['cx'] for s in rows_list[0]]
        
        for r_idx, row in enumerate(rows_list[:ROWS]):
            for s in row:
                c_idx = min(range(min(COLS, len(ref_cx))), key=lambda i: abs(s['bbox']['cx'] - ref_cx[i]))
                # Find index in main sprites list
                idx = sprites.index(s)
                grid[r_idx][c_idx] = idx
                
    return grid

def main():
    pygame.init()
    screen = pygame.display.set_mode((1024, 768))
    pygame.display.set_caption("Configurador Manual de Sprites - Doctor Penguin")
    font = pygame.font.SysFont("Arial", 14)
    font_bold = pygame.font.SysFont("Arial", 16, bold=True)
    
    print("Extraindo sprites...")
    sprites = extract_sprites("penguin_sprites.png")
    grid = auto_map_grid(sprites)
    
    selected_sprite = None
    
    # Layout dimensions
    grid_x = 50
    grid_y = 50
    
    palette_x = 50
    palette_y = 400
    palette_cols = 10
    
    btn_rect = pygame.Rect(800, 50, 150, 50)
    
    running = True
    while running:
        screen.fill((40, 40, 40))
        
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    # Check palette click
                    for i, s in enumerate(sprites):
                        px = palette_x + (i % palette_cols) * (CELL_W + 10)
                        py = palette_y + (i // palette_cols) * (CELL_H + 30)
                        if pygame.Rect(px, py, CELL_W, CELL_H).collidepoint(mouse_pos):
                            selected_sprite = i
                            
                    # Check grid click
                    for r in range(ROWS):
                        for c in range(COLS):
                            gx = grid_x + c * (CELL_W + 5)
                            gy = grid_y + r * (CELL_H + 20)
                            if pygame.Rect(gx, gy, CELL_W, CELL_H).collidepoint(mouse_pos):
                                if selected_sprite is not None:
                                    grid[r][c] = selected_sprite
                                    
                    # Check save button
                    if btn_rect.collidepoint(mouse_pos):
                        save_spritesheet(grid, sprites)
                        print("Salvo com sucesso!")
                        
                elif event.button == 3: # Right click
                    # Check grid click to clear
                    for r in range(ROWS):
                        for c in range(COLS):
                            gx = grid_x + c * (CELL_W + 5)
                            gy = grid_y + r * (CELL_H + 20)
                            if pygame.Rect(gx, gy, CELL_W, CELL_H).collidepoint(mouse_pos):
                                grid[r][c] = None

        # Draw Grid
        screen.blit(font_bold.render("GRADE DE ANIMAÇÃO (Clique para posicionar sprite selecionado, Clique Direito para limpar)", True, (200, 255, 200)), (grid_x, 20))
        for c in range(COLS):
            label = font.render(DIRECTIONS[c], True, (150, 150, 150))
            screen.blit(label, (grid_x + c * (CELL_W + 5), grid_y - 20))
            
        for r in range(ROWS):
            label = font.render(STATES[r], True, (150, 150, 150))
            screen.blit(label, (grid_x - 60, grid_y + r * (CELL_H + 20) + 20))
            for c in range(COLS):
                gx = grid_x + c * (CELL_W + 5)
                gy = grid_y + r * (CELL_H + 20)
                
                pygame.draw.rect(screen, (80, 80, 80), (gx, gy, CELL_W, CELL_H), 1)
                
                idx = grid[r][c]
                if idx is not None:
                    surf = sprites[idx]['surface']
                    # Center bottom align
                    dx = gx + (CELL_W - surf.get_width()) // 2
                    dy = gy + (CELL_H - surf.get_height()) - 2
                    screen.blit(surf, (dx, dy))
                    
                    # Draw index
                    idx_text = font.render(str(idx), True, (255, 255, 0))
                    screen.blit(idx_text, (gx + 2, gy + 2))

        # Draw Palette
        screen.blit(font_bold.render("PALETA DE SPRITES (Clique para selecionar)", True, (200, 255, 200)), (palette_x, palette_y - 30))
        for i, s in enumerate(sprites):
            px = palette_x + (i % palette_cols) * (CELL_W + 10)
            py = palette_y + (i // palette_cols) * (CELL_H + 30)
            
            color = (150, 150, 150)
            if selected_sprite == i:
                color = (0, 255, 0)
                pygame.draw.rect(screen, (50, 100, 50), (px, py, CELL_W, CELL_H))
                
            pygame.draw.rect(screen, color, (px, py, CELL_W, CELL_H), 2 if selected_sprite == i else 1)
            
            surf = s['surface']
            dx = px + (CELL_W - surf.get_width()) // 2
            dy = py + (CELL_H - surf.get_height()) - 2
            screen.blit(surf, (dx, dy))
            
            idx_text = font.render(str(i), True, (255, 255, 255))
            screen.blit(idx_text, (px + CELL_W//2 - 5, py + CELL_H + 2))

        # Draw Save Button
        color = (100, 200, 100) if btn_rect.collidepoint(mouse_pos) else (50, 150, 50)
        pygame.draw.rect(screen, color, btn_rect)
        pygame.draw.rect(screen, (255,255,255), btn_rect, 2)
        save_text = font_bold.render("SALVAR", True, (255, 255, 255))
        screen.blit(save_text, (btn_rect.x + 45, btn_rect.y + 15))

        pygame.display.flip()

    pygame.quit()

def save_spritesheet(grid, sprites):
    sheet = Image.new('RGBA', (CELL_W * COLS, CELL_H * ROWS), (0, 0, 0, 0))
    
    for r in range(ROWS):
        for c in range(COLS):
            idx = grid[r][c]
            if idx is not None:
                pil_img = sprites[idx]['pil']
                dx = (c * CELL_W) + (CELL_W - pil_img.width) // 2
                dy = (r * CELL_H) + (CELL_H - pil_img.height) - 2
                sheet.paste(pil_img, (dx, dy), pil_img)
                
    sheet.save("penguin_sprites_aligned.png")

if __name__ == "__main__":
    main()
