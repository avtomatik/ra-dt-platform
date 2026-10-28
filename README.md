# RA DP — Платформа данных Центра регистрации

RA DP (Registration Authority Data Platform) — локальная платформа для получения, хранения и анализа данных REST API Центра регистрации. Она формирует собственный аналитический слой: синхронизация обращается к внешнему API, а отчёты и исследование данных выполняются по локальной базе.

> **API Центра регистрации — источник данных. Локальная база PostgreSQL — источник аналитики.**

**Статус:** активная разработка, Stage 1 — Data Acquisition Platform.

## Возможности

- клиент REST API и постраничное получение списка сертификатов;
- получение полного представления сертификата и декодирование X.509;
- локальный справочник OID с загрузкой начальных данных из `data/seed/oid_registry.json`;
- хранение сертификатов и их изменяемого жизненного статуса в PostgreSQL;
- синхронизация новых сертификатов и обновление статуса уже известных сертификатов;
- генерация XLSX-отчётов с использованием `xlsxwriter`;
- CLI для диагностики, синхронизации, экспорта и инспекции БД;
- FastAPI-интерфейс;
- транспорт HTTP для разработки и CryptoPro curl для соответствующего рабочего окружения;
- Docker Compose для PostgreSQL, приложения и внешнего планировщика.

## Архитектура

Проект разделяет доменную модель, прикладные сценарии, инфраструктуру и интерфейсы. Зависимости собираются в `radp/bootstrap/container.py`; получение контейнера выполняется через `radp/bootstrap/runtime.py`. Прикладные сценарии зависят от портов, а инфраструктурные адаптеры реализуют эти порты.

```text
REST API Центра регистрации
          │
          ▼
     RAClient / Transport
          │
          ▼
   Synchronization workflow
          │
          ▼
 PostgreSQL: certificates + OID registry
          │
          ├── CLI / DB inspection
          ├── reporting → XLSX
          └── FastAPI

Внешний планировщик (Ofelia) ── запускает CLI по расписанию
```

### Сертификаты и жизненный цикл

Запись сертификата хранится в таблице `certificates`. Неизменяемое содержимое сертификата хранится в JSONB-поле `payload`; поля текущего состояния, включая статус и сведения об отзыве, хранятся отдельно в реляционных столбцах. Для сертификатов не создаётся история снимков (snapshots) или версий.

При синхронизации платформа получает список сертификатов. Для новой записи запрашивается полное представление сертификата и сохраняется его содержимое. Для уже известной записи неизменяемое содержимое не перезаписывается, но актуальные поля жизненного цикла обновляются. История отзыва и доказательства отзыва относятся к источнику данных Центра регистрации (например, CRL), а не к самодельной истории снимков в RADP.

Отчёты работают с локальной базой и не обращаются к REST API напрямую.

### OID Registry

`data/seed/oid_registry.json` — исходный справочник и артефакт bootstrap. При инициализации в БД добавляются отсутствующие определения. База может содержать обогащённые данные; команда `radp oid export` выгружает справочник из БД обратно в JSON в детерминированном порядке. Перед фиксацией такого экспорта рекомендуется просмотреть diff.

### Транспорт

- **HTTP** — локальная разработка, тестирование и эмулятор API.
- **CryptoPro curl** — окружение, в котором требуется транспорт CryptoPro и соответствующая конфигурация mTLS.

Клиент RA API не должен содержать бизнес-логику; реализация транспорта выбирается конфигурацией.

## Структура проекта

Основные каталоги (полный состав зависит от текущего checkout):

```text
radp/
├── application/       # сценарии, порты, синхронизация, отчёты, диагностика
├── bootstrap/         # composition root и инициализация
├── cli/               # команды командной строки
├── config/            # конфигурация и пути
├── domain/            # доменные модели и декодирование сертификатов
├── infrastructure/    # PostgreSQL, репозитории, RA API и transport
├── interfaces/api/    # FastAPI
├── __main__.py        # python -m radp
└── __main__.py        # python -m radp

data/seed/oid_registry.json
data/exports/
docker-compose.yml
```

## Требования и конфигурация

Для локальной разработки нужны Python, `uv` и доступ к PostgreSQL. Для контейнерного запуска нужен Docker с Docker Compose. Установите зависимости проекта:

```bash
uv sync
```

Настройки читаются через Pydantic Settings и переменные окружения с префиксом `RADP_`. Обязательно задайте `RADP_REMOTE_RA__CERTIFICATE_FOLDER`: это имя каталога RA передаётся параметром `folder` при запросе `GET /api/ra/certificates?folder=...`; значение не зашито в код. Compose-файл использует следующие переменные для создания PostgreSQL:

```dotenv
RADP_DATABASE__NAME=radp
RADP_DATABASE__USER=radp
RADP_DATABASE__PASSWORD=replace-with-a-local-password
```

Создайте локальный `.env` из актуального шаблона проекта (если он предусмотрен), задайте параметры подключения к RA API и транспорта в соответствии с настройками `radp/config/settings.py`. Не коммитьте пароли, сертификаты или thumbprint-ы. Имена переменных подключения к БД должны соответствовать модели `Settings` именно в вашем checkout.

## Запуск на хосте через `uv`

`radp` поддерживает запуск как Python-модуля:

```bash
uv run python -m radp --help
uv run python -m radp doctor
uv run python -m radp tables
uv run python -m radp db tables
uv run python -m radp db stats
uv run python -m radp db inspect --table certificates --limit 10
uv run python -m radp db latest-certificates --limit 20
uv run python -m radp db oids --limit 20
uv run python -m radp sync run
# Optional one-off override; .env remains unchanged
uv run python -m radp sync run --certificate-folder "production folder/2026"
uv run python -m radp oid export
uv run python -m radp export excel
uv run python -m radp serve --host 127.0.0.1 --port 9000
```

