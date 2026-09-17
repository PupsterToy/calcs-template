# Worklog — проект «Парсер шоукасов Геншин Импакт»

---
Task ID: 1
Agent: main (Super Z)
Task: Этап 1 — изучить формат входных данных и научиться автоматически извлекать данные из таблиц-шоукасов (лист "Showcase", диапазон-шаблон A4:S12)

Work Log:
- Скачан лист Showcase (gid=121343185) таблицы 19C-JTqT5uSE5RjSPohIz5XeHp1hVfOcJ7ehEYAQiNC4 → download/showcase_template.xlsx (49 КБ)
- Скачана полная книга (82 листа) → download/full_workbook.xlsx (42 МБ)
- Извлечён диапазон A4:S12 (значения + формулы + merged + гиперссылки), изучен raw XML
- Изучен источник карточки: 'Sand Yae Ode Alyo'!AA256:AM262 и шапка расчётного листа (строки 2-8)
- Написан универсальный парсер scripts/showcase_parser.py (URL/файл → JSON)
- Извлечены все 29 команд листа Showcase → download/showcase_all_teams.json (суммы урона сходятся)
- End-to-end тест по URL пройден

Stage Summary:

## ШАБЛОН ВХОДНЫХ ДАННЫХ (запомнить!)

### Источник
Google-таблица: https://docs.google.com/spreadsheets/d/19C-JTqT5uSE5RjSPohIz5XeHp1hVfOcJ7ehEYAQiNC4/edit?gid=121343185#gid=121343185
Это копия шоукаса Timmie's Bird (оригинал: 16FA7FMru_AYqa7J4Sm1RqYrpAr-3rxCrZrMS4JP4OzM).
Нужный лист называется "Showcase" (бывают также "Showcase 2"/"Showcase 3").
Полная книга: 82 листа = Landing, Guide, Showcase, Farming Priority, Template, ~60 расчётных листов команд (напр. "Sand Yae Ode Alyo"), Showcase 2/3, Compact, Vertical, справочные листы (Weapon Data, Character Data, Buffs, ...).

### Сетка листа Showcase
- Командные блоки: 6 колонок × 6 рядов = 36 слотов (29 заполнено).
- Шаг: 19 колонок, 10 строк (9 строк блока + 1 пустая-разделитель).
- Якоря блоков ('Team'): строки 4/14/24/34/44/54; колонки J(10)/AC(29)/AV(48)/BO(67)/CH(86) [+ 6-я колонка CS без Team].
- Карточная область блока начинается в колонке B (якорь Team - 8 колонок).

### Структура блока (на примере A4:S12; якорь 'Team' = (r, c), B-колонка блока bc = c-8)
| Позиция | Содержимое |
|---|---|
| (r, bc) B4 | МАССИВНАЯ ФОРМУЛА ='Имя расчётного листа'!$AA$256:$AM$262 — spill-карточка всей команды. Имя листа = идентификатор команды. 'Sheet Name Here' = пустой слот |
| (r..r+3, bc..bc+7) B4:I7 | 4 merged-карточки 2x4 (B:C, D:E, F:G, H:I) — визуальные портреты, в xlsx пустые (картинки не экспортируются) |
| (r, c..c+4) J4:N4 | Заголовки: Team, Damage, Dist, Field |
| (r, c+6..c+9) P4:S4 | Заголовок 'Extra Information' |
| (r+1..r+4, c) J5:J8 | Имена персонажей с констелляцией: "C0 Sandrone", "C1 Yae Miko", ... |
| (r+1..r+4, c+2) L5:L8 | DPR персонажа (урон за ротацию) |
| (r+1..r+4, c+3) M5:M8 | Доля урона (0-1; сумма = 1) |
| (r+1..r+4, c+4) N5:N8 | Время на поле, сек |
| (r+4, bc+0/2/4/6) B8/D8/F8/H8 | Оружие персонажей 1-4 (merged пары B:C и т.д.; +гиперссылки на вики) |
| (r+5, bc+0/2/4/6) B9... | Сет артефактов (свои названия: Disenchant, Tenacity, 7.0 Supp) |
| (r+6, bc+0/2/4/6) B10... | Требования ER ("129% ER") |
| (r+5, c) J9 | 'Total DPR' (метка) |
| (r+5, c+2) L9 | Суммарный DPR команды |
| (r+5, c+3) M9:N9 | Дата (=TODAY() в источнике; в xlsx — serial date) |
| (r+6, c) J10 | Длина ротации, сек (21.0 = сумма field time) |
| (r+6, c+2) L10 | DPS = TotalDPR / время ротации |
| (r+6, c+3) M10:N10 | Автор ("Timmie's Bird") |
| (r+7, bc) B11 | Метка 'Rot' |
| (r+7, bc+1) C11:N12 | ТЕКСТ РОТАЦИИ: "Ode EE, Yae EEE, Alyo QE, Sand CECE (Q) CE" |
| (r+8, bc) B12 | Метка 'Sheet' (гиперссылка на расчётный лист; в xlsx теряется — имя берём из формулы B4) |
| (r+1..r+8, c+6..c+9) P5:S12 | Extra Information (merged, примечания автора) |

