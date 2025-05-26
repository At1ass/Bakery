# Build stage
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Add package files
COPY package*.json ./

# Install dependencies and generate package-lock.json
RUN npm install

# Add rest of the client code
COPY . .

# Build the app
RUN npm run build

# Copy the environment.js file to be used as a template
RUN cp /app/src/environment.js /app/dist/assets/environment.js

# Production stage
FROM nginx:stable-alpine

# Install envsubst for environment variable substitution
RUN apk add --no-cache gettext

# Create SSL directory
RUN mkdir -p /etc/nginx/ssl

# Copy locally generated mkcert certificates
COPY localhost+2.pem /etc/nginx/ssl/cert.pem
COPY localhost+2-key.pem /etc/nginx/ssl/key.pem

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy static files from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy entrypoint script
COPY entrypoint.sh /
RUN chmod +x /entrypoint.sh

# Expose port
EXPOSE 3001 3002

# Run entrypoint script
CMD ["/entrypoint.sh"]
