"""
CameraVisionSystem — Sistema de Visão do Doctor Penguin
-------------------------------------------------------
Captura frames da câmera + screenshots periodicamente de forma randômica.
Detecta presença de rostos via Haar cascade (sem modelo externo).
Envia imagens para o Gemma 4 via AIManager para reações contextuais.
"""

import threading
import time
import random
import io
import os

# OpenCV para câmera e detecção de rostos
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("[CameraVision] OpenCV não instalado. Câmera desativada.")

# PIL para screenshot
try:
    from PIL import ImageGrab, Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("[CameraVision] PIL não disponível. Screenshot desativado.")


class VisionContext:
    """Resultado de uma captura de câmera + tela."""
    __slots__ = ['camera_frame', 'screen_frame', 'face_count', 'user_present', 'has_content']

    def __init__(self, camera_frame=None, screen_frame=None, face_count=0):
        self.camera_frame = camera_frame   # PIL Image | None
        self.screen_frame = screen_frame   # PIL Image | None
        self.face_count = face_count       # Quantidade de rostos detectados
        self.user_present = face_count > 0 # True se há pelo menos 1 rosto
        self.has_content = camera_frame is not None or screen_frame is not None

    def build_context_description(self) -> str:
        """Gera uma string de contexto para adicionar ao prompt da IA."""
        parts = []
        if self.camera_frame is not None:
            parts.append("A imagem da câmera do usuário está anexada (analise a pessoa e o ambiente).")
        if self.screen_frame is not None:
            parts.append("A imagem da tela atual do usuário também está anexada (veja o que ele está fazendo).")
        return " ".join(parts) if parts else ""


