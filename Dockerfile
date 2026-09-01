FROM python:3.12-slim AS builder
WORKDIR /build
RUN pip install --no-cache-dir build
COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m build --wheel

FROM python:3.12-slim
RUN useradd --create-home --uid 10001 appuser
COPY --from=builder /build/dist/*.whl /tmp/app.whl
RUN pip install --no-cache-dir /tmp/app.whl && rm /tmp/app.whl
USER appuser
EXPOSE 8000
CMD ["python", "-m", "app", "{}"]
