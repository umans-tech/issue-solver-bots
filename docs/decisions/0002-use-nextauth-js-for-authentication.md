# 2. Use NextAuth.js (Auth.js) for Authentication with Social Providers and Email Verification

Date: 2025-05-27

## Status

Accepted

## Context

Our application currently uses NextAuth.js with a Credentials provider for email/password authentication. We need to add
social authentication (Google now, Microsoft later) and implement email validation and password reset functionality. We
considered several authentication solutions:

1. **NextAuth.js (Auth.js)** - Our current solution, an open-source authentication library for Next.js
2. **Clerk** - A comprehensive managed authentication service with pre-built UI components
3. **AWS Cognito** - Amazon's managed authentication service with enterprise-grade security features

Key factors in our decision:

- Minimizing changes to the existing codebase
- Implementation complexity and development time
- Long-term maintenance requirements
- Cost considerations at different user scales
- Security and compliance requirements
- Support for our specific authentication needs (social auth, email verification, password reset)

## Decision

We will continue using NextAuth.js (Auth.js) and extend it to support:

1. Social authentication with Google (and later Microsoft)
2. Email verification via the NextAuth Email provider
3. Password reset functionality

## Consequences

### Positive

- **Minimal migration effort**: No need to migrate existing users to a new system
- **Cost-effective**: No additional per-user costs beyond email service expenses
- **Full control**: We maintain complete control over authentication logic and user data
- **Familiar technology**: The team is already familiar with NextAuth.js
- **Flexibility**: We can customize the authentication flow to our specific needs
- **Open source**: No vendor lock-in, community-supported solution

### Negative

- **Development overhead**: We need to implement email verification and password reset flows
- **Maintenance responsibility**: We are responsible for keeping authentication secure and up-to-date
- **Email service dependency**: We need to set up and maintain an email service integration
- **Limited built-in features**: Advanced features like multi-factor authentication will require custom implementation

### Neutral

- **Database schema changes**: Minor changes may be needed to support verification tokens
- **Email template management**: We'll need to create and maintain email templates for verification and password reset

## Implementation Details

### 1. Social Authentication

- Add Google OAuth provider to NextAuth configuration
- Implement user creation for first-time social logins
- Add social login buttons to the login page
- Configure environment variables for OAuth credentials

### 2. Email Verification & Password Reset

- Add Email provider to NextAuth configuration
- Set up email service integration (SMTP or API-based)
- Create email templates for verification and password reset
- Implement verification and reset UI flows
- Update database schema to store verification tokens if needed

### 3. Future Microsoft Authentication

- Add Microsoft OAuth provider to NextAuth configuration
- Add Microsoft login button to the login page
- Configure environment variables for Microsoft OAuth credentials

## Compliance & Security Considerations

- Ensure proper handling of authentication tokens
- Implement rate limiting for authentication attempts
- Follow security best practices for password storage and verification
- Maintain audit logs for authentication events
- Ensure GDPR compliance for user data handling

## Alternatives Considered

### Clerk

- **Pros**: Comprehensive solution, excellent developer experience, built-in UI components
- **Cons**: Cost at scale, migration effort, vendor lock-in
- **Rejection reason**: Higher migration effort and ongoing costs

### AWS Cognito

- **Pros**: Enterprise-grade security, AWS ecosystem integration, built-in features
- **Cons**: Complex setup, AWS-specific knowledge required, costs at higher scale
- **Rejection reason**: Unnecessary complexity for our current needs

## References

- **[Discussion leading to this decision](https://app.umans.ai/chat/180686ee-4f6b-469f-9ace-bbcf274172b4)**
- [NextAuth.js Documentation](https://next-auth.js.org/)
- [NextAuth Email Provider](https://next-auth.js.org/providers/email)
- [NextAuth OAuth Providers](https://next-auth.js.org/providers/google)
- [Auth.js v5 Documentation](https://authjs.dev/)