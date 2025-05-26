#!/bin/sh

# Create template from existing environment.js if template doesn't exist
if [ ! -f /usr/share/nginx/html/assets/environment.js.template ]; then
  cp /usr/share/nginx/html/assets/environment.js /usr/share/nginx/html/assets/environment.js.template
fi

# Replace environment variables in the environment.js file
envsubst < /usr/share/nginx/html/assets/environment.js.template > /usr/share/nginx/html/assets/environment.js

# Check if health endpoint script exists, create if not
if [ ! -f /usr/share/nginx/html/health ]; then
  echo "OK" > /usr/share/nginx/html/health
fi

# Start nginx
exec nginx -g "daemon off;" 