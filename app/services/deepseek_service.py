import os
import re
import requests
import time
from bs4 import BeautifulSoup
from openai import OpenAI
from app.config import get_api_key
from app.services.context_manager import add_message_to_thread, get_thread_context

def extract_urls(text: str) -> list:
    """
    Извлекает все URL из текста.
    """
    return re.findall(r'https?://\S+', text)

def fetch_page_content(url: str, max_lines: int = 20) -> str:
    """
    Получает HTML-страницу по URL, пытается найти основной блок содержимого (если есть),
    иначе возвращает первые max_lines строк чистого текста.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        
        # Попытка найти блок с основным содержимым (например, с id="content")
        main_content = soup.find(id="content")
        if main_content:
            text = main_content.get_text(separator='\n')
        else:
            text = soup.get_text(separator='\n')
        
        # Удаляем лишние пробелы и пустые строки
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines[:max_lines])
    except Exception as e:
        return f"Ошибка получения контента: {str(e)}"

def fetch_file_content(file_path: str, max_lines: int = 20) -> str:
    """
    Получает содержимое файла.
    Для текстовых файлов (форматы .txt, .md, .csv, .json, .log) – возвращает первые max_lines строк.
    Для PDF файлов извлекает текст с помощью PyPDF2.
    Поддерживаются только текстовые файлы и PDF файлы.
    """
    if not os.path.exists(file_path):
        return f"Ошибка: файл {file_path} не найден."
    
    ext = os.path.splitext(file_path)[1].lower()
    if ext in [".txt", ".md", ".csv", ".json", ".log"]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            cleaned_lines = [line.strip() for line in lines if line.strip()]
            return "\n".join(cleaned_lines[:max_lines])
        except Exception as e:
            return f"Ошибка при чтении текстового файла: {str(e)}"
    elif ext == ".pdf":
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n"
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            return "\n".join(lines[:max_lines])
        except Exception as e:
            return f"Ошибка при чтении PDF файла: {str(e)}"
    else:
        return f"Формат файла {ext} не поддерживается. Поддерживаются только текстовые файлы и PDF файлы."

def perform_web_search(query: str) -> str:
    """
    Выполняет веб-поиск через Google Custom Search API, извлекает содержимое найденных страниц 
    и возвращает отформатированные результаты.
    """
    google_api_key = os.getenv("GOOGLE_API_KEY")
    google_cse_id = os.getenv("GOOGLE_CSE_ID")
    
    if not google_api_key or not google_cse_id:
        raise ValueError("Не заданы GOOGLE_API_KEY или GOOGLE_CSE_ID в переменных окружения.")
    
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": google_api_key,
        "cx": google_cse_id,
        "q": query,
        "num": 3  # возвращаем до 3 результатов
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    
    items = data.get("items", [])
    if not items:
        return "Нет результатов веб-поиска."
    
    result_text = ""
    for item in items:
        title = item.get("title", "Без заголовка")
        snippet = item.get("snippet", "")
        link = item.get("link", "")
        page_content = fetch_page_content(link, max_lines=20)
        result_text += (
            f"Заголовок: {title}\n"
            f"Сниппет: {snippet}\n"
            f"Ссылка: {link}\n"
            f"Частичное содержимое страницы:\n{page_content}\n\n"
        )
    
    return result_text

def get_deepseek_response(provider_id, assistant_name, user_message, thread_id=None, prompt=None, enable_web_search=False, file_paths=None):
    """
    Формирует контекст для Deepseek. Если в запросе содержится URL или переданы файлы,
    извлекает данные с указанных ресурсов, иначе, если включён веб-поиск, выполняет поиск и 
    добавляет результаты в виде системного сообщения. Затем отправляет запрос в Deepseek и 
    возвращает ответ.
    """
    try:
        api_key = get_api_key(provider_id)
        print(f"API Key: {api_key}")
        
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        
        # Если thread_id не задан, создаём новый контекст
        if thread_id:
            context = get_thread_context(thread_id)
        else:
            thread_id = f"new_thread_{int(time.time())}"
            context = []
        
        system_message_parts = []
        
        # Обработка файлов, если переданы пути к файлам
        if file_paths:
            file_messages = ""
            for file_path in file_paths:
                content = fetch_file_content(file_path, max_lines=20)
                file_messages += f"Содержимое файла {file_path}:\n{content}\n\n"
            system_message_parts.append(
                "Пожалуйста, используйте данные, полученные из указанных ниже файлов, для формирования ответа.\n\n" +
                (prompt or "") +
                "\n\nИнформация из файлов:\n" + file_messages
            )
        
        # Если в запросе содержится URL, обрабатываем их
        urls = extract_urls(user_message)
        if urls:
            url_messages = ""
            for url in urls:
                content = fetch_page_content(url, max_lines=20)
                url_messages += f"Содержимое сайта {url}:\n{content}\n\n"
            system_message_parts.append(
                "Пожалуйста, используйте данные, полученные с указанных ниже сайтов, для формирования ответа.\n\n" +
                (prompt or "") +
                "\n\nИнформация с сайтов:\n" + url_messages
            )
            # Опционально удаляем URL из сообщения пользователя
            user_message = re.sub(r'https?://\S+', '', user_message).strip()
        # Если файлов и URL нет, но включён веб-поиск, выполняем поиск
        elif enable_web_search:
            search_results = perform_web_search(user_message)
            system_message_parts.append(
                "Пожалуйста, используйте приведённые ниже данные веб-поиска для формирования ответа.\n\n" +
                (prompt or "") +
                "\n\nРезультаты веб-поиска по запросу '" + user_message + "':\n" + search_results
            )
        elif prompt:
            system_message_parts.append(prompt)
        
        if system_message_parts:
            system_message = "\n\n".join(system_message_parts)
            context.insert(0, {"role": "system", "content": system_message})
        
        # Добавляем сообщение пользователя
        context.append({"role": "user", "content": user_message})
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=context,
            max_tokens=1024,
            temperature=0.7,
            stream=False
        )
        
        message_content = response.choices[0].message.content
        context.append({"role": "assistant", "content": message_content})
        add_message_to_thread(thread_id, "assistant", message_content)
        
        return {
            "id": response.id,
            "created_at": response.created,
            "thread_id": thread_id,
            "message": message_content
        }
    except Exception as e:
        try:
            print(f"Raw Response: {response.text}")
        except Exception:
            print("Нет raw-ответа.")
        return {"error": f"Error processing request: {str(e)}"}