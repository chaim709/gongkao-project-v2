# 阶段1：构建
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
RUN npm run build

# 阶段2：Nginx 服务
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
# 默认 nginx 配置（生产环境通过 docker-compose volume 覆盖）
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
