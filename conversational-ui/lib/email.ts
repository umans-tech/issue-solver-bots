import { Resend } from 'resend';
import { getUser } from '@/lib/db/queries';

if (!process.env.EMAIL_API_KEY) {
  throw new Error('EMAIL_API_KEY environment variable is required');
}

if (!process.env.EMAIL_FROM) {
  throw new Error('EMAIL_FROM environment variable is required');
}

const resend = new Resend(process.env.EMAIL_API_KEY);

// Common email template wrapper
const emailTemplate = (title: string, content: string) => `
  <div style="max-width: 600px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif;">
    <h1 style="color: #333; text-align: center; margin-bottom: 30px;">
      ${title}
    </h1>
    ${content}
  </div>
`;

// Common button component
const emailButton = (href: string, text: string, color: string = '#007bff') => `
  <div style="text-align: center; margin: 30px 0;">
    <a 
      href="${href}" 
      style="background-color: ${color}; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;"
    >
      ${text}
    </a>
  </div>
`;

export async function sendVerificationEmail(
  to: string,
  verificationToken: string,
): Promise<void> {
  const verificationUrl = `${process.env.NEXTAUTH_URL || 'http://localhost:3000'}/verify-email?token=${verificationToken}`;
  
  const content = `
    <p style="color: #666; font-size: 16px; line-height: 1.5; margin-bottom: 25px;">
      Thank you for signing up! Please click the button below to verify your email address and complete your account setup.
    </p>
    
    ${emailButton(verificationUrl, 'Verify Email Address')}
    
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
  `;
  
  try {
    await resend.emails.send({
      from: process.env.EMAIL_FROM!,
      to,
      subject: 'Verify your email address',
      html: emailTemplate('Verify Your Email Address', content),
    });
  } catch (error) {
    console.error('Failed to send verification email:', error);
    throw new Error('Failed to send verification email');
  }
}

export async function sendWelcomeEmail(to: string): Promise<void> {
  const content = `
    <p style="color: #666; font-size: 16px; line-height: 1.5; margin-bottom: 25px;">
      Your email has been successfully verified! You can now enjoy all the features of Umans.
    </p>
    
    ${emailButton(process.env.NEXTAUTH_URL || 'http://localhost:3000', 'Get Started', '#28a745')}
    
    <p style="color: #666; font-size: 16px; line-height: 1.5;">
      If you have any questions or need assistance, feel free to reach out to our support team.
    </p>
  `;
  
  try {
    await resend.emails.send({
      from: process.env.EMAIL_FROM!,
      to,
      subject: 'Welcome to Umans!',
      html: emailTemplate('Welcome to Umans! 🎉', content),
    });
  } catch (error) {
    console.error('Failed to send welcome email:', error);
    // Don't throw here as this is not critical for the verification flow
  }
}

export async function sendSpaceInviteNotificationEmail(
  to: string,
  spaceName: string,
  inviterEmail: string,
): Promise<void> {
  const content = `
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 25px; border-left: 4px solid #007bff;">
      <h2 style="color: #333; margin: 0 0 15px 0; font-size: 18px;">Space: ${spaceName}</h2>
      <p style="color: #666; margin: 0; font-size: 16px;">
        <strong>${inviterEmail}</strong> has added you to their space.
      </p>
    </div>
    
    <p style="color: #666; font-size: 16px; line-height: 1.5; margin-bottom: 25px;">
      You now have access to collaborate in this space. Sign in to start exploring and working together!
    </p>
    
    ${emailButton(process.env.NEXTAUTH_URL || 'http://localhost:3000', 'Access Your Space')}
    
    <p style="color: #888; font-size: 14px; line-height: 1.5; margin-top: 30px;">
      If you have any questions about this space or need help getting started, feel free to reach out to your team or our support.
    </p>
    
    <p style="color: #888; font-size: 14px; margin-top: 15px;">
      This email was sent because ${inviterEmail} added you to the "${spaceName}" space on Umans.
    </p>
  `;
  
  try {
    await resend.emails.send({
      from: process.env.EMAIL_FROM!,
      to,
      subject: `You've been added to the "${spaceName}" space`,
      html: emailTemplate("You've been added to a new space! 🚀", content),
    });
  } catch (error) {
    console.error('Failed to send space invite notification email:', error);
    throw new Error('Failed to send space invite notification email');
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