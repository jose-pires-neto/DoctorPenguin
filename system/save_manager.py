import os
import json
import time

SAVE_FILE = "save_data.json"

class SaveManager:
    def __init__(self):
        self.data = self._load()

    def _load(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, "r") as f:
                    data = json.load(f)
                    
                # Fix color tuples which might be saved as lists
                if 'penguin_color' in data and data['penguin_color']:
                    data['penguin_color'] = tuple(data['penguin_color'])
                    
                return data
            except:
                pass
        return {
            "fish_count": 0,
            "ignored_processes": {},
            "penguin_color": None,
            "ai_enabled": False,
            "ai_model_type": "cloud",
            "cloud_model": "gemma-4-31b-it",
            "voice_enabled": False,
            "voice_id": None,
            "camera_enabled": False,
            "camera_permission_granted": False
        }

    def _save(self):
        try:
            with open(SAVE_FILE, "w") as f:
                json.dump(self.data, f)
        except:
            pass

    def ignore_process(self, process_name, hours=2):
        """Ignora um processo por X horas"""
        if "ignored_processes" not in self.data:
            self.data["ignored_processes"] = {}
        
        expire_time = time.time() + (hours * 3600)
        self.data["ignored_processes"][process_name] = expire_time
        self._save()

    def is_ignored(self, process_name):
        """Verifica se o processo ainda está ignorado"""
        if "ignored_processes" not in self.data:
            return False
            
        expire_time = self.data["ignored_processes"].get(process_name, 0)
        if time.time() < expire_time:
            return True
            
        # Se expirou, pode remover para limpar
        if process_name in self.data["ignored_processes"]:
            del self.data["ignored_processes"][process_name]
            self._save()
            
        return False
        
    # --- Fish Inventory ---
    def get_fishes(self):
        return self.data.get("fish_count", 0)
        
    def set_penguin_color(self, color):
        """Salva a cor do pinguim"""
        self.data["penguin_color"] = color
        self._save()
        
    def get_penguin_color(self):
        """Retorna a cor do pinguim ou None"""
        return self.data.get("penguin_color", None)
        
    def add_fish(self, amount=1):
        self.data["fish_count"] = self.get_fishes() + amount
        self._save()
        
    def consume_fish(self):
        if self.get_fishes() > 0:
            self.data["fish_count"] -= 1
            self._save()
            return True
        return False
        
    def set_ai_enabled(self, status):
        self.data["ai_enabled"] = status
        self._save()
        
    def is_ai_enabled(self):
        return self.data.get("ai_enabled", False)

    def set_ai_model(self, model_type):
        """Salva o modelo de IA selecionado ('local' ou 'cloud')"""
        self.data["ai_model_type"] = model_type
        self._save()
        
    def get_ai_model(self):
        """Retorna o modelo de IA selecionado ('local' ou 'cloud')"""
        return self.data.get("ai_model_type", "cloud")
        
    def set_cloud_model(self, model_name):
        self.data["cloud_model"] = model_name
        self._save()
        
    def get_cloud_model(self):
        return self.data.get("cloud_model", "gemma-4-31b-it")

    def is_voice_enabled(self):
        return self.data.get("voice_enabled", False)

    def set_voice_enabled(self, status):
        self.data["voice_enabled"] = status
        self._save()

    def get_voice_id(self):
        return self.data.get("voice_id", None)

    def set_voice_id(self, voice_id):
        self.data["voice_id"] = voice_id
        self._save()

    # --- Camera Vision ---

    def is_camera_enabled(self) -> bool:
        return self.data.get("camera_enabled", False)

    def set_camera_enabled(self, status: bool):
        self.data["camera_enabled"] = status
        self._save()

    def is_camera_permission_granted(self) -> bool:
        """Retorna True se o usuário já concedeu permissão de câmera alguma vez."""
        return self.data.get("camera_permission_granted", False)

    def grant_camera_permission(self):
        """Marca que o usuário concedeu permissão de câmera."""
        self.data["camera_permission_granted"] = True
        self._save()
