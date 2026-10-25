FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DATA_DIR=/srv/data
WORKDIR /srv
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .
COPY data ./data
RUN useradd -r -u 10001 app && chown -R app /srv
USER app
EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request as u; u.urlopen('http://localhost:8000/api/ready')"
CMD ["uvicorn", "windportal.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
