# AUT-CLK

Windows-автокликер с GUI на `tkinter`, глобальными хуками мыши/клавиатуры, гибкими настройками CPS, оверлеем-индикатором и локальным TCP bridge для внешнего управления.

## Возможности

- LMB и RMB автокликер с независимыми настройками.
- Режим `Smart` для LMB: диапазон CPS + jitter (рандомизация интервала).
- Глобальный хоткей `Pause/Active` (по умолчанию `~`, можно переназначить).
- Ограничение работы по активному окну (`Window lock`).
- Визуальный оверлей поверх fullscreen/borderless приложений.
- Локальный `Control bridge` (`127.0.0.1:25566`) для удаленного управления состоянием автокликера.
- Кнопка ручного отключения/включения bridge прямо из GUI.

---

## Как работает автоклик

Автокликер не кликает “сам по себе” без нажатия мыши:

- LMB клик идет только когда физически зажата ЛКМ и включен LMB-режим.
- RMB клик идет только когда физически зажата ПКМ и включен RMB-режим.
- При `PAUSED` (глобальная пауза) оба канала клика останавливаются.

Это сделано через глобальные low-level hooks Windows API.

---

## GUI: подробное описание разделов

## 1) `LMB Auto-Click`

- `Enable/Disable` — включает или отключает LMB канал.
- `OFF/ON` — текущий статус канала.
- `Smart mode (range + jitter)`:
  - **выключен**: используется фиксированный `CPS`.
  - **включен**: используется диапазон `Min CPS`–`Max CPS` + `Jitter ms`.
- `Preset`:
  - `Sword PvP` → `(10..15 CPS, jitter 15ms)`
  - `Block Break` → `(18..20 CPS, jitter 5ms)`
  - `Bridge` → `(6..8 CPS, jitter 20ms)`
  - `Custom` — ручные значения.

## 2) `RMB Auto-Click`

- Отдельный `Enable/Disable`.
- Отдельный `CPS` (фиксированный).

## 3) `Toggle hotkey`

- Показывает текущую клавишу глобальной паузы/возобновления.
- `Rebind` переводит в режим ожидания новой клавиши.
- По умолчанию используется `~` (`VK 0xC0`).

## 4) `Window lock`

- `Only run in selected window` — автокликер работает только в выбранном процессе.
- Список окон и кнопка обновления `↻`.
- Используется имя exe активного foreground-процесса.

## 5) `Control bridge`

- Строка статуса:
  - `Bridge: ● Connected` — клиент подключен.
  - `Bridge: ○ Disconnected` — bridge включен, но клиентов нет.
  - `Bridge: OFF` — bridge вручную выключен.
- Кнопка `Disable/Enable`:
  - `Disable` останавливает TCP bridge.
  - `Enable` поднимает bridge снова.
- По умолчанию bridge **включен**.

## 6) `Show overlay indicator` + `Indicator settings`

- Включает/выключает оверлей.
- Формы: `Circle`, `Line`, `Text`.
- Настройки:
  - размер (радиус/ширина/длина/размер текста),
  - позиция `X/Y`,
  - мигание в неактивном состоянии.
- Цветовая логика:
  - зеленый — `ACTIVE`,
  - красный (с миганием, если включено) — `PAUSED`.

## 7) Глобальный статус

- `ACTIVE` / `PAUSED` внизу окна.
- Отражает глобальное состояние автокликера.

---

## Control Bridge (TCP API)

Bridge слушает:

- Host: `127.0.0.1`
- Port: `25566`
- Формат: newline-delimited JSON (`UTF-8`, 1 объект на строку)

### Команда управления (клиент -> AUT-CLK)

```json
{"type":"ac_control","active":true,"lmb_enabled":true,"rmb_enabled":false}
```

Поля можно передавать частично; отсутствующие поля не меняются.

### Статус (AUT-CLK -> клиент)

```json
{
  "type":"ac_status",
  "active":true,
  "lmb_enabled":true,
  "lmb_on":false,
  "lmb_cps":15,
  "rmb_enabled":true,
  "rmb_on":false,
  "rmb_cps":50
}
```

Также поддерживаются `ping/pong`.

Подробный протокол: `autoclicker_techdocs/protocol.md`

## Bridge Client Example

Готовый клиентский мод, который можно использовать вместе с bridge:

- [PLAYRUrk/bws-util-mod](https://github.com/PLAYRUrk/bws-util-mod)

Что это дает в связке с `AUT-CLK`:

- мод подключается к `127.0.0.1:25566`;
- может отправлять команды `ac_control` (`active`, `lmb_enabled`, `rmb_enabled`);
- может читать `ac_status` и отображать состояние автокликера в HUD/GUI.

### Быстрый старт интеграции

1. Запусти `AUT-CLK.exe`.
2. В блоке `Control bridge` убедись, что bridge включен (кнопка должна быть `Disable`).
3. Собери и запусти мод из репозитория `bws-util-mod`.
4. Проверь, что статус в AUT-CLK стал `Bridge: ● Connected`.

### Рекомендации по совместимости

- Держи `Control bridge` включенным, если управляешь автокликером из мода.
- Если переключаешь bridge в `OFF`, внешние команды управления игнорируются до повторного `Enable`.
- При изменениях протокола обновляй и `AUT-CLK`, и мод-клиент синхронно.

---

## Конфигурация (`settings.json`)

Файл создается/обновляется автоматически.

Ключевые поля:

- Clicker:
  - `lmb_cps`, `rmb_cps`
  - `lmb_smart`, `lmb_min_cps`, `lmb_max_cps`, `lmb_jitter_ms`, `lmb_preset`
  - `toggle_vk`
- Overlay:
  - `show_indicator`
  - `indicator_x`, `indicator_y`
  - `indicator_shape`, `indicator_radius`
  - `indicator_line_width`, `indicator_line_length`
  - `indicator_blink`, `indicator_text_size`
- Window lock:
  - `target_window_enabled`
  - `target_process`
  - `target_window_title`

### Где хранится `settings.json`

- В `.py` режиме: рядом с `autoclicker.py`.
- В `.exe` режиме: рядом с `AUT-CLK.exe` (через `sys.executable`).

---

## Запуск из исходников

Требования:

- Windows
- Python 3.14+ (текущий проект собирался на 3.14.2)

Зависимости:

- Внешних зависимостей нет (используется стандартная библиотека Python).

Запуск:

```powershell
python autoclicker.py
```

---

## Сборка `.exe`

В проекте используется `PyInstaller` и файл `AUT-CLK.spec`.

```powershell
python -m PyInstaller --noconfirm "AUT-CLK.spec"
```

Готовый файл:

- `dist/AUT-CLK.exe`

---

## Структура проекта

- `autoclicker.py` — основной код приложения.
- `AUT-CLK.spec` — конфигурация сборки PyInstaller.
- `settings.json` — runtime-настройки.
- `autoclicker_techdocs/` — техническая документация по bridge-протоколу.

---

## Примечания

- Приложение использует глобальные хуки ввода и Win32 API.
- Bridge принимает соединения только с localhost.
- Для стабильной записи настроек `.exe` лучше запускать из каталога с правом записи (не `Program Files`).

