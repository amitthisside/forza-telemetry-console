FROM node:22-alpine AS builder
WORKDIR /app

COPY apps/web/package.json /app/package.json
COPY apps/web/tsconfig.json /app/tsconfig.json
COPY apps/web/tsconfig.app.json /app/tsconfig.app.json
COPY apps/web/vite.config.ts /app/vite.config.ts
COPY apps/web/index.html /app/index.html
COPY apps/web/eslint.config.js /app/eslint.config.js
COPY apps/web/src /app/src

RUN npm install && npm run build

FROM nginx:1.27-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
