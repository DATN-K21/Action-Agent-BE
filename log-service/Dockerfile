ARG NODE_VERSION=20.9.0

#######################################
# Build Stage
#######################################
FROM node:${NODE_VERSION}-alpine AS builder

WORKDIR /usr/src/app

COPY package*.json ./

RUN npm ci --omit=dev && npm run build

COPY dist .

#######################################
# Runner Stage
#######################################
FROM node:${NODE_VERSION}-alpine AS runner

WORKDIR /usr/src/app

COPY --from=builder /usr/src/app/dist ./

EXPOSE 8200

CMD ["node", "main.js"]