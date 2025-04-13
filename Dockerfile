FROM python:3.10-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    unzip \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libgdk-pixbuf2.0-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    ca-certificates \
    chromium \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver matching known version 135.0.7049.84
RUN wget -q https://chromedriver.storage.googleapis.com/135.0.7049.84/chromedriver_linux64.zip -O chromedriver.zip && \
    unzip chromedriver.zip && \
    mv chromedriver /usr/bin/chromedriver && \
    chmod +x /usr/bin/chromedriver && \
    rm chromedriver.zip

# Set environment variables
ENV CHROME_BIN="/usr/bin/chromium"
ENV GOOGLE_CHROME_BIN="/usr/bin/chromium"
ENV CHROMEDRIVER_PATH="/usr/bin/chromedriver"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . /app
WORKDIR /app

# Run Streamlit app
CMD streamlit run app.py --server.port=$PORT --server.enableCORS=false
