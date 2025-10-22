FROM python:3.12-slim

WORKDIR /app

# Installer les outils nécessaires
RUN apt-get update && apt-get install -y \
    zip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Installer AWS CLI
RUN pip install --no-cache-dir awscli

# Copier les requirements
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

CMD ["/bin/bash"]
