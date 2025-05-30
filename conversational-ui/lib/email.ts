import { Resend } from 'resend';
import { getUser } from '@/lib/db/queries';

if (!process.env.EMAIL_API_KEY) {
  throw new Error('EMAIL_API_KEY environment variable is required');
}

if (!process.env.EMAIL_FROM) {
  throw new Error('EMAIL_FROM environment variable is required');
}

const resend = new Resend(process.env.EMAIL_API_KEY);

export async function sendVerificationEmail(
  to: string,
  verificationToken: string,
): Promise<void> {
  const verificationUrl = `${process.env.NEXTAUTH_URL || 'http://localhost:3000'}/verify-email?token=${verificationToken}`;
  
  try {
    await resend.emails.send({
      from: process.env.EMAIL_FROM!,
      to,
      subject: 'Verify your email address',
      html: `
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif;">
          <h1 style="color: #333; text-align: center; margin-bottom: 30px;">
            Verify Your Email Address
          </h1>
          
          <p style="color: #666; font-size: 16px; line-height: 1.5; margin-bottom: 25px;">
            Thank you for signing up! Please click the button below to verify your email address and complete your account setup.
          </p>
          
          <div style="text-align: center; margin: 30px 0;">
            <a 
              href="${verificationUrl}" 
              style="background-color: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;"
            >
              Verify Email Address
            </a>
          </div>
          
          <p style="color: #888; font-size: 14px; line-height: 1.5; margin-top: 30px;">
            If the button doesn't work, you can copy and paste this link into your browser:
            <br>
            <a href="${verificationUrl}" style="color: #007bff; word-break: break-all;">
              ${verificationUrl}
            </a>
          </p>
          
          <p style="color: #888; font-size: 14px; margin-top: 30px;">
            This verification link will expire in 24 hours. If you didn't request this email, you can safely ignore it.
          </p>
        </div>
      `,
    });
  } catch (error) {
    console.error('Failed to send verification email:', error);
    throw new Error('Failed to send verification email');
  }
}

export async function sendWelcomeEmail(to: string): Promise<void> {
  try {
    await resend.emails.send({
      from: process.env.EMAIL_FROM!,
      to,
      subject: 'Welcome to Umans!',
      html: `
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif;">
          <h1 style="color: #333; text-align: center; margin-bottom: 30px;">
            Welcome to Umans! 🎉
          </h1>
          
          <p style="color: #666; font-size: 16px; line-height: 1.5; margin-bottom: 25px;">
            Your email has been successfully verified! You can now enjoy all the features of Umans.
          </p>
          
          <div style="text-align: center; margin: 30px 0;">
            <a 
              href="${process.env.NEXTAUTH_URL || 'http://localhost:3000'}" 
              style="background-color: #28a745; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;"
            >
              Get Started
            </a>
          </div>
          
          <p style="color: #666; font-size: 16px; line-height: 1.5;">
            If you have any questions or need assistance, feel free to reach out to our support team.
          </p>
        </div>
      `,
    });
  } catch (error) {
    console.error('Failed to send welcome email:', error);
    // Don't throw here as this is not critical for the verification flow
  }
}

export async function sendPasswordResetEmail(
  to: string,
  resetToken: string,
): Promise<void> {
  try {
    // Check if user exists and if they're a Gmail user
    const [user] = await getUser(to);
    
    if (!user) {
      // Don't send email if user doesn't exist (security)
      return;
    }

    // If user has no password (OAuth user), send different email
    if (!user.password) {
      await resend.emails.send({
        from: process.env.EMAIL_FROM!,
        to,
        subject: 'Sign in with Google',
        html: `
          <div style="max-width: 600px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif;">
            <h1 style="color: #333; text-align: center; margin-bottom: 30px;">
              Sign in with Google
            </h1>
            
            <p style="color: #666; font-size: 16px; line-height: 1.5; margin-bottom: 25px;">
              Your account is linked to Google. You don't need to reset a password - just sign in using Google.
            </p>
            
            <div style="text-align: center; margin: 30px 0;">
              <a 
                href="${process.env.NEXTAUTH_URL || 'http://localhost:3000'}/login" 
                style="background-color: #4285F4; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;"
              >
                Sign in with Google
              </a>
            </div>
            
            <p style="color: #888; font-size: 14px; margin-top: 30px;">
              If you didn't request this email, you can safely ignore it.
            </p>
          </div>
        `,
      });
      return;
    }

    // Regular password reset email for credential users
    const resetUrl = `${process.env.NEXTAUTH_URL || 'http://localhost:3000'}/reset-password?token=${resetToken}`;
    
    await resend.emails.send({
      from: process.env.EMAIL_FROM!,
      to,
      subject: 'Reset your password',
      html: `
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif;">
          <h1 style="color: #333; text-align: center; margin-bottom: 30px;">
            Reset Your Password
          </h1>
          
          <p style="color: #666; font-size: 16px; line-height: 1.5; margin-bottom: 25px;">
            You requested a password reset. Click the button below to set a new password for your account.
          </p>
          
          <div style="text-align: center; margin: 30px 0;">
            <a 
              href="${resetUrl}" 
              style="background-color: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;"
            >
              Reset Password
            </a>
          </div>
          
          <p style="color: #888; font-size: 14px; line-height: 1.5; margin-top: 30px;">
            If the button doesn't work, you can copy and paste this link into your browser:
            <br>
            <a href="${resetUrl}" style="color: #007bff; word-break: break-all;">
              ${resetUrl}
            </a>
          </p>
          
          <p style="color: #888; font-size: 14px; margin-top: 30px;">
            This reset link will expire in 24 hours. If you didn't request this email, you can safely ignore it.
          </p>
        </div>
      `,
    });
  } catch (error) {
    console.error('Failed to send password reset email:', error);
    throw new Error('Failed to send password reset email');
  }
} 