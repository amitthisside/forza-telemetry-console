FROM node:22-alpine AS builder
WORKDIR /app
COPY package.json tsconfig.json tsconfig.app.json vite.config.ts index.html /app/
COPY src /app/src
RUN npm install && npm run build

FROM nginx:1.27-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
