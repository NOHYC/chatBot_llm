FROM nvidia/cuda:12.8.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV CC=gcc

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash ca-certificates curl git vim \
    x11-apps libgl1 libglib2.0-0 \
    python3 python3-pip python3-venv python3-dev \
    build-essential gcc g++ make \
 && rm -rf /var/lib/apt/lists/*

# uv 설치
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# venv 생성
RUN uv venv /opt/venv --python 3.12 --seed

# venv "activate" 효과를 ENV로 고정
ENV VIRTUAL_ENV="/opt/venv"
ENV PATH="/opt/venv/bin:${PATH}"

# vLLM / bitsandbytes 설치
RUN uv pip install -U "bitsandbytes>=0.46.1" && uv pip install vllm
    


# 빌드 단계에서 vllm --help check
RUN vllm --help

CMD ["/bin/bash"]
