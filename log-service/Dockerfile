# syntax=docker/dockerfile:1

#######################################
# Stage 1: Build Stage
#######################################
FROM node:18-alpine AS builder

# Set the working directory inside the container.
WORKDIR /usr/src/app

# Copy dependency definition files to leverage Docker cache.
# If package.json or package-lock.json doesn't change, this layer is cached.
COPY package*.json ./

# Install all dependencies (including dev dependencies needed for building).
RUN npm install

# Copy the rest of the application source code.
COPY . .

# Build the application (this typically outputs the build artifacts into the 'dist' directory).
RUN npm run build

#######################################
# Stage 2: Production Runner Stage
#######################################
FROM node:18-alpine AS runner

# Install curl for health checks
RUN apk add --no-cache curl

# Set the working directory for the production container.
WORKDIR /usr/src/app

# Copy the built files from the builder stage.
COPY --from=builder /usr/src/app/dist ./dist

# Copy package definition files to install production dependencies.
COPY package*.json ./

# Install only production dependencies to minimize the final image size.
RUN npm install --only=production

# Expose the port that the application listens on.
EXPOSE 8200

# Define the default command to start the application.
CMD ["node", "dist/main.js"]
