FROM python:3.12-alpine

ENV HOME=/home/fast \
    PYTHONPATH="$PYTHONPATH:/home/fast" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN addgroup -S fast && adduser -S fast -G fast

WORKDIR $HOME

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock* ./

RUN uv pip install --system --no-cache -r pyproject.toml

# Копируем все файлы
COPY --chown=fast:fast . .

RUN chown -R fast:fast .

USER fast

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]