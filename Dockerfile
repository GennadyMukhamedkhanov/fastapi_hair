FROM python:3.12-alpine

ENV HOME=/home/fast \
    PYTHONPATH="$PYTHONPATH:/home/fast" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Устанавливаем PostgreSQL клиент
RUN apk add --no-cache \
    postgresql-client \
    && rm -rf /var/cache/apk/*

# Создаем пользователя и группу
RUN addgroup -S fast && adduser -S fast -G fast

WORKDIR $HOME

# Создаем все необходимые папки и даем права
RUN mkdir -p $HOME/app $HOME/backups $HOME/media $HOME/logs && \
    chown -R fast:fast $HOME && \
    chmod 755 $HOME/backups

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock* ./

RUN uv pip install --system --no-cache -r pyproject.toml

# Копируем код
COPY --chown=fast:fast . .

# Проверяем права
RUN chown -R fast:fast .

USER fast

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]