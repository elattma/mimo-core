FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.10

ENV YOUR_ENV=production \
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  POETRY_VERSION=1.4.0

# Install poetry separated from system interpreter
RUN pip install "poetry==$POETRY_VERSION"

# Add `poetry` to PATH
ENV PATH="${PATH}:${POETRY_VENV}/bin"

WORKDIR /app

# Install dependencies
COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false \
  && poetry install $(test "$YOUR_ENV" == production && echo "--only main") --no-interaction --no-ansi

RUN python -m nltk.downloader -d ./nltk_data punkt averaged_perceptron_tagger
RUN python -m spacy download en_core_web_sm

# Run your app
COPY . ${LAMBDA_TASK_ROOT}

CMD ["app.handlers.unknown"]