FROM nvcr.io/nvidia/nemo:25.02
WORKDIR /app


# Anti-"sanction" fix
RUN set -xe \
 && sed -r 's#developer.download.nvidia.com#mirror.yandex.ru/mirrors/developer.download.nvidia.com#g' -i /etc/apt/sources.list.d/cuda-*.list

# Install dependencies
RUN set -xe \
 && apt update -q \
 && apt install -fyq \
        bash git cmake portaudio19-dev \
        python3 python3-pip time \
 && apt clean

# Install Python packages
COPY requirements.txt .
RUN set -xe \
 && pip install --no-cache-dir -r requirements.txt

# Copy sources
COPY . .
RUN set -xe \
 && git submodule update --init --recursive
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
