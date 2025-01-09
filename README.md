# technical-task
- start envernoment on Win   ```.venv\Scripts\activate```
- by Linux ```source .venv/bin/activate```

### run docker
```
docker-compose build 
docker-compose up -d redis
docker-compose down
```

### start app 
```python app.py```

# Functionality:
### POST /weather 
- [x] Приймає список міст у JSON-запиті.
- [x] Нормалізує імена міст.
- [x] Ініціалізує асинхронне завдання через Celery.
- [x] Повертає task_id і результати одразу (хоча це виконується двічі: один раз асинхронно і один раз синхронно).

### GET /tasks/<task_id>
- [x] Перевіряє статус завдання (running, completed, failed).
- [x] Повертає результат з Redis, якщо завдання завершено.

### GET /results/<region>
- [x] Повертає список міст і їхні дані для заданого регіону.
- [x] Зчитує результати з файлів weather_data/<region>/.

### Обробка API-відповідей
- [x] Логіка обробки враховує помилки API.
- [x] Фільтруються некоректні дані (температура, відсутні ключі).
- [x] Результати групуються за регіонами.

### Вимоги
- [x] Ліміти API і помилки враховані через Celery з параметром max_retries.
- [x] Підтримка міст у кількох мовах із виправленням помилок у назвах.
- [x] Збереження результатів у Redis і у файловій системі.