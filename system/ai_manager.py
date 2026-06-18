import threading
import urllib.request
import json
import queue
import time
import re
import os
import io
from dotenv import load_dotenv

load_dotenv()

try:
    from google import genai
    from google.genai import types as genai_types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Ordem de fallback entre modelos cloud (do preferido ao menos preferido)
CLOUD_FALLBACK_ORDER = [
    "gemma-4-31b-it",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
]

def _is_gemma_model(model_name: str) -> bool:
    """Retorna True se o modelo for da família Gemma (não suporta system_instruction via config)."""
    return "gemma" in model_name.lower()


def _pil_to_genai_part(pil_image):
    """Converte PIL Image para um objeto Part do google-genai (JPEG em memória)."""
    buf = io.BytesIO()
    pil_image.save(buf, format='JPEG', quality=82)
    return genai_types.Part(
        inline_data=genai_types.Blob(
            mime_type='image/jpeg',
            data=buf.getvalue()
        )
    )


class AIManager:
    def __init__(self, save_manager=None):
        self.save_manager = save_manager
        self._is_enabled = False
        self.model = "llama3.2:1b"
        self.api_url = "http://localhost:11434/api/generate"
        
        # Sistema de Fila de Falas
        self.request_queue = queue.Queue()
        self.current_task_id = 0    # Incrementado por diálogos de texto (debounce)
        self.vision_task_id = 0     # Incrementado só por requisições de visão (nunca canceladas)
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        
        self.system_prompt = (
            "Você é o Doctor Penguin, um pinguim mascote virtual de computador. Você mora no PC do usuário e ajuda a cuidar do sistema. "
            "Você é inteligente, engraçado e bastante atrevido. Você ama peixes, frio, gelo e a Antártida. "
            "Suas falas devem ser SEMPRE curtas e diretas [no máximo 12 palavras em portugues brasil (PT-BR)]."
            "NUNCA descreva suas ações (não use asteriscos como *sorri* ou *olha*). Fale diretamente o texto."
            "Reaja ao contexto fornecido. NÃO dê explicações extras, NÃO saia do personagem."
        )

    @property
    def is_enabled(self):
        return self._is_enabled

    def enable(self, state: bool):
        self._is_enabled = state

    def request_dialogue(self, event_context, callback, fallback):
        """Enfileira uma requisição de diálogo apenas com texto (sujeita a debounce)."""
        if not self._is_enabled:
            callback(fallback)
            return

        self.current_task_id += 1
        self.request_queue.put({
            'task_id': self.current_task_id,
            'event_context': event_context,
            'callback': callback,
            'fallback': fallback,
            'vision_context': None,
            'is_vision': False
        })

    def request_dialogue_with_vision(self, vision_context, event_context, callback, fallback):
        """
        Enfileira uma requisição de diálogo com imagens (câmera + screenshot).
        Requisições de visão NÃO são canceladas por novos diálogos de texto.
        vision_context: VisionContext do camera_vision.py
        """
        if not self._is_enabled:
            callback(fallback)
            return

        self.vision_task_id += 1
        vid = self.vision_task_id
        self.request_queue.put({
            'task_id': vid,        # Usa vision_task_id separado
            'event_context': event_context,
            'callback': callback,
            'fallback': fallback,
            'vision_context': vision_context,
            'is_vision': True      # Não será cancelado por diálogos de texto
        })
        print(f"[AIManager] Visão enfileirada (vision_task_id={vid})")

    def cancel_current(self):
        """Cancela falas pendentes."""
        self.current_task_id += 1

    # ── Helpers de Texto ───────────────────────────────────────────────────────

    def _clean_ai_text(self, text: str) -> str:
        """Remove formatação indesejada da resposta da IA."""
        text = text.strip()
        text = re.sub(r'[*_][^*_]*[*_]', '', text).strip()
        # Remove emojis e caracteres especiais que quebram o Pygame/TTS
        text = re.sub(r'[^\w\s.,!?;:\'\"()-]', '', text).strip()
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1].strip()
        return text

    # ── Chamadas à API Cloud ───────────────────────────────────────────────────

    def _build_contents(self, model_name: str, prompt: str, vision_context=None) -> list:
        """
        Monta a lista de `contents` para a chamada da API.
        
        Para modelos Gemma: injeta o system prompt no texto (não suportam system_instruction via config).
        Adiciona imagens da câmera e screenshot se vision_context for fornecido.
        """
        contents = []

        # Adiciona imagens se houver contexto de visão
        if vision_context and GEMINI_AVAILABLE:
            if vision_context.camera_frame is not None:
                try:
                    contents.append(_pil_to_genai_part(vision_context.camera_frame))
                except Exception as e:
                    print(f"[AIManager] Erro ao converter frame de câmera: {e}")
            if vision_context.screen_frame is not None:
                try:
                    contents.append(_pil_to_genai_part(vision_context.screen_frame))
                except Exception as e:
                    print(f"[AIManager] Erro ao converter screenshot: {e}")

        # Monta o texto final
        if _is_gemma_model(model_name):
            # Gemma não suporta system_instruction → injeta no texto
            final_text = f"[Sistema: {self.system_prompt}]\n\n{prompt}"
        else:
            final_text = prompt

        contents.append(final_text)
        return contents

    def _call_cloud_model(self, model_name: str, prompt: str, vision_context=None) -> str:
        """
        Faz uma chamada para um modelo cloud específico.
        Suporta contexto de visão (câmera + screenshot) quando fornecido.
        """
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        contents = self._build_contents(model_name, prompt, vision_context)

        if _is_gemma_model(model_name):
            response = client.models.generate_content(
                model=model_name,
                contents=contents
            )
        else:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config={'system_instruction': self.system_prompt}
            )

        return self._clean_ai_text(response.text)

    def _call_cloud_with_cascade(self, primary_model: str, prompt: str, vision_context=None) -> str:
        """
        Tenta o modelo primário com cascade de fallback automático.
        
        Em erro 429 (quota): tenta o próximo modelo da lista.
        Em erro 500 (instabilidade): faz 1 retry com 2s de espera antes de escalar.
        Suporta vision_context para chamadas multimodais.
        """
        # Monta a ordem: primário primeiro, depois CLOUD_FALLBACK_ORDER
        models_to_try = [primary_model]
        for m in CLOUD_FALLBACK_ORDER:
            if m != primary_model and m not in models_to_try:
                models_to_try.append(m)

        last_exception = None
        for i, model_name in enumerate(models_to_try):
            try:
                if i > 0:
                    print(f"[AIManager] Tentando modelo fallback: {model_name}")

                # Retry com backoff exponencial para erros 500
                for attempt in range(2):
                    try:
                        result = self._call_cloud_model(model_name, prompt, vision_context)
                        if result:
                            if i > 0:
                                print(f"[AIManager] Fallback bem-sucedido com: {model_name}")
                            return result
                        break  # Resposta vazia — não retenta
                    except Exception as e:
                        err_str = str(e)
                        is_server_error = "500" in err_str or "INTERNAL" in err_str
                        if is_server_error and attempt == 0:
                            print(f"[AIManager] Erro 500 com {model_name}, retentando em 2s...")
                            time.sleep(2)
                        else:
                            raise

            except Exception as e:
                err_str = str(e)
                is_quota = "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower()
                is_server = "500" in err_str or "INTERNAL" in err_str
                last_exception = e

                if is_quota:
                    print(f"[AIManager] Quota esgotada em '{model_name}', tentando próximo modelo...")
                elif is_server:
                    print(f"[AIManager] Erro interno em '{model_name}' após retentativas, tentando próximo...")
                else:
                    print(f"[AIManager] Erro inesperado com '{model_name}': {e}")
                    raise  # Erro de rede/desconhecido — não tenta mais modelos

        raise last_exception or Exception("Todos os modelos cloud falharam.")

    # ── Worker Thread ──────────────────────────────────────────────────────────

    def _worker_loop(self):
        while True:
            req = self.request_queue.get()
            is_vision = req.get('is_vision', False)

            # Verifica cancelação: visão NUNCA é cancelada por novos diálogos de texto
            if not is_vision and req['task_id'] != self.current_task_id:
                print(f"[AIManager] Requisição de texto #{req['task_id']} descartada (task atual: {self.current_task_id})")
                continue

            accumulated_contexts = [req['event_context']]
            final_callback = req['callback']
            final_fallback = req['fallback']
            final_vision = req.get('vision_context')

            # DEBOUNCE: só para requisições de texto — consume ações empilhadas na fila
            if not is_vision:
                while not self.request_queue.empty():
                    try:
                        new_req = self.request_queue.get_nowait()
                        if new_req.get('is_vision', False):
                            # Recoloca visão de volta na fila (não pode consumir)
                            self.request_queue.put(new_req)
                            break
                        accumulated_contexts.append(new_req['event_context'])
                        final_callback = new_req['callback']
                        final_fallback = new_req['fallback']
                        req = new_req
                    except queue.Empty:
                        break

                # Verifica cancelação novamente após debounce
                if req['task_id'] != self.current_task_id:
                    print(f"[AIManager] Requisição #{req['task_id']} cancelada após debounce.")
                    continue

            if is_vision:
                print(f"[AIManager] Processando requisição de VISÃO (cam={final_vision and final_vision.camera_frame is not None}, screen={final_vision and final_vision.screen_frame is not None})")

            try:
                if len(accumulated_contexts) > 1:
                    combined = " E LOGO EM SEGUIDA ".join(accumulated_contexts)
                    prompt = f"O usuário fez a seguinte sequência rápida de ações com você: {combined}\nO que você diria para o usuário agora como reação a TUDO isso de uma vez?"
                else:
                    prompt = f"Contexto atual do PC ou da interação: {accumulated_contexts[0]}\nO que você diria para o usuário agora?"

                model_type = self.save_manager.get_ai_model() if self.save_manager else "cloud"

                # Cloud Model com cascade e suporte a visão
                if model_type == "cloud" and GEMINI_AVAILABLE and os.getenv("GEMINI_API_KEY"):
                    primary_model = self.save_manager.get_cloud_model() if self.save_manager else "gemma-4-31b-it"

                    ai_text = self._call_cloud_with_cascade(primary_model, prompt, final_vision)

                    # Para texto, descarta se já há um request mais novo
                    # Para visão, SEMPRE entrega (o processamento foi longo mas válido)
                    if not is_vision and req['task_id'] != self.current_task_id:
                        print(f"[AIManager] Resposta de texto descartada após API (task expirou).")
                        continue

                    if ai_text:
                        if is_vision:
                            print(f"[AIManager] Resposta de visão entregue: '{ai_text[:40]}...'")
                        final_callback(ai_text)
                    else:
                        final_callback(final_fallback)

                # Local Model (Ollama)
                else:
                    payload = {
                        "model": self.model,
                        "prompt": prompt,
                        "system": self.system_prompt,
                        "stream": False,
                        "options": {"temperature": 0.6}
                    }
                    data = json.dumps(payload).encode("utf-8")
                    http_req = urllib.request.Request(
                        self.api_url, data=data,
                        headers={"Content-Type": "application/json"}
                    )
                    with urllib.request.urlopen(http_req, timeout=15) as response:
                        if req['task_id'] != self.current_task_id:
                            continue
                        if response.status == 200:
                            resp_data = json.loads(response.read().decode("utf-8"))
                            ai_text = resp_data.get("response", "").strip()
                            ai_text = re.sub(r'[*_][^*_]*[*_]', '', ai_text).strip()
                            ai_text = re.sub(r'[^\w\s.,!?;:\'\"()-]', '', ai_text).strip()
                            if ai_text.startswith('"') and ai_text.endswith('"'):
                                ai_text = ai_text[1:-1].strip()
                            if ai_text:
                                final_callback(ai_text)
                            else:
                                final_callback(final_fallback)
                        else:
                            print(f"[AIManager] Erro na API do Ollama (Status {response.status})")
                            final_callback(final_fallback)

            except Exception as e:
                if req['task_id'] == self.current_task_id:
                    print(f"[AIManager] Todos os modelos falharam, usando frase estática: {e}")
                    final_callback(final_fallback)