FROM node:20-alpine AS builder

WORKDIR /app

# node:20-alpine ships npm 10.8.2, which has a known arborist bug
# ("Cannot read properties of null (reading 'edgesOut')") that can crash
# `npm install` while resolving the dependency tree from package.json alone
# (no lockfile in this repo). Pinned to the latest 10.x patch rather than
# `@latest`: npm 12 requires Node >=22, which node:20-alpine doesn't have,
# and `@latest` is a moving target that will break this build again the
# next time npm cuts a major that drops Node 20 support.
RUN npm install -g npm@10.9.9

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
