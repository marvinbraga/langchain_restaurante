# Usando Python 3.12 - compatível com as especificações do pyproject.toml
FROM python:3.12-slim-bookworm

WORKDIR /app

# Instalar dependências do sistema necessárias para compilação de algumas bibliotecas
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Criar a estrutura de diretório correta para manter os imports funcionando
RUN mkdir -p /app

# Copiar todos os arquivos da aplicação mantendo a estrutura
COPY ./service2 /app/service2

# Mudar para o diretório do serviço para instalação
WORKDIR /app/service2

# Instalar as dependências de acordo com pyproject.toml
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir \
    python-dotenv==1.1.0 \
    fastapi==0.115.12 \
    uvicorn==0.25.0 \
    redis==6.0.0 \
    langchain==0.3.25 \
    langchain-postgres==0.0.13 \
    langchain-core==0.3.58 \
    langchain-openai==0.3.16 \
    "psycopg[binary]>=3.0" \
    pydantic-settings>=2.0

# Instalar o próprio serviço como um pacote (para resolver os imports relativos)
RUN pip install -e .

# Configurar PYTHONPATH para incluir o diretório pai
ENV PYTHONPATH=/app

EXPOSE 80

# O comando Python inicia o app diretamente
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80"]
