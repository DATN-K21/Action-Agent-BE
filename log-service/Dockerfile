# Stage 1: Build
FROM node:18 as builder

# Set the working directory
WORKDIR /usr/src/app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application files
COPY . .

# Build the application
RUN npm run build

# Stage 2: Run
FROM node:18

# Set the working directory
WORKDIR /usr/src/app

# Copy the built files and necessary configs from the builder stage
COPY --from=builder /usr/src/app/dist ./dist
COPY package*.json ./

# Install only production dependencies
RUN npm install --only=production

# Expose the application port
EXPOSE 8101

# Define the default command
CMD ["node", "dist/main.js"]