### Схема извлечения (scripts/showcase_parser.py)
- find_team_anchors(): поиск всех ячеек со значением 'Team' → (r, c)
- calc_sheet: regex из формулы в (r, c-8): ^='(.*?)'!\$AA\$
- Персонажи: строки r+1..r+4, имя в col c; оружие/сет/ER — колонки bc+2*i, строки r+4/r+5/r+6
- Итоги: L9/L10/M9/J10; ротация: (r+7, bc+1); extra: (r+1..r+8, c+6..c+9)
- Слот пуст ⇢ формула = 'Sheet Name Here' или нет имён

### Особенности экспорта/доступа
- Скачать лист: /export?format=xlsx&gid={gid} (gid листа Showcase = 121343185); без gid — вся книга (42 МБ)
- Гиперссылки на оружие в B8/F8/H8 (Fandom wiki), B12 — внутренняя (теряется)
- Google разворачивает spill-массив B4 в статические значения ячеек → xlsx листа-одиночки содержит ВСЕ данные даже без расчётных листов
- Лёгкая альтернатива: gviz CSV (/gviz/tq?tqx=out:csv&gid=...&range=A4:S12) — работает, но значения отформатированы ("1,959,082", "51.09%", "14.5s") — теряется точность; xlsx предпочтителен
- M9 — дата auto-update (TODAY), не показатель

### Расчётные листы (для будущих этапов)
Шапка расчётного листа ('Sand Yae Ode Alyo'): H2='Team Damage', H3:H6 = имена, I3:I6 = урон, J2='Rotation', J3 = текст ротации, G3:G6 = 'время | ER%' по персонажам, B5 = автор. Зеркало шоукаса на AA256:AM262 (те же смещения, что и блок). ВАЖНО: J3 расчётного листа содержит ту же ротацию, что и C11 шоукаса.

### Артефакты
- download/showcase_template.xlsx — лист Showcase (сохранён)
- download/full_workbook.xlsx — полная книга, 82 листа (сохранён)
- download/showcase_all_teams.json — все 29 команд, структурированный JSON (main-результат)
- scripts/showcase_parser.py — переиспользуемый парсер (URL|файл → JSON)
- scripts/a4_s12_template.json — сырой дамп шаблонного диапазона A4:S12

### Контроль качества
- sum(урон персонажей) == Total DPR по всем 29 командам (расхождение < 0.1%) ✓
- sum(доли) == 1.0 ✓; sum(field_time) == J10 (длина ротации) ✓; DPS == TotalDPR / время ✓
- End-to-end по URL ✓

---
Task ID: 2
Agent: main (Super Z)
Task: Этап 1.5 — (2-a) поддержка CSV в парсере; (2-b) HTML-страница со всеми командами

