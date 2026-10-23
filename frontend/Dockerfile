FROM node:20-alpine AS builder

WORKDIR /app

# node:20-alpine ships npm 10.8.2, which has a known arborist bug
# ("Cannot read properties of null (reading 'edgesOut')") that can crash
# `npm install` while resolving the dependency tree from package.json alone
# (no lockfile in this repo). Upgrading npm first avoids it.
RUN npm install -g npm@latest

COPY frontend/package.json ./
RUN npm install

COPY frontend/ .
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY frontend/public/favicon.ico /usr/share/nginx/html/favicon.ico
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

RUN printf '#!/bin/sh\n\
sed -i "s|TO_BE_REPLACED_BY_ENTRYPOINT|$BACKEND_URL|g" /usr/share/nginx/html/index.html\n\
exec nginx -g "daemon off;"\n' > /docker-entrypoint.sh && \
    chmod +x /docker-entrypoint.sh

EXPOSE 80
ENTRYPOINT ["/docker-entrypoint.sh"]
