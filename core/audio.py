import pygame
import wave
import struct
import math
import io
import random

def generate_square_wave(frequency, duration, volume=0.5, sample_rate=44100):
    """Gera uma onda quadrada básica (estilo 8-bits retro)"""
    num_samples = int(sample_rate * duration)
    buf = bytearray()
    
    for i in range(num_samples):
        t = float(i) / sample_rate
        # Fator de onda quadrada
        val = 1.0 if math.sin(2.0 * math.pi * frequency * t) > 0 else -1.0
        
        # Envelope de decaimento rápido (som de hit/quack)
        envelope = max(0, 1.0 - (i / num_samples))
        
        sample = int(val * volume * envelope * 32767.0)
        buf.extend(struct.pack('<h', sample))
        
    return buf

def create_sound_from_buffer(buffer, num_channels=1, sample_rate=44100):
    """Cria um pygame.mixer.Sound a partir de um buffer PCM 16-bit"""
    # Precisamos empacotar como um arquivo WAV em memória para o pygame ler
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wav_file:
        wav_file.setnchannels(num_channels)
        wav_file.setsampwidth(2) # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(buffer)
        
    wav_io.seek(0)
    return pygame.mixer.Sound(wav_io)

class AudioSystem:
    def __init__(self):
        # Inicializa o mixer se não estiver inicializado
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
            
        self.sounds = {}
        self._generate_sounds()
        
    def _generate_sounds(self):
        # 1. Quack (Frequência média que cai rapidamente)
        quack_buf = bytearray()
        sample_rate = 44100
        duration = 0.15
        num_samples = int(sample_rate * duration)
        
        for i in range(num_samples):
            t = float(i) / sample_rate
            freq = 600 - (300 * (i / num_samples)) # Frequência cai de 600 pra 300
            val = 1.0 if math.sin(2.0 * math.pi * freq * t) > 0 else -1.0
            envelope = max(0, 1.0 - (i / num_samples) ** 2)
            sample = int(val * 0.3 * envelope * 32767.0)
            quack_buf.extend(struct.pack('<h', sample))
            
        self.sounds['quack'] = create_sound_from_buffer(quack_buf)
        
        # 2. Splat/Boing (Bater na parede)
        boing_buf = bytearray()
        duration = 0.2
        num_samples = int(sample_rate * duration)
        
        for i in range(num_samples):
            t = float(i) / sample_rate
            freq = 150 + (400 * (i / num_samples)) # Frequência sobe rápido
            val = math.sin(2.0 * math.pi * freq * t) # Onda senoidal (mais suave)
            envelope = max(0, 1.0 - (i / num_samples))
            sample = int(val * 0.4 * envelope * 32767.0)
            boing_buf.extend(struct.pack('<h', sample))
            
        self.sounds['boing'] = create_sound_from_buffer(boing_buf)
        
        # 3. Punch/Thud (Batida surda para os cliques)
        punch_buf = bytearray()
        duration = 0.06 # Bem curto
        num_samples = int(sample_rate * duration)
        
        for i in range(num_samples):
            # Ruído branco básico (White Noise)
            val = random.uniform(-1.0, 1.0)
            
            # Envelope de decaimento exponencial rápido para simular o baque seco
            envelope = math.exp(-i / (num_samples * 0.2))
            
            # Um pouco de frequência baixa misturada para dar o 'peso' do soco
            t = float(i) / sample_rate
            bass = math.sin(2.0 * math.pi * 80 * t) * envelope
            
            # Mistura ruído com grave
            mixed_val = (val * 0.4) + (bass * 0.6)
            
            sample = int(mixed_val * 0.5 * 32767.0)
            punch_buf.extend(struct.pack('<h', sample))
            
        self.sounds['beep'] = create_sound_from_buffer(punch_buf)
        
    def play(self, name):
        if name in self.sounds:
            self.sounds[name].play()
