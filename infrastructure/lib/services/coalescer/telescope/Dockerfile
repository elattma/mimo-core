FROM python:3.9-slim-buster

# Install poetry separated from system interpreter
RUN pip install "poetry==$POETRY_VERSION"

# Add `poetry` to PATH
ENV PATH="${PATH}:${POETRY_VENV}/bin"

WORKDIR /app

# Install dependencies
COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false \
  && poetry install $(test "$YOUR_ENV" == production && echo "--only main") --no-interaction --no-ansi

# Run your app
COPY . /app/

CMD ["python", "app.py"]