# Build stage
FROM node:18-alpine as build
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

# Development configuration
FROM node:18-alpine
WORKDIR /app

# Install dependencies
COPY package.json package-lock.json ./
RUN npm install

# Copy source code
COPY . .

# Expose port
EXPOSE 3000

# Set development mode
ENV NODE_ENV=development
ENV VITE_HOST=0.0.0.0
ENV VITE_PORT=3000

# Start Vite dev server
CMD ["npm", "run", "dev"]

# Production stage
FROM node:18-alpine
WORKDIR /app
COPY --from=build /app/dist ./dist
RUN npm install -g serve
EXPOSE 3000
CMD ["serve", "-s", "dist", "-l", "3000"]
