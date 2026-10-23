FROM node:20-alpine AS builder

WORKDIR /app

# --legacy-peer-deps works around a live npm/arborist bug (confirmed open
# upstream: npm/cli#9787) that crashes `npm install` with "Cannot read
# properties of null (reading 'edgesOut')" while auto-resolving an optional,
# self-referential peer-dependency set -- the shape vite's own tooling
# declares. Not an npm-version issue (reproduces on 10.8.2 through 10.9.9,
# and differently even on 11.x); this flag skips that resolution path
# entirely instead of auto-installing those peers.
COPY frontend/package.json ./
RUN npm install --legacy-peer-deps

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
