import os
import json
from typing import List, Dict

# Папка для хранения контекста
CONTEXT_DIR = "./contexts"

# Убедимся, что папка для хранения контекстов существует
os.makedirs(CONTEXT_DIR, exist_ok=True)

def _get_context_file_path(thread_id: str) -> str:
    """Возвращает путь к файлу для указанного thread_id."""
    return os.path.join(CONTEXT_DIR, f"{thread_id}.json")

def add_message_to_thread(thread_id: str, role: str, content: str):
    """Добавляет сообщение в контекст указанного thread_id."""
    context = get_thread_context(thread_id)
    context.append({"role": role, "content": content})
    _save_thread_context(thread_id, context)

def get_thread_context(thread_id: str) -> List[Dict[str, str]]:
    """Возвращает контекст для thread_id. Если контекст отсутствует, возвращает пустой список."""
    context_file = _get_context_file_path(thread_id)
    if os.path.exists(context_file):
        with open(context_file, "r", encoding="utf-8") as file:
            return json.load(file)
    return []

def clear_thread_context(thread_id: str):
    """Удаляет файл контекста для указанного thread_id."""
    context_file = _get_context_file_path(thread_id)
    if os.path.exists(context_file):
        os.remove(context_file)

def clear_all_contexts():
    """Очищает все файлы контекста."""
    for file in os.listdir(CONTEXT_DIR):
        os.remove(os.path.join(CONTEXT_DIR, file))

def _save_thread_context(thread_id: str, context: List[Dict[str, str]]):
    """Сохраняет контекст в файл."""
    context_file = _get_context_file_path(thread_id)
    with open(context_file, "w", encoding="utf-8") as file:
        json.dump(context, file, ensure_ascii=False, indent=4)
