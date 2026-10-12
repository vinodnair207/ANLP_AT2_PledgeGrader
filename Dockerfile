# Container for the Hugging Face Spaces Docker SDK. Builds the React frontend, then serves it
# and the FastAPI backend from one process on port 7860.

# Stage 1: builds the React frontend into frontend/dist.
FROM node:22-slim AS frontend
WORKDIR /frontend
# The package files are copied first so that the npm install layer is cached between builds.
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python runtime with the API, the models and the built frontend.
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/home/user/.cache/huggingface \
    PATH=/home/user/.local/bin:$PATH

# Hugging Face Spaces runs containers as a user with id 1000.
RUN useradd -m -u 1000 user
USER user
WORKDIR /home/user/app

# The CPU build of torch is installed first because the default wheel adds several gigabytes of GPU libraries.
# The extra index lets pip prefer the CPU build of the pinned version and fall back to PyPI if it is missing.
COPY --chown=user requirements.txt .
RUN pip install --user --extra-index-url https://download.pytorch.org/whl/cpu \
        "$(grep -E '^torch==' requirements.txt | head -1 | tr -d ' ')" \
    && grep -v -E '^(nvidia|cuda|triton)' requirements.txt > requirements.cpu.txt \
    && pip install --user -r requirements.cpu.txt

COPY --chown=user config ./config
COPY --chown=user src ./src
COPY --chown=user outputs ./outputs
COPY --chown=user --from=frontend /frontend/dist ./frontend/dist

# Downloads the pinned ClimateBERT weights during the build, so that the first request does not wait for them.
RUN python -c "import yaml, huggingface_hub as h; c = yaml.safe_load(open('config/config.yaml'))['climatebert']; h.snapshot_download(c['hub_repo'], revision=c['hub_revision'])"

EXPOSE 7860
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "7860"]
