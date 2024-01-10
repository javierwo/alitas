# Usa una imagen base de Python
FROM python:3.10

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia los archivos de requisitos y los instala
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copiamos los archivos necesarios al contenedor
COPY app.py .
COPY config.yaml .

# Expone el puerto en el que se ejecutará la aplicación
EXPOSE 8501

# Define el comando para ejecutar la aplicación
CMD ["streamlit", "run", "app.py"]