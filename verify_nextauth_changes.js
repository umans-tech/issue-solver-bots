// Script to validate NextAuth.js configuration
const fs = require('fs');
const path = require('path');

console.log('Verifying NextAuth.js implementation...');

// Check for ADR file
const adrPath = path.join(__dirname, 'docs', 'adr_001_nextauth_authentication.md');
if (fs.existsSync(adrPath)) {
  console.log('✅ ADR file exists at:', adrPath);
  
  // Read ADR content to verify it follows Nygard's template
  const adrContent = fs.readFileSync(adrPath, 'utf8');
  const requiredSections = ['Status', 'Context', 'Decision', 'Consequences'];
  
  let allSectionsPresent = true;
  for (const section of requiredSections) {
    if (!adrContent.includes(`## ${section}`)) {
      console.error(`❌ ADR is missing the required "${section}" section`);
      allSectionsPresent = false;
    }
  }
  
  if (allSectionsPresent) {
    console.log('✅ ADR follows the Nygard template with all required sections');
  }
  
  // Check for social providers and email verification in ADR content
  if (adrContent.includes('social provider') && adrContent.includes('email verification')) {
    console.log('✅ ADR documents the decision to use social providers and email verification');
  } else {
    console.error('❌ ADR is missing documentation about social providers or email verification');
  }
} else {
  console.error('❌ ADR file not found at:', adrPath);
}

// Check NextAuth.js implementation
const authPath = path.join(__dirname, 'conversational-ui', 'app', '(auth)', 'auth.ts');
if (fs.existsSync(authPath)) {
  console.log('✅ NextAuth.js implementation file exists at:', authPath);
  
  // Read auth.ts to verify it has necessary providers
  const authContent = fs.readFileSync(authPath, 'utf8');
  
  if (authContent.includes('GoogleProvider') && 
      authContent.includes('GitHubProvider') && 
      authContent.includes('EmailProvider')) {
    console.log('✅ Social providers and email verification are implemented');
  } else {
    console.error('❌ Missing one or more required providers (Google, GitHub, or Email)');
  }
} else {
  console.error('❌ NextAuth.js implementation file not found at:', authPath);
}

// Check TypeScript declarations
const typesPath = path.join(__dirname, 'conversational-ui', 'types', 'next-auth.d.ts');
if (fs.existsSync(typesPath)) {
  console.log('✅ NextAuth.js TypeScript declarations file exists at:', typesPath);
  
  // Read next-auth.d.ts to verify it has necessary type extensions
  const typesContent = fs.readFileSync(typesPath, 'utf8');
  
  if (typesContent.includes('provider?') && typesContent.includes('emailVerified?')) {
    console.log('✅ Type declarations support social providers and email verification');
  } else {
    console.error('❌ Type declarations are missing provider or emailVerified fields');
  }
} else {
  console.error('❌ NextAuth.js TypeScript declarations file not found at:', typesPath);
}

console.log('\nVerification complete!');