Work Log:
- Скачан лист Showcase в CSV: /export?format=csv&gid=121343185 -> download/showcase_sheet.csv (20 КБ, 64 строки, 111 полей)
- Изучен формат CSV: та же блочная структура и смещения, якоря 'Team' на тех же позициях (29 шт); значения отформатированы ("1,959,082", "51.09%", "14.5s", дата "9/17/2026"); формулы/гиперссылки теряются
- Обновлён scripts/showcase_parser.py: download_google_csv(), класс CsvSheet (адаптер CSV под интерфейс openpyxl-листа, 1-based, cell/iter_rows), _load_sheets() (Google-URL xlsx/csv, локальные .xlsx/.csv), _num() понимает проценты/суффикс 's', _iso() парсит даты строками, is_empty теперь по наличию персонажей (calc_sheet в CSV = None)
- Тест scripts/test_csv_vs_xlsx.py: CSV-файл и CSV-URL дают те же 29 команд, что и xlsx (макс. расхождение: урон 0.492, доля 0.00005, DPR 0.487, DPS 0.482 — округление CSV); ротации/авторы/даты/оружие/сеты/ER совпадают точно
- Результаты: download/showcase_all_teams_csv.json (CSV-режим)
- Написан генератор scripts/make_showcase_html.py -> download/showcase.html (45.8 КБ, автономный, данные встроены, без внешних запросов)
- QA в headless-браузере (agent-browser): 29 карточек, статистика (29 команд / 18 персонажей / лучший DPR 5 361 521 / лучший DPS 255 311), бейдж "Топ DPS", поиск "Cyno" -> 4 команды, сортировка по времени ротации работает, ошибок JS нет; скриншот download/showcase_preview.png

Stage Summary:
- Парсер теперь принимает: Google-URL (xlsx), Google-URL (csv: format=csv / out:csv), локальный .xlsx, локальный .csv
- Особенности CSV-режима (запомнить): значения теряют точность (округление до целых, проценты до 2 знаков), calc_sheet недоступен (формулы не экспортируются), даты в формате M/d/yyyy
- HTML: тёмная GI-тема, поиск (команда/персонаж/оружие/сет), сортировки (DPR/DPS/время/имя), карточки со стек-баром долей урона, оружием/сетами/ER, ротацией, автором; полностью офлайн
- Артефакты: download/showcase_sheet.csv, download/showcase_all_teams_csv.json, download/showcase.html, download/showcase_preview.png, scripts/test_csv_vs_xlsx.py, scripts/make_showcase_html.py

---
Task ID: 3
Agent: main (Super Z)
Task: Этап 2 — (а) простые скрипты «только видимые значения» (xlsx + CSV); (б) пояснение «слот R2·C1» на HTML-странице; (в) ответ про GitHub Pages; (г) динамическая страница (Next.js) с загрузкой xlsx/CSV/ссылки

