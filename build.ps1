# Script de Build do Doctor Penguin
Write-Host "Iniciando processo de compilação..." -ForegroundColor Cyan

# 1. Instala o PyInstaller se não tiver
Write-Host "Verificando dependências (PyInstaller)..."
pip install pyinstaller

# 2. Compila o projeto
Write-Host "Compilando o arquivo executável..." -ForegroundColor Green
pyinstaller --noconsole --onefile --name "DoctorPenguin" --add-data "penguin_sprites_aligned.png;." main.py

Write-Host "Concluído! O seu executável está na pasta 'dist'." -ForegroundColor Green
pause
