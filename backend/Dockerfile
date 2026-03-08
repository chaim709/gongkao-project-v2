# 阶段1：安装依赖
FROM python:3.11-slim AS builder

WORKDIR /app

# 安装系统依赖（含 Playwright 所需的浏览器依赖）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libxshmfence1 \
    libx11-xcb1 \
    libxcb1 \
    libxfixes3 \
    libxkbcommon0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgcc-s1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libstdc++6 \
    libx11-6 \
    libxcb-shm0 \
    libxext6 \
    fonts-wqy-zenhei \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装 Playwright Chromium 浏览器
RUN python -m playwright install chromium

# 阶段2：运行
FROM python:3.11-slim

WORKDIR /app

# 安装运行时所需的系统库
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libxshmfence1 \
    libx11-xcb1 \
    libxcb1 \
    libxfixes3 \
    libxkbcommon0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgcc-s1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libstdc++6 \
    libx11-6 \
    libxcb-shm0 \
    libxext6 \
    fonts-wqy-zenhei \
    && rm -rf /var/lib/apt/lists/*

# 从 builder 复制 Python 包和 Playwright 浏览器
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /root/.cache/ms-playwright /home/appuser/.cache/ms-playwright

# 创建非 root 用户
RUN groupadd -r appuser && useradd -r -g appuser -d /home/appuser -s /sbin/nologin appuser

# 复制应用代码
COPY . .

# 创建上传目录 + 设置权限
RUN mkdir -p uploads && chown -R appuser:appuser /app /home/appuser && chmod +x start.sh

# 切换到非 root 用户
USER appuser

# 暴露端口
EXPOSE 8000

# 启动命令（含数据库迁移）
CMD ["./start.sh"]
