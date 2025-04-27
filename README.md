# YouTube Assistant 🎬

## Описание
Простое веб-приложение на FastAPI для работы с видео YouTube:
- 📥 Скачивание видео и субтитров  
- ❓ Задание вопросов по содержимому видео  
- 🚀 Минималистичный интерфейс

## Установка и запуск

1. **Клонируйте репозиторий**  
   ```bash
   git clone https://github.com/anrbk-n/youtube-assistant.git
   ```



2. **Установите зависимости**  
   ```bash
   pip install -r requirements.txt
   ```

3. **Запустите сервер**  
   ```bash
   python main.py
   ```

4. **Откройте в браузере**  
   http://127.0.0.1:8000

---

## Структура проекта

```
/
├── main.py             # Запуск FastAPI-сервера
├── requirements.txt    # Список зависимостей
├── templates/          # HTML-шаблоны
│   ├── form.html
│   ├── choose.html
│   ├── ask.html
│   └── watch.html
└── static/             # CSS и прочие статические файлы
    └── style.css
```

---

## Зависимости

- Python 3.9+  
- fastapi  
- uvicorn  
- jinja2  
- python-multipart  

(Все устанавливаются одной командой `pip install -r requirements.txt`.)

