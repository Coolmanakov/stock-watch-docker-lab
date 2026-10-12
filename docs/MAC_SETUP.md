# Запуск на Mac: инструкция для Дениса

## 1. Что видно на твоём фото

`/usr/local/bin/docker --version` работает: Docker CLI установлен, версия 29.3.1.

`docker: unknown command: docker compose` означает, что этот клиент не обнаружил Compose.

`docker info` сообщает об отсутствии `/var/run/docker.sock`: клиент не смог подключиться к Engine по выбранному адресу. Это не ошибка лабораторной. Engine может быть не установлен, не запущен либо выбран неверный context. Не нужно вручную создавать файл socket.

Docker CLI — команда управления. Docker Engine — среда, которая реально запускает контейнеры. Docker Compose — инструмент, который читает YAML и управляет несколькими контейнерами вместе.

## 2. Установка Docker Desktop

1. Открой https://docs.docker.com/desktop/setup/install/mac-install/ .
2. Выбери версию под процессор своего Mac: Apple silicon для M1/M2/M3/M4 и других M-серий, Intel — для Intel. Если не уверен, проверь меню Apple → «Об этом Mac».
3. Открой `Docker.dmg`, перенеси Docker в «Программы».
4. Запусти Docker из «Программ», пройди первоначальные настройки и дождись готовности Engine. Оставь приложение работающим.
5. Открой новое окно Terminal.

Docker Desktop включает Engine, CLI и Compose. Устанавливать Python, PostgreSQL или Nginx на свой Mac для запуска приложения не требуется.

Проверка:

```bash
docker compose version
docker info
docker context ls
```

`compose version` должен показать версию. В `docker info` должен появиться раздел Server без ошибки соединения.

## 3. Если продолжает использоваться старый `/usr/local/bin/docker`

Проверь клиент прямо из установленного Docker Desktop:

```bash
/Applications/Docker.app/Contents/Resources/bin/docker compose version
/Applications/Docker.app/Contents/Resources/bin/docker context ls
```

Если в списке есть `desktop-linux`, выбери его:

```bash
/Applications/Docker.app/Contents/Resources/bin/docker context use desktop-linux
/Applications/Docker.app/Contents/Resources/bin/docker info
```

Если команды с полным путём работают, для текущего окна терминала можно сделать короткую команду:

```bash
alias docker='/Applications/Docker.app/Contents/Resources/bin/docker'
docker compose version
docker info
```

Эта настройка действует только в этом окне. Она не удаляет твой старый клиент. Можно также продолжать использовать полный путь перед каждой командой. Не требуется заходить в `/usr/local/bin`: команды запускаются из папки проекта.

Если соединение всё ещё идёт по неверному адресу:

```bash
printenv DOCKER_HOST
printenv DOCKER_CONTEXT
```

Если эти значения заданы вручную для другого Engine, сбрось их **только в текущем окне** и повтори выбор `desktop-linux`:

```bash
unset DOCKER_HOST DOCKER_CONTEXT
docker context use desktop-linux
docker info
```

Если `desktop-linux` нет, сначала проверь, что Docker Desktop действительно открыт и закончил запуск. Не переключайся на несуществующий context.

## 4. Запуск проекта из ZIP

Распакуй `Stock-Watch-Docker-Lab.zip`. Внутри будет папка `stock-watch`. Для примера, если она находится в «Загрузках»:

```bash
cd ~/Downloads/stock-watch
ls
docker compose config --quiet
docker compose up --build -d --wait
docker compose ps
```

Если распаковка создала ещё одну внешнюю папку, сначала открой нужную папку через Finder. Самый простой способ получить путь: введи `cd ` в Terminal и перетащи туда папку `stock-watch`, затем нажми Enter. В ней должен лежать `docker-compose.yml`.

Первый запуск скачивает образы и зависимости. Дождись завершения команды. Открой http://localhost:8080 .

Не размещай проект в `/usr/local/bin`: там лежат программы, а не исходники лабораторной.

## 5. Если возникла ошибка

| Симптом | Действие |
| --- | --- |
| `unknown command: compose` | Использовать клиент Docker Desktop из раздела 3 |
| `Cannot connect` / отсутствует socket | Открыть Docker Desktop, проверить `docker info` и context |
| `no configuration file provided` | Перейти в папку с `docker-compose.yml` |
| Порт 8080 занят | Выполнить `FRONTEND_PORT=8081 docker compose up -d --wait`; открывать localhost:8081 |
| Ошибка скачивания образа / DNS / TLS | Проверить интернет и доступ Docker Desktop к Docker Hub; посмотреть текст ошибки, затем повторить запуск |
| Контейнер `unhealthy` | Выполнить команды ниже и посмотреть причину |
| Страница открылась, но запрос не работает | Посмотреть логи backend, db и web-service |

```bash
docker compose ps
docker compose logs --tail=80
```

Не применяй `down -v` как универсальное исправление: она уничтожает товары и историю.

## 6. Запись видео

Перед записью один раз успешно запусти проект и пройди [сценарий защиты](DEFENSE.md). Это позволяет заранее скачать образы. Затем сделай обычный `docker compose down`. При записи покажи `docker compose up --build -d --wait` — повторная сборка будет быстрее.

На Mac запись экрана открывается сочетанием `Shift + Command + 5`. Выбери область записи и в настройках включи нужный микрофон. Можно также показать программу преподавателю напрямую.

Официальные инструкции: https://docs.docker.com/compose/install/ и https://docs.docker.com/desktop/setup/install/mac-install/ .
