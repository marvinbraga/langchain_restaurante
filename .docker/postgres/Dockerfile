# Atualizando para PostgreSQL 16 - última versão com suporte de longo prazo
# Melhorias: performance em queries paralelas, suporte melhorado a vetores,
# otimizações de memória e novas funcionalidades para análise de dados
FROM postgres:16

# Atualizando todas as dependências do sistema
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y wget build-essential postgresql-server-dev-16

# Atualizando pgvector para a versão mais recente
# A versão 0.5.1 é compatível com PostgreSQL 16 e traz melhorias na indexação de vetores
RUN wget https://github.com/pgvector/pgvector/archive/v0.5.1.tar.gz && \
    tar -xzvf v0.5.1.tar.gz && \
    cd pgvector-0.5.1 && \
    make && \
    make install

# Copiar o script de inicialização do banco de dados
# IMPORTANTE: Com o contexto sendo o diretório raiz, precisamos especificar o caminho completo
COPY ./.docker/postgres/init.sql /docker-entrypoint-initdb.d/
