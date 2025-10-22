# Опис проєкту backend-tech-task

## Запуск проєкту
```bash 
cd backend/
```
```bash 
cp env.sample .env
```
```bash 
docker-compose up --build -d
```


## Запуск тестів
```bash 
docker exec -it <container_name> python manage.py test events_service
```

## Імпорт історії
```bash 
docker cp data/events_sample.csv <container_name>:/app/events_sample.csv
```
```bash
docker exec -it <container_name> python manage.py import_events data/events_sample.csv
```


## Вимірювання продуктивності
### Запуск бенчмарку
```bash 
docker exec -it <container_name> python manage.py benchmark
```

### Методологія
100,000 подій було згенеровано і вставлено пакетно у базу з оптимальним batch_size=5000. 
Події мали розподіл по 30 000 унікальних користувачів із різними часовими відмітками.

### Результати
- Batch insert: 2.34 сек.
- DAU query: 0.02 сек.

### Висновки
Загалом вийшла досить продуктивна система. Створене навантаження вузьких місць не виявило.
