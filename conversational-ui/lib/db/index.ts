import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import * as schema from './schema';

// Get the database URL from environment variables
const databaseUrl = process.env.POSTGRES_URL;

if (!databaseUrl) {
  throw new Error('POSTGRES_URL environment variable is not set');
}

// Create the connection
const client = postgres(databaseUrl);

// Create the database instance
export const db = drizzle(client, { schema });
