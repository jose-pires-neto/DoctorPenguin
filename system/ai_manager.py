import threading
import urllib.request
import json

class AIManager:
    def __init__(self):
        self._is_enabled = False
        self.model = "llama3.2:1b"
        self.api_url = "http://localhost:11434/api/generate"
        self.system_prompt = (
            "Você é o Doctor Penguin, um pinguim mascote virtual de computador. "
            "Você mora no PC do usuário e ajuda a cuidar do sistema. "
            "Você é fofo, inteligente, prestativo e um pouco atrevido. "
            "Você ama peixes, frio, gelo e a Antártida. "
            "Suas respostas devem ser SEMPRE curtas (no máximo 10 frases), diretas e em português do Brasil (PT-BR). "
            "Aja como o mascote interagindo com seu dono e reaja ao contexto fornecido. Não dê explicações extras, não saia do personagem."
        )

    @property
    def is_enabled(self):
        return self._is_enabled

    def enable(self, state: bool):
        self._is_enabled = state

    def request_dialogue(self, event_context, callback, fallback):
        if not self._is_enabled:
            callback(fallback)
            return

        def task():
            try:
                prompt = f"Contexto atual do PC ou da interação: {event_context}\nO que você diria para o usuário agora?"
                
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "system": self.system_prompt,
                    "stream": False
                }
                
                data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(self.api_url, data=data, headers={"Content-Type": "application/json"})
                
                with urllib.request.urlopen(req, timeout=30) as response:
                    if response.status == 200:
                        resp_data = json.loads(response.read().decode("utf-8"))
                        ai_text = resp_data.get("response", "").strip()
                        # Remove aspas se a IA por algum motivo as incluir no começo e fim
                        if ai_text.startswith('"') and ai_text.endswith('"'):
                            ai_text = ai_text[1:-1]
                            
                        if ai_text:
                            callback(ai_text)
                        else:
                            callback(fallback)
                    else:
                        print(f"[AIManager] Erro na API do Ollama (Status {response.status})")
                        callback(fallback)
            except Exception as e:
                print(f"[AIManager] Erro ao contatar Ollama. Certifique-se de que ele está rodando. Erro: {e}")
                callback(fallback)

        thread = threading.Thread(target=task)
        thread.daemon = True
        thread.start()