Work Log:
- Исследованы эндпоинты для браузерной загрузки: /export?format=csv — CORS OK (echo Origin + финальный ACAO:* после 307-редиректа), строки 1:1; gviz — CORS OK, но ПРОПУСКАЕТ пустые строки (якоря 4→1, 14→10) и НЕ вычисляет межлистовые формулы (автор пустой)
- Создан scripts/simple_xlsx.py: только видимые значения (data_only=True), без формул/calc_sheet/гиперссылок; метки слотов R·C по ПОЗИЦИИ якоря (не по абсолютным координатам)
- Создан scripts/simple_csv.py: тот же простой формат для CSV (файл или Google-ссылка через /export?format=csv)
- scripts/test_simple_parsers.py: xlsx 29/29 ТОЧНО, csv-файл 29/29 (допуск округления), csv-URL 29/29 → download/showcase_simple.json + showcase_simple_csv.json
- make_showcase_html.py: добавлена легенда «Что означает слот R2·C1» (раскрыта по умолчанию) + тултипы на бейджах слотов → showcase.html регенерирован (48,6 КБ), JS проверен node --check
- Динамическая страница (Next.js 16, клиентский парсинг): src/lib/showcase/{types,csv,parse,xlsx,google,format}.ts — TS-порт простых скриптов; SheetJS (xlsx) для файлов, собственный RFC4180-парсер CSV, ссылка → export CSV (фолбэк gviz, тогда якоря скрыты через alignedRows:false)
- UI (тёмная GI-тема): src/app/page.tsx + components/showcase/{source-panel,team-card,slot-legend}.tsx; дроп-зона xlsx/csv, поле ссылки, выбор листа при отсутствии Showcase*, демо-данные по умолчанию (src/data/demo-teams.json = showcase_simple.json), легенда слотов, поиск/сортировки/статистика/тултипы
- next.config.ts: BUILD_MODE=export → output:'export' + distDir '.next-export' (не трогает .next дев-сервера); NEXT_PUBLIC_BASE_PATH для GitHub Pages; package.json: build:static/build:pages; api/route.ts → force-static
- Тесты: bun scripts/ts-parser-test.ts — xlsx deep-equal эталону, csv/gviz/URL в допуске, все PASS; lint 0 ошибок
- Браузер (agent-browser): 29 карточек демо, поиск Cyno→4, ссылка на лист→fetch export CSV→29 команд (источник «Google Sheets · CSV»), upload xlsx и csv → 29 команд, возврат к демо, ошибок нет; мобильная вёрстка 390/390 без скролла (исправлен flex-ряд ссылки: min-w-40 flex-1 flex-wrap)
- Статическая сборка проверена: BUILD_MODE=export next build → .next-export/ = готовый сайт (index.html+ассеты); поднят http.server:8788 → страница работает, upload работает, без ошибок

Stage Summary:
- «Простой» формат JSON: showcase-simple/1 — slot (R·C позиционно), anchor/range (для выравненных источников), team_name (из имён персонажей — calc_sheet больше не нужен), персонажи, DPR/DPS/ротации; сложный парсер showcase_parser.py НЕ тронут (пользователь просил сохранить)
- Ключевой вывод по размещению: фулл-стек с бэкендом на GitHub Pages НЕВОЗМОЖЕН (статика); выбрана клиентская архитектура — вся страница = статика, парсинг в браузере; для серверного Python — Vercel/Netlify/Cloudflare (бесплатно)
- По ссылке из браузера доступен только CSV (export/gviz, CORS); xlsx — только файлом (export?format=xlsx без CORS)
- Деплой на GH Pages: bun run build:static → содержимое .next-export/ на ветку/Actions; для проекта вида user.github.io/repo — NEXT_PUBLIC_BASE_PATH=/repo
- Артефакты: scripts/simple_xlsx.py, scripts/simple_csv.py, scripts/test_simple_parsers.py, scripts/ts-parser-test.ts, download/showcase_simple.json, download/showcase_simple_csv.json, download/showcase.html (обновлён), download/app_preview.png, download/app_preview_mobile.png, .next-export/ (статический сайт)

---
Task ID: 4
Agent: main (Super Z)
Task: Архитектурная консультация — пользователь усомнился в решении «фулл стак»: «простого сайта достаточно или динамический был правильным?»

Work Log:
- Проверено фактическое состояние этапа 2: страница — клиентское SPA без сервера; next.config.ts поддерживает BUILD_MODE=export (статика для GitHub Pages); dnd-kit уже в зависимостях (задел под drag&drop конструктор)
- Сопоставлены все заявленные будущие фичи с клиентскими технологиями: шаблоны (React-компоненты/CSS-темы), скриншоты (html-to-image — DOM→PNG в браузере), iframe (URL + сжатые данные в hash), правка на лету (React-состояние), drag&drop (dnd-kit) — сервер не требуется ни для одной
- Выявлена единственная «пограничная» фича: iframe с пользовательскими данными — сжатый URL-hash ок для 1 карточки; для целых листов при росте объёмов может позже понадобиться serverless-хранилище (free-tier)

