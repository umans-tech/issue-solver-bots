#!/bin/sh
set -e

# Run database migrations if DB_MIGRATE is set to true
if [ "$DB_MIGRATE" = "true" ]; then
  echo "Running database migrations..."
  node -r tsx lib/db/migrate.ts
fi

# Start the Next.js application
echo "Starting Next.js application..."
exec node server.js