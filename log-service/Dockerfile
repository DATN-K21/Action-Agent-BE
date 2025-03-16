ARG NODE_VERSION=20.9.0

#######################################
# Builder Stage
#######################################
FROM node:${NODE_VERSION}-alpine AS builder
ENV NODE_ENV=build

WORKDIR /home/node

COPY package*.json ./
RUN npm ci --omit=dev \
  && npm install -g @nestjs/cli

COPY . .
RUN npm run build \
  && npm prune --omit=dev


#######################################
# Runner Stage
#######################################
FROM node:${NODE_VERSION}-alpine
ENV NODE_ENV=production

WORKDIR /home/node

COPY --from=builder /home/node/package*.json ./
COPY --from=builder /home/node/node_modules/ ./node_modules/
COPY --from=builder /home/node/dist/ ./dist/

CMD ["node", "dist/main.js"]
