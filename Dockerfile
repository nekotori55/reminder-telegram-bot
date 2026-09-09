FROM python:3.15.0rc2-slim-trixie AS builder
LABEL authors="nekotori55"

WORKDIR /app

RUN python3 -m venv /venv
ENV PATH="/venv/bin:$PATH"

RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    pip install -r requirements.txt

FROM python:3.15.0rc2-slim-trixie

WORKDIR /app

COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

# Copy the source code into the container.
COPY . .

CMD /venv/bin/python3 -m main