class CameraVisionSystem:
    """
    Sistema de visão computacional do Doctor Penguin.

    Comportamento periódico:
    - Verifica a cada CHECK_INTERVAL segundos (8 min por padrão)
    - Tem TRIGGER_CHANCE (35%) de disparar uma captura quando a janela vence
    - Captura câmera + screenshot e chama o callback registrado
    - Detecta presença de rostos via Haar cascade (offline, sem internet)
    """

    CHECK_INTERVAL_SECS = 480   # Janela de 8 minutos
    TRIGGER_CHANCE = 0.35       # 35% de chance de disparar quando a janela vence

    def __init__(self, save_manager):
        self.save_manager = save_manager
        self._enabled = save_manager.is_camera_enabled()
        self._camera_available = None   # None = não testado ainda
        self._last_trigger_time = time.time()  # Inicializa com now, evita disparar logo no boot
        self._on_vision_ready = None    # callback(VisionContext) periódico
        self._face_cascade = None
        self._lock = threading.Lock()
        self.last_capture_time = 0      # Timestamp da última captura bem-sucedida

        # Carrega o detector de rostos Haar cascade (offline)
        if CV2_AVAILABLE:
            try:
                cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                if os.path.exists(cascade_path):
                    self._face_cascade = cv2.CascadeClassifier(cascade_path)
                    print("[CameraVision] Detector de rostos Haar carregado.")
            except Exception as e:
                print(f"[CameraVision] Erro ao carregar Haar cascade: {e}")

        # Thread daemon de verificação periódica
        self._thread = threading.Thread(target=self._periodic_loop, daemon=True)
        self._thread.start()

        # Testa câmera em background (não bloqueia o startup)
        threading.Thread(target=self._probe_camera, daemon=True).start()

    # ── Detecção de Câmera ─────────────────────────────────────────────────────

    def _probe_camera(self):
        """Testa silenciosamente se há câmera conectada."""
        if not CV2_AVAILABLE:
            self._camera_available = False
            return
        try:
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            self._camera_available = cap.isOpened()
            cap.release()
        except Exception:
            self._camera_available = False

        status = "detectada" if self._camera_available else "não encontrada"
        print(f"[CameraVision] Câmera {status}.")

    # ── Controle de Estado ─────────────────────────────────────────────────────

    def enable(self, state: bool):
        """Ativa ou desativa o sistema de câmera."""
        self._enabled = state
        self.save_manager.set_camera_enabled(state)
        print(f"[CameraVision] {'Ativado' if state else 'Desativado'}.")

    def is_enabled(self) -> bool:
        return self._enabled

    def is_camera_available(self) -> bool:
        """Retorna True se OpenCV está disponível e câmera foi detectada."""
        return CV2_AVAILABLE and bool(self._camera_available)

    def is_probing(self) -> bool:
        """Retorna True se ainda está testando a câmera."""
        return self._camera_available is None

    def set_on_vision_ready(self, callback):
        """
        Registra o callback para capturas periódicas: callback(VisionContext).
        Chamado quando a janela de 8 min vence e o random dispara.
        """
        with self._lock:
            self._on_vision_ready = callback

    # ── Captura Manual (On-Demand) ─────────────────────────────────────────────

    def capture_now_async(self, callback):
        """
        Dispara uma captura imediata e não-bloqueante.
        Chama callback(VisionContext) quando concluída.
        """
        threading.Thread(target=self._do_capture, args=(callback,), daemon=True).start()

    # ── Loop Periódico ─────────────────────────────────────────────────────────

    def _periodic_loop(self):
        """Loop daemon que verifica a cada minuto se deve disparar uma captura."""
        while True:
            time.sleep(60)

            if not self._enabled:
                continue

            with self._lock:
                callback = self._on_vision_ready

            if not callback:
                continue

            elapsed = time.time() - self._last_trigger_time
            if elapsed >= self.CHECK_INTERVAL_SECS:
                if random.random() < self.TRIGGER_CHANCE:
                    self._last_trigger_time = time.time()
                    print("[CameraVision] Disparo periódico aleatório!")
                    self._do_capture(callback)

    # ── Captura de Câmera ──────────────────────────────────────────────────────

    def _capture_camera(self):
        """
        Captura um frame da webcam.
        Retorna (PIL Image, BGR ndarray) ou (None, None) em caso de falha.
        Usa resolução reduzida para minimizar tamanho do payload e tempo de API.
        """
        if not self.is_camera_available():
            return None, None
        try:
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not cap.isOpened():
                self._camera_available = False
                return None, None

            # Define resolução reduzida diretamente na câmera (mais rápido)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

            # Lê alguns frames para a câmera calibrar exposição automática
            for _ in range(3):
                cap.read()

            ret, frame = cap.read()
            cap.release()

            if not ret or frame is None:
                return None, None

            # Garante resolução máxima de 320x240 (econom. tokens)
            h, w = frame.shape[:2]
            if w > 640:
                frame = cv2.resize(frame, (640, 480))

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return Image.fromarray(frame_rgb), frame

        except Exception as e:
            print(f"[CameraVision] Erro ao capturar câmera: {e}")
            return None, None

    def _detect_faces(self, bgr_frame) -> int:
        """Detecta rostos no frame BGR usando Haar cascade. Retorna contagem."""
        if self._face_cascade is None or bgr_frame is None:
            return 0
        try:
            gray = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)
            faces = self._face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40)
            )
            return len(faces)
        except Exception:
            return 0

    # ── Screenshot ─────────────────────────────────────────────────────────────

    def _capture_screenshot(self):
        """Captura screenshot da tela. Retorna PIL Image ou None."""
        if not PIL_AVAILABLE:
            return None
        try:
            shot = ImageGrab.grab()
            # Reduz para 640x360 para minimizar tokens e acelerar a API
            shot = shot.resize((640, 360), Image.LANCZOS)
            return shot
        except Exception as e:
            print(f"[CameraVision] Erro ao capturar screenshot: {e}")
            return None

    # ── Captura Completa ───────────────────────────────────────────────────────

    def _do_capture(self, callback):
        """Realiza captura completa (câmera + screenshot) e chama callback."""
        cam_pil, cam_bgr = self._capture_camera()
        face_count = self._detect_faces(cam_bgr) if cam_bgr is not None else 0
        screen_pil = self._capture_screenshot()

        ctx = VisionContext(
            camera_frame=cam_pil,
            screen_frame=screen_pil,
            face_count=face_count
        )

        if ctx.has_content:
            self.last_capture_time = time.time()  # Marca o momento da captura
            try:
                callback(ctx)
            except Exception as e:
                print(f"[CameraVision] Erro no callback de visão: {e}")
        else:
            print("[CameraVision] Captura sem conteúdo, ignorando.")
