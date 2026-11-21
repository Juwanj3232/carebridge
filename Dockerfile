# One container: build the React frontend, then serve it and the API from server.py.
FROM node:20.18.1-alpine AS web
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.13.5-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HOST=0.0.0.0 PORT=8100
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY server.py ./
COPY backend ./backend
COPY --from=web /app/frontend/dist ./frontend/dist
RUN useradd --create-home carebridge
USER carebridge
EXPOSE 8100
CMD ["python", "server.py"]
