# syntax=docker/dockerfile:1

# Define the Node.js version to use as a build argument.
ARG NODE_VERSION=20.9.0

#######################################
# Build Stage: Prepare application build
#######################################
FROM node:${NODE_VERSION}-alpine AS builder

# Set the environment to production.
ENV NODE_ENV=production

# Set the working directory inside the container.
WORKDIR /usr/src/app

# Copy dependency definitions (package.json and package-lock.json)
# This leverages Docker caching: if these files haven't changed, npm ci won't run again.
COPY package*.json ./

# Install only production dependencies.
RUN npm ci --omit=dev

# Copy the rest of the application's source code.
COPY . .

#######################################
# Runner Stage: Create a minimal runtime image
#######################################
FROM node:${NODE_VERSION}-alpine AS runner

# Set the environment to production.
ENV NODE_ENV=production

# Set the working directory.
WORKDIR /usr/src/app

# Copy the application from the build stage.
COPY --from=builder /usr/src/app .

# Expose the port the application listens on (changed from 8080 to 8100).
EXPOSE 8100

# Define the command to run the application.
CMD ["npm", "start"]