Stage Summary:
- Вердикт: «динамический» — правильное решение, но фулл стака (сервера) мы НЕ делали и не нужно: текущая реализация = динамическое SPA, хостящееся как статика (GitHub Pages совместима, `bun run build:static` → `.next-export/`)
- Правило на будущее: «изменяется на экране без перезагрузки» = клиент; «хранить/шарить между устройствами, аккаунты, секретные ключи, серверный рендер» = сервер (тогда free-tier Vercel/Cloudflare/Supabase; Next.js добавляет API-роуты к текущему коду без переписывания — тупика нет)
- Ничего переделывать не требуется

---
Task ID: 5
Agent: main (Super Z)
Task: (а) как открыть страницу в окне демонстрации + какой файл основной; (б) подготовка репозитория и пошаговая инструкция по публикации на GitHub Pages

Work Log:
- Проверено: dev-сервер на :3000 отвечает 200 (страница уже запущена в песочнице); превью-URL из env/конфигов не извлекается — направил пользователя к кнопке предпросмотра интерфейса
- Основной файл страницы: src/app/page.tsx; указана полная карта файлов (компоненты src/components/showcase/, парсеры src/lib/showcase/, демо-данные src/data/demo-teams.json); предупреждение: download/showcase.html — старая простая страница этапа 1.5, не путать
- Создан .github/workflows/deploy.yml: авто-сборка GitHub Pages (checkout → setup-bun → bun install --frozen-lockfile → prisma generate → вычисление basePath из имени репозитория → bun run build:static → upload → deploy); триггер: push в main + workflow_dispatch; YAML провалидирован (python yaml)
- basePath вычисляется динамически: repo «user.github.io» → пустой, иначе «/repo-name» — оба типа адресов работают без правок
- Чистка git-индекса (репозиторий песочницы содержал 44 МБ закоммиченного): git rm --cached для download/ (вкл. full_workbook.xlsx 42 МБ), db/, .env, .zscripts/, mini-services/, tests/, examples/, Caddyfile, scripts/__pycache__/, scripts/xml_check/; .gitignore дополнен соответствующими правилами; два коммита; итог: 908 КБ, только исходники
- Проверено: bun install --frozen-lockfile — синхронно (CI не упадёт на lockfile)
- Создан архив исходников: git archive HEAD → download/showcase-site-source.zip (232 КБ, 109 файлов: .github/, src/, scripts/, public/, конфиги, без .git) — пользователь скачивает, распаковывает, делает git init + push
- В чате выдана пошаговая инструкция: аккаунт GitHub → скачивание архива → установка git (или GitHub Desktop) → создание репозитория → git init/add/commit/remote/push с пояснением каждой команды → Settings → Pages → Source: GitHub Actions → URL сайта; + раздел «если что-то пошло не так»

Stage Summary:
- Репозиторий теперь «публикуемый»: 908 КБ исходников, авто-сборка на GitHub Actions, тяжёлые данные и служебные файлы песочницы исключены (но ОСТАЮТСЯ на диске — ничего не удалено)
- Воркфлоу сам подстраивает basePath под имя репозитория; для обновления сайта в будущем: новые исходники → git push → GitHub пересобирает автоматически
- Артефакты: .github/workflows/deploy.yml, download/showcase-site-source.zip, обновлённый .gitignore
- Пользователю сообщено: превью — через кнопку предпросмотра интерфейса; основной файл — src/app/page.tsx

---
Task ID: 5-b
Agent: main (Super Z)
Task: Техподдержка — пользователь не нашёл download/showcase-site-source.zip в интерфейсе

Work Log:
- Проверено: файл существует (235 944 байта, mtime обновлена touch), unzip -t — «No errors detected» (архив валиден)
- Гипотеза: файл создан через Bash (git archive), панель файлов интерфейса могла не обновить список; после touch файл должен отображаться как самый новый в папке download
- Пользователю выданы инструкции: обновить страницу/панель, искать в папке download (в алфавитном порядке файл идёт после full_workbook.xlsx, перед showcase.html); план Б — перегенерация архива или разбор панели по скриншоту

