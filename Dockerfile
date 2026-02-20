# Usamos una imagen oficial de Python ligera
FROM python:3.13.3-slim
# Evita que Python escriba archivos .pyc y buffee la salida (logs en tiempo real)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_ROOT_USER_ACTION=ignore

# Directorio de trabajo
WORKDIR /app

# Copiamos requerimientos e instalamos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY cookies.txt .

# Copiamos el código fuente
COPY . .

# Cloud Run inyecta la variable PORT (por defecto 8080)
# Usamos uvicorn para lanzar la app
CMD exec uvicorn gcp_whatsapp.main:app --host 0.0.0.0 --port ${PORT}