FROM python:3.11

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"


COPY ./poetry.lock /
COPY ./pyproject.toml /

RUN useradd -m -o -u 1000 -d /app app \
    && pip install -U poetry \
    && poetry config virtualenvs.create false \
    && GIT_SSL_NO_VERIFY=1 poetry install ${POETRY_INSTALL_ARGS}

COPY ./ /app
WORKDIR /app

ENV PYTHONPATH=/app

RUN python -O -m compileall /app

EXPOSE 8001
CMD bash -c 'echo "Overwrite command for container!"; exit 1'
