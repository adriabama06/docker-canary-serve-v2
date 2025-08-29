# Canary-Serve: NVIDIA Canary ASR HTTP API

**Русский** | [中文](./README.zh.md) | [English](./README.en.md)

Canary-Serve - это минималистичный FastAPI-сервер, позволяющий работать с многоязычными
`speech-to-text` моделями NVIDIA Canary.

Он позволяет отправить WAV-файл на единственный маршрут `/inference` и получить текстовый
результат или субтитры всего за несколько секунд - максимально эффективно используя
производительность вашей NVIDIA GPU.

## Возможности

* **Отметки времени для слов и сегментов** (только для моделей Flash) через простой флаг timestamps=yes|no.

* **Переключатель PnC** - возможность включать или отключать автоматическую пунктуацию и капитализацию (PnC).

* **Обработка длинных аудиофайлов** - автоматическое разбиение аудио длиннее 10 секунд на части, параллельная обработка
  и последующая сборка.

* **Поддержка нескольких форматов ответов** - text, srt, vtt, json и verbose_json.

* **Docker-Compose с поддержкой GPU** - по умолчанию резервируются все доступные GPU, при этом возможно тонкое
  управление выбором устройств через стандартный `deploy.resources.reservations.devices`.

* **Zero-copy скачивание моделей** - модели скачиваются один раз
  через [huggingface_hub.snapshot_download](./canary_api/utils/download_model.py) и кэшируются локально.

* **Компактный образ** - итоговый Docker-образ построен на `nvidia/cuda:12.6.1-devel-ubuntu22.04`, весит около 4.5 ГБ и
  содержит только необходимые зависимости для выполнения.

## Поддерживаемые модели

* [nvidia/canary-1b-v2](https://huggingface.co/nvidia/canary-1b-v2)
* [nvidia/canary-1b](https://huggingface.co/nvidia/canary-1b)
* [nvidia/canary-1b-flash](https://huggingface.co/nvidia/canary-1b-flash)
* [nvidia/canary-180m-flash](https://huggingface.co/nvidia/canary-180m-flash)

## Поддерживаемые языки

| ISO | Язык    | ASR | Перевод  | Отметки времени (Flash) |
|-----|---------|-----|----------|-------------------------|
| en  | English | +   | de/fr/es | +                       |
| de  | German  | +   | en       | +                       |
| fr  | French  | +   | en       | +                       |
| es  | Spanish | +   | en       | +                       |

> Базовые модели Canary официально поддерживают только эти четыре языка
> как для распознавания речи (ASR), так и для перевода речи в текст.

## Быстрый старт

### Однострочник для запуска через Docker

```shell
docker run --gpus all -it --rm \
  -p 9000:9000 \
  -v $(pwd)/models:/app/models \
  -e CANARY_MODEL_NAME=nvidia/canary-1b-flash \
  evilfreelancer/canary-serve:latest
```

### Запуск через Docker-Compose

В репозитории доступен актуальный [docker-compose.dist.yml](./docker-compose.dist.yml), который автоматически
предоставляет доступ к GPU внутри контейнера.

```shell
cp docker-compose.dist.yml docker-compose.yml
docker compose up -d
```

## Переменные окружения

| Variable           | Default                | Purpose                                             |
|--------------------|------------------------|-----------------------------------------------------|
| CANARY_MODEL_NAME  | nvidia/canary-1b-flash | Название чекпойнта Canary на Hugging Face           |
| CANARY_MODEL_PATH  | ./models               | Путь к локальной директории для кэшированной модели |
| CANARY_BEAM_SIZE   | 1                      | Ширина луча при декодировании                       |
| CANARY_BATCH_SIZE  | 1                      | Размер батча на запрос                              |
| CANARY_PNC         | yes                    | yes для включения пунктуации и регистра             |
| CANARY_TIMESTAMPTS | no                     | yes для активации отметок времени                   |
| APP_BIND           | 0.0.0.0                | IP-адрес для привязки сервера                       |
| APP_PORT           | 9000                   | Порт сервера внутри контейнера                      |
| APP_WORKERS        | 1                      | Количество процессов Uvicorn                        |

## HTTP API

`POST /inference`

* Content-Type: multipart/form-data
* Поля формы:
    * `file` WAV-файл (моно/16 кГц), обязательно
    * `language` en|de|fr|es (по умолчанию en)
    * `pnc` yes|no (по умолчанию yes)
    * `timestamps` yes|no (по умолчанию no, доступно только для Flash-моделей)
    * `beam_size`, `batch_size` (целые числа, опционально)
    * `response_format` json|text|srt|vtt|verbose_json (по умолчанию text)

**Пример запроса**

```shell
curl http://localhost:9000/inference \
  -F file=@sample.wav \
  -F language=de \
  -F response_format=text
```

Пример успешного ответа в формате JSON:

```json
{
  "text": "Guten Tag, hier spricht die KI."
}
```

## Лицензия

Код, Dockerfile и документация этого репозитория распространяются под лицензией MIT - короткой и разрешительной
лицензией, допускающей как коммерческое, так и частное использование при условии сохранения оригинального авторского
права и текста лицензии.

## Цитирование

Если вы используете **Canary-Serve** в академических или продакшен проекта, пожалуйста, указывайте ссылку следующим
образом:

```text
Pavel Rykov. (2025). Canary-Serve: NVIDIA Canary ASR HTTP API (Version 1.0.0) [Computer software]. GitHub. https://github.com/EvilFreelancer/docker-canary-serve
```

BibTeX:

```bibtex
@misc{rykov2025canaryserve,
    author = {Pavel Rykov},
    title = {Canary-Serve: NVIDIA Canary ASR HTTP API},
    howpublished = {\url{https://github.com/EvilFreelancer/docker-canary-serve}},
    year = {2025},
    version = {1.0.0},
    note = {MIT License}
}
```
