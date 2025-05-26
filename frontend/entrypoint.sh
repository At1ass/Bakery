#!/bin/sh

# Replace environment variables in the environment.js file
envsubst < /usr/share/nginx/html/assets/environment.js.template > /usr/share/nginx/html/assets/environment.js

# Check if health endpoint script exists, create if not
if [ ! -f /usr/share/nginx/html/health ]; then
  echo "OK" > /usr/share/nginx/html/health
fi

# Start nginx
exec nginx -g "daemon off;" 