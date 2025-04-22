# Nvidia Canary ASR as API-server

## Environment variables

API settings

```dotenv
APP_WORKERS=1
APP_BIND=0.0.0.0
APP_PORT=8000
```

Canary ASR settings

```dotenv
CANARY_MODEL_PATH=./models
CANARY_MODEL_NAME=nvidia/canary-1b-flash
CANARY_BEAM_SIZE=1
CANARY_BATCH_SIZE=1
CANARY_PNC=yes
CANARY_TIMESTAMPTS=no
```