При запуске CLI с хоста настройте адрес PostgreSQL на `localhost` и используйте только если порт БД намеренно опубликован в вашем локальном Compose override. Базовый Compose должен держать PostgreSQL внутри приватной сети Compose. Если конфигурация не загружает `.env` автоматически, передайте его явно, например `uv run --env-file .env python -m radp tables`. Команды `drop` и `reset` удаляют данные/схему — используйте их только осознанно.

## Запуск через Docker Compose

```bash
docker compose up --build -d
docker compose ps
docker compose logs -f platform scheduler
```

Compose поднимает PostgreSQL, выполняет одноразовый этап создания схемы, запускает API и отдельный планировщик Ofelia. Ofelia запускает команду синхронизации ежедневно в 00:00 по времени контейнера: `python -m radp sync run`. Чтобы изменить расписание, поправьте метку `ofelia.job-exec.sync.schedule` в `docker-compose.yml`. Планировщик внешний по отношению к приложению: внутри RADP не требуется APScheduler. Ofelia получает доступ к Docker API через `/var/run/docker.sock`; суффикс `:ro` делает read-only только само монтирование, но **не** превращает Docker API в read-only. Сохраняйте этот вариант только при осознанном принятии риска оператором системы: ограничьте доступ к хосту и Docker, используйте доверенный и закреплённый образ планировщика, не публикуйте Docker API по TCP и регулярно проверяйте состав запускаемых задач. Изолированная/air-gapped сеть снижает внешнюю экспозицию, но не устраняет риск компрометации хоста или контейнера. Процедура и поля согласования остаточного риска: [`docs/security/docker-socket-risk-acceptance.md`](docs/security/docker-socket-risk-acceptance.md).

Остановка контейнеров без удаления данных:

```bash
docker compose down
```

**Внимание:** `docker compose down -v` удаляет volume PostgreSQL вместе с данными.

## Подключение к PostgreSQL и DBeaver

В Compose сервис БД называется `postgres`. Поэтому приложение и другие контейнеры в сети Compose обращаются к БД по адресу `postgres:5432`. Клиент на хост-машине (например, DBeaver) обращается через опубликованный порт:

| Параметр DBeaver | Значение |
|---|---|
| Driver | PostgreSQL |
| Host | `localhost` |
| Port | `5432` |
| Database | значение `RADP_DATABASE__NAME` из `.env` |
| Username | значение `RADP_DATABASE__USER` из `.env` |
| Password | значение `RADP_DATABASE__PASSWORD` из `.env` |

В DBeaver выберите **New Database Connection → PostgreSQL**, заполните поля выше, нажмите **Test Connection**, затем **Finish**. После старта Compose можно проверить доступность командой `docker compose ps`; логи PostgreSQL доступны через `docker compose logs -f postgres`. Если порт `5432` уже занят на Mac, измените левую часть публикации в Compose, например `15432:5432`, и используйте `localhost:15432` в DBeaver. Не публикуйте PostgreSQL наружу в недоверенной сети; для локальной разработки доступ к `localhost` предпочтительнее.

## CLI: краткий справочник

| Команда | Назначение |
|---|---|
| `python -m radp doctor` | Проверить конфигурацию и доступность компонентов |
| `python -m radp bootstrap` | Инициализировать платформу и OID registry |
| `python -m radp db create` | Создать схему |
| `python -m radp db tables` / `python -m radp tables` | Список таблиц |
| `python -m radp db stats` | Число строк в таблицах |
| `python -m radp db inspect --table TABLE` | Первые строки таблицы |
| `python -m radp sync run [--certificate-folder FOLDER]` | Выполнить синхронизацию; необязательный параметр переопределяет папку из `.env` только для этого запуска |
| `python -m radp oid export` | Экспортировать справочник OID из БД в seed JSON |
| `python -m radp export excel` | Создать XLSX-отчёт |
| `python -m radp export flush` | Вручную удалить XLSX-файлы из `data/exports` (не запускается при старте) |
| `python -m radp serve` | Запустить FastAPI |

## Проверки

```bash
uv run python -m pytest
uv run python -m radp doctor
```

Модульные тесты не заменяют интеграционную проверку с реальным PostgreSQL и доступным RA API. Перед слиянием изменений проверьте подключение, bootstrap, одну синхронизацию, инспекцию таблиц и экспорт.

## Принципы проекта

- Архитектура остаётся простой и явной; runtime — тонкий слой сборки зависимостей.
- Бизнес-логика отделена от REST-транспорта и инфраструктуры хранения.
- PostgreSQL — локальный источник аналитики.
- Содержимое сертификата неизменно после первичного сохранения; текущий жизненный статус обновляется отдельно.
- История snapshots не используется.
- Планирование синхронизации выполняется внешним планировщиком, а не встроенным scheduler-модулем приложения.
- Справочник OID можно воспроизводимо экспортировать из БД в seed JSON.

### Certificate synchronization efficiency

Certificate list pages are parsed into lightweight ID/status summaries. The synchronizer
normalizes RA statuses to canonical values (`VALID`, `REVOKED`, `EXPIRED`) and performs
one status/lifecycle-column lookup for the IDs on each page. It fetches and parses a full
certificate only for new records or when the list status differs from the stored status.

Because the collection endpoint does not expose revocation timestamps/reasons, changes to
those fields without a status change are intentionally not detected by this fast path. A
separate forced-refresh/reconciliation operation would be needed if that case must be covered.

## Лицензия

Проект распространяется в соответствии с лицензией, указанной в файле [LICENSE.md](LICENSE.md).
