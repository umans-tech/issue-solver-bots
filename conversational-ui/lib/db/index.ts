import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import * as schema from './schema';

// Get the database URL from environment variables
const databaseUrl = process.env.POSTGRES_URL;

if (!databaseUrl) {
  throw new Error('POSTGRES_URL environment variable is not set');
}

// Create the connection with pool limits to prevent connection exhaustion
// See: https://github.com/porsager/postgres#connection-options
const client = postgres(databaseUrl, {
  max: 10,                    // Maximum pool size (default: 10)
  idle_timeout: 20,           // Close idle connections after 20s
  connect_timeout: 10,        // Connection timeout: 10s
  max_lifetime: 60 * 30,      // Close connections after 30 minutes
});

// Create the database instance
export const db = drizzle(client, { schema }); 