Stage Summary:
- Файл на диске есть и валиден; проблема на стороне отображения UI, а не файловой системы

---
Task ID: 5-c
Agent: main (Super Z)
Task: Файл zip не отображается в панели chat.z.ai — организовать передачу архива пользователю другим способом

Work Log:
- Диагноз: веб-интерфейс chat.z.ai, судя по всему, не показывает .zip в панели файлов (файл на диске есть, после touch и F5 всё равно не виден)
- Решение — раздача через сам сайт: download/showcase-site-source.zip скопирован в public/showcase-site-source.zip; Next dev-сервер отдаёт файлы из public/ по прямой ссылке
- page.tsx: в футер добавлена кнопка «⬇ Скачать исходники сайта», рендерится ТОЛЬКО при NODE_ENV=development (в превью песочницы — есть, в статической сборке для GitHub — исчезает)
- .gitignore: добавлено /public/*.zip — архив не попадёт в репозиторий и на GitHub Pages
- Проверено curl: /showcase-site-source.zip → HTTP 200, application/zip, 235 944 байта, бинарно идентичен оригиналу (cmp); страница скомпилировалась без ошибок, ссылка присутствует в HTML
- Пользователю объяснено: открыть превью → прокрутить в самый низ → нажать кнопку; альтернатива — дописать /showcase-site-source.zip к адресу превью в строке браузера

Stage Summary:
- Универсальный канал передачи бинарных файлов пользователю: папка public/ работающего сайта (dev-превью); кнопка в футере только для dev-сборки
- Для будущих поставок: если панель файлов не показывает тип файла — класть его в public/ и давать ссылку/кнопку

---
Task ID: 6
Agent: main (Super Z)
Task: Фиксы первого деплоя на GitHub: (а) падение configure-pages «Get Pages site failed: Not Found»; (б) объяснение, почему push с LICENSE отклонялся; (в) предупреждение Node 20

Work Log:
- Диагноз (а): у пользователя не включён Pages в Settings → configure-pages@v5 читает настройки Pages через API → 404 Not Found → сборка падает. Исправление: в воркфлоу добавлен параметр enablement: true (сам включает Pages при первом запуске; рекомендуем сам текст ошибки действия)
- Диагноз (б): пользователь добавлял LICENSE через веб-интерфейс GitHub (виджет «Add a license») → коммит создался на стороне GitHub → локальный компьютер о нём не знал → push отклонён (non-fast-forward, «remote contains work that you do not have locally») → пользователь удалил LICENSE на сайте, после чего push прошёл. Правильный паттерн: правки на сайте → перед следующим push делать git pull
- Диагноз (в): «Node 20 is being deprecated» — уведомление о среде выполнения экшенов (GitHub автоматически гоняет их на Node 24), НЕ причина падения; вникать не требуется
- LICENSE (MIT) добавлен в репозиторий с плейсхолдером «ВАШ-НИК-GitHub» — пользователь заменит на свой ник; в будущем можно зашивать реальный ник, если пользователь его сообщит
- Коммит; архив пересобран в download/ и public/ (кнопка в превью отдаёт свежую версию, 239 317 байт); проверено: enablement: true и LICENSE внутри архива, YAML валиден
- Пользователю выданы два пути: (1) рекомендуемый — скачать новый архив из превью, распаковать с заменой в папку проекта, поправить LICENSE, git add/commit/push (новый push сам запустит сборку, а enablement сам включит Pages); (2) быстрый — Settings → Pages → Source: GitHub Actions, затем Actions → Re-run all jobs (но LICENSE и самовключение при этом не появятся)

Stage Summary:
- Воркфлоу теперь самодостаточен: свежий репозиторий + push = сайт без ручных переключателей
- Архив download/showcase-site-source.zip и public/showcase-site-source.zip синхронны с HEAD (enablement + LICENSE)
- Урок для пользователя задокументирован в чате: веб-правки GitHub ↔ git pull перед push
