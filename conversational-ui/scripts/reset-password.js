#!/usr/bin/env node

const { genSaltSync, hashSync } = require('bcrypt-ts');
const postgres = require('postgres');

// Get the email from command line arguments and trim any whitespace
const email = (process.argv[2] || '').trim();

if (!email) {
  console.error('Error: Email address is required');
  console.error('Usage: node reset-password.js user@example.com');
  process.exit(1);
}

console.log('Email:', `"${email}"`); // Added quotes to clearly see the value

// Get database URL from environment or use a default for local development
const dbUrl = process.env.DB_URL || process.env.POSTGRES_URL;

if (!dbUrl) {
  console.error('Error: Database URL not provided');
  console.error('Please set the DB_URL or POSTGRES_URL environment variable');
  process.exit(1);
}

// Generate a secure random password
function generateSecurePassword(length = 12) {
  // Define character sets
  const uppercaseChars = 'ABCDEFGHJKLMNPQRSTUVWXYZ';
  const lowercaseChars = 'abcdefghijkmnopqrstuvwxyz';
  const numberChars = '23456789';
  const specialChars = '!@#$%^&*-_=+';

  const allChars = uppercaseChars + lowercaseChars + numberChars + specialChars;

  // Ensure we have at least one of each type
  let password =
    uppercaseChars.charAt(Math.floor(Math.random() * uppercaseChars.length)) +
    lowercaseChars.charAt(Math.floor(Math.random() * lowercaseChars.length)) +
    numberChars.charAt(Math.floor(Math.random() * numberChars.length)) +
    specialChars.charAt(Math.floor(Math.random() * specialChars.length));

  // Fill the rest of the password
  for (let i = 4; i < length; i++) {
    password += allChars.charAt(Math.floor(Math.random() * allChars.length));
  }

  // Shuffle the password characters
  return password
    .split('')
    .sort(() => 0.5 - Math.random())
    .join('');
}

async function resetPassword() {
  let client;

  try {
    console.log('Connecting to database...');
    // Connect to the database
    client = postgres(dbUrl);

    // First, check if the user exists
    console.log('Checking if user exists...');
    const users = await client`
      SELECT id, email FROM "User" WHERE email = ${email}
    `;

    console.log(`Found ${users.length} users matching email`);

    if (users.length === 0) {
      // List a few users to help debug
      console.log('Listing some users in database for debugging:');
      const allUsers = await client`SELECT id, email FROM "User" LIMIT 5`;
      console.log(allUsers);

      throw new Error(`No user found with email "${email}"`);
    }

    // Generate a new password
    const newPassword = generateSecurePassword();

    // Hash the password
    const salt = genSaltSync(10);
    const passwordHash = hashSync(newPassword, salt);
    console.log('Email: <', email, '>');
    console.log('New password: ', newPassword);
    console.log('Hashed password: ', passwordHash);

    console.log('Updating password...');
    // Update the user's password in the database
    const result = await client`
      UPDATE "User" 
      SET password = ${passwordHash} 
      WHERE id = ${users[0].id}
      RETURNING id, email
    `;

    if (result.length === 0) {
      throw new Error(`Failed to update password for user ${email}`);
    }

    // Print success message with the new password
    console.log('\n========== PASSWORD RESET SUCCESSFUL ==========');
    console.log(`User: ${result[0].email}`);
    console.log(`New password: ${newPassword}`);
    console.log('==============================================');
    console.log('\nPlease share this password with the user securely.');
    console.log('Advise them to change it immediately after logging in.\n');
  } catch (error) {
    console.error('Error:', error.message);
    process.exit(1);
  } finally {
    // Close the database connection
    if (client) {
      console.log('Closing database connection...');
      await client.end();
    }
  }
}

// Run the password reset function
resetPassword();
