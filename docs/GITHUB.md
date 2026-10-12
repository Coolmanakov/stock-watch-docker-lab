# Публикация на GitHub

Исходники готовы к публикации. ZIP содержит файлы проекта, не готовый публичный репозиторий. Доступ к аккаунту GitHub в среде подготовки не подключён, поэтому публикация ещё не выполнена.

## Через сайт — без настройки Git

1. Войди на github.com под своим аккаунтом.
2. Создай **New repository** с именем `stock-watch-docker-lab`, видимостью **Public**. Не добавляй автоматически README, .gitignore и лицензию: README и .gitignore уже есть в проекте.
3. Нажми загрузку существующих файлов — **uploading an existing file** или **Add file → Upload files**.
4. Загрузи **содержимое** папки `stock-watch`: в корне репозитория должны быть `docker-compose.yml` и `README.md`, а не вложенная папка `stock-watch`.
5. Убедись, что `.gitignore`, `.env.example`, `.dockerignore` и `.github/workflows/verify.yml` тоже загружены. Finder скрывает файлы с точкой; `Command + Shift + .` включает их показ. Для скрытых файлов и папок надёжнее использовать Git ниже.
6. Нажми **Commit changes**. Открой README, затем Actions → Verify lab. Дождись результата workflow.
7. В README есть ссылка на отчёт `docs/REPORT.md`: он входит в репозиторий.

Не загружай сам ZIP вместо исходников. Не добавляй локальный `.env`.

## Через Git

Создай пустой публичный репозиторий на сайте. В папке проекта выполни:

```bash
git init -b main
git add .
git status
git commit -m "Add Docker Compose stock management lab"
git remote add origin https://github.com/YOUR_USERNAME/stock-watch-docker-lab.git
git push -u origin main
```

**Перед выполнением замени `YOUR_USERNAME` своим логином.** Если Git попросит имя и email автора коммита, задай их локально в этой папке:

```bash
git config user.name "Denis Kulmanakov"
git config user.email "YOUR_VERIFIED_OR_NOREPLY_EMAIL"
```

Для HTTPS push GitHub не принимает обычный пароль аккаунта. Используй установленный менеджер учётных данных, SSH или вход через GitHub CLI. Пароли и токены не вставляй в исходники и не присылай в чат.

Если установлен GitHub CLI, после входа можно создать репозиторий и отправить файлы одной командой:

```bash
gh auth login
gh repo create stock-watch-docker-lab --public --source=. --remote=origin --push
```

Последнюю команду используй вместо `git remote add`/`git push` и только если репозиторий ещё не создан; предварительно должен существовать локальный commit.

## После публикации

В таблице группы https://docs.google.com/spreadsheets/d/1nQfg12wMu-y7ty3KbT6d3xw9Anem5EmKt5rjLpNHdjQ/edit у своей фамилии укажи тему №55 «Учёт остатков на складе» и ссылку на созданный репозиторий. Не копируй ссылку с `YOUR_USERNAME`: нужна фактическая ссылка твоего репозитория. В таблицу при подготовке проекта изменения не вносились.
