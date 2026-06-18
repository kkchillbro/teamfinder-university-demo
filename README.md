# TeamFinder

TeamFinder — Django-приложение для поиска участников в pet-проекты. Пользователи могут регистрироваться, входить по email, создавать проекты, присоединяться к чужим проектам, редактировать профиль и управлять необходимыми навыками проекта.

Реализован вариант 3: необходимые навыки проектов и фильтрация проектов по навыкам.

## Стек

- Python 3.13
- Django 5.2.4
- PostgreSQL 16
- Docker Compose
- Pillow
- python-decouple
- Gunicorn
- WhiteNoise

## Быстрый запуск

1. Создайте виртуальное окружение и установите зависимости:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Создайте `.env`:

   ```bash
   cp .env_example .env
   ```

3. Проверьте переменные в `.env`:

   ```env
   DJANGO_SECRET_KEY=change_for_safety
   DJANGO_DEBUG=True
   DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
   CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000

   POSTGRES_DB=team_finder
   POSTGRES_USER=team_finder
   POSTGRES_PASSWORD=team_finder
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5436
   DATABASE_URL=
   DB_SSL_REQUIRE=False

   TASK_VERSION=3
   SERVE_MEDIA_FILES=True
   ```

4. Запустите PostgreSQL:

   ```bash
   docker compose up -d
   ```

5. Примените миграции:

   ```bash
   python manage.py migrate
   ```

6. Загрузите тестовые данные:

   ```bash
   python manage.py seed_data
   ```

   Будут созданы пользователи:

   - `anna@example.com`
   - `ivan@example.com`
   - `maria@example.com`

   Пароль для всех: `teamfinder123`.

7. Запустите сервер:

   ```bash
   python manage.py runserver
   ```

   Приложение будет доступно на [http://127.0.0.1:8000/projects/list/](http://127.0.0.1:8000/projects/list/).

## Проверка без PostgreSQL

Для быстрой локальной проверки можно временно включить SQLite:

```bash
DJANGO_SECRET_KEY=dev-secret DJANGO_DEBUG=True USE_SQLITE=True TASK_VERSION=3 python manage.py migrate
DJANGO_SECRET_KEY=dev-secret DJANGO_DEBUG=True USE_SQLITE=True TASK_VERSION=3 python manage.py seed_data
DJANGO_SECRET_KEY=dev-secret DJANGO_DEBUG=True USE_SQLITE=True TASK_VERSION=3 python manage.py runserver
```

Основной режим проекта для ревью — PostgreSQL через Docker Compose.

## Деплой на Render

Проект подготовлен под Render Blueprint: в корне есть `render.yaml` и `build.sh`.

Самый короткий путь:

1. Загрузите проект в GitHub-репозиторий.
2. В Render откройте **Blueprints** → **New Blueprint Instance**.
3. Выберите GitHub-репозиторий с этим проектом.
4. Render прочитает `render.yaml` и создаст:
   - web service `teamfinder`;
   - PostgreSQL `teamfinder-db`;
   - переменные окружения;
   - build/start команды.
5. После деплоя откройте выданный Render URL.

Build command:

```bash
./build.sh
```

Start command:

```bash
gunicorn team_finder.wsgi:application
```

`build.sh` устанавливает зависимости, собирает static, применяет миграции и загружает демо-данные командой `seed_data`.

На бесплатном тарифе Render приложение может засыпать после простоя, поэтому первый запрос после паузы будет медленнее. Пользовательские media-файлы в этом демо обслуживаются самим Django и подходят для показа проекта, но для долгого production-использования лучше подключить S3/Cloudinary.

## Тесты

```bash
DJANGO_SECRET_KEY=dev-secret DJANGO_DEBUG=True USE_SQLITE=True TASK_VERSION=3 python manage.py test
```

Покрыты базовые сценарии регистрации/логина, фильтрации проектов по навыкам, прав владельца на навыки проекта и участия в проекте.

## Реализованная функциональность

- Кастомная модель `User` с входом по email.
- Генерация первичного аватара пользователя при создании аккаунта.
- Регистрация, вход, выход, смена пароля.
- Просмотр и редактирование своего профиля.
- Список пользователей с пагинацией по 12 карточек.
- Создание и редактирование проектов.
- Просмотр проекта, завершение своего проекта.
- Присоединение к чужому проекту и отказ от участия через AJAX.
- Модель `Skill` для необходимых навыков проекта.
- Добавление и удаление навыков проекта владельцем через AJAX.
- Автодополнение навыков по `/projects/skills/?q=`.
- Фильтр проектов по `?skill=<название навыка>`.
- Админ-панель для пользователей, проектов и навыков.

## Важные URL

- `/projects/list/` — список проектов.
- `/projects/create-project/` — создание проекта.
- `/projects/<id>/` — страница проекта.
- `/projects/<id>/edit/` — редактирование проекта.
- `/users/list/` — список участников.
- `/users/register/` — регистрация.
- `/users/login/` — вход.
- `/users/<id>/` — профиль пользователя.
- `/users/edit-profile/` — редактирование своего профиля.
- `/users/change-password/` — смена пароля.

## Примечания для ревьюера

- `TASK_VERSION=3` выбран по заданию: необходимые навыки проектов.
- Папки `templates_var1` и `templates_var2` оставлены как материалы стартового набора; активный набор выбирается через `TASK_VERSION`.
- Регистрация после создания пользователя ведёт на страницу входа, как указано в функциональном описании и чек-листе сдачи.
- Пользовательские загрузки и локальная SQLite-база игнорируются через `.gitignore`.
- Для публичного демо добавлены `render.yaml`, `build.sh`, Gunicorn, WhiteNoise и поддержка `DATABASE_URL`.
