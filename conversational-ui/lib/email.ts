import { Resend } from 'resend';
import { getUser } from '@/lib/db/queries';

if (!process.env.EMAIL_API_KEY) {
  throw new Error('EMAIL_API_KEY environment variable is required');
}

if (!process.env.EMAIL_FROM) {
  throw new Error('EMAIL_FROM environment variable is required');
}

const resend = new Resend(process.env.EMAIL_API_KEY);

// Base URL for assets
const getBaseUrl = () => process.env.NEXTAUTH_URL || 'http://localhost:3000';

// Logo URL - use PNG for email compatibility (SVG isn't supported in most email clients)
const getLogoUrl = () => `${getBaseUrl()}/images/umans-logo.png`;

// Email logo using the hosted PNG file
const getEmailLogo = () => {
  return `<img src="${getLogoUrl()}" alt="Umans" width="120" height="39" style="display: block; width: 120px; height: 39px; max-width: 120px; border: none;">`;
};

// Modern email template with consistent branding
const createEmailTemplate = (
  title: string,
  content: string,
  showLogo = true,
) => `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${title}</title>
    <!--[if mso]>
    <noscript>
        <xml>
            <o:OfficeDocumentSettings>
                <o:PixelsPerInch>96</o:PixelsPerInch>
            </o:OfficeDocumentSettings>
        </xml>
    </noscript>
    <![endif]-->
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f8fafc;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); overflow: hidden;">
                    ${
                      showLogo
                        ? `
                    <!-- Header with Logo -->
                    <tr>
                        <td align="center" style="padding: 48px 40px 32px 40px; background: linear-gradient(135deg, #1a1a1a 0%, #374151 100%);">
                            ${getEmailLogo()}
                        </td>
                    </tr>
                    `
                        : ''
                    }
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: ${showLogo ? '32px 40px 48px 40px' : '48px 40px'};">
                            <h1 style="margin: 0 0 24px 0; font-size: 24px; line-height: 1.3; font-weight: 600; color: #1a1a1a; text-align: center;">
                                ${title}
                            </h1>
                            ${content}
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 32px 40px; background-color: #f8fafc; border-top: 1px solid #e2e8f0;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td align="center">
                                        <p style="margin: 0 0 8px 0; font-size: 14px; color: #64748b; line-height: 1.5;">
                                            © ${new Date().getFullYear()} Umans. All rights reserved.
                                        </p>
                                        <p style="margin: 0; font-size: 12px; color: #94a3b8; line-height: 1.4;">
                                            This email was sent from a trusted Umans account.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
`;

// Modern button component
const createButton = (
  href: string,
  text: string,
  style: 'primary' | 'secondary' | 'success' | 'google' = 'primary',
) => {
  const styles = {
    primary: 'background-color: #1a1a1a; color: #ffffff;',
    secondary:
      'background-color: #f1f5f9; color: #1a1a1a; border: 1px solid #e2e8f0;',
    success: 'background-color: #10b981; color: #ffffff;',
    google: 'background-color: #4285f4; color: #ffffff;',
  };

  return `
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
        <tr>
            <td align="center" style="padding: 24px 0;">
                <a href="${href}" style="display: inline-block; ${styles[style]} padding: 16px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; line-height: 1.4; transition: all 0.2s ease;">
                    ${text}
                </a>
            </td>
        </tr>
    </table>
  `;
};

// Utility for creating info boxes
const createInfoBox = (
  content: string,
  variant: 'info' | 'warning' | 'success' = 'info',
) => {
  const styles = {
    info: 'background-color: #eff6ff; border-left: 4px solid #3b82f6; color: #1e40af;',
    warning:
      'background-color: #fefce8; border-left: 4px solid #eab308; color: #a16207;',
    success:
      'background-color: #f0fdf4; border-left: 4px solid #22c55e; color: #166534;',
  };

  return `
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
        <tr>
            <td style="padding: 20px; border-radius: 8px; margin: 24px 0; ${styles[variant]}">
                ${content}
            </td>
        </tr>
    </table>
  `;
};

export async function sendVerificationEmail(
  to: string,
  verificationToken: string,
): Promise<void> {
  const verificationUrl = `${getBaseUrl()}/verify-email?token=${verificationToken}`;

  const content = `
    <p style="margin: 0 0 24px 0; font-size: 16px; line-height: 1.6; color: #475569; text-align: center;">
      Welcome to Umans! To complete your account setup and start collaborating, please verify your email address.
    </p>
    
    ${createButton(verificationUrl, 'Verify Email Address', 'primary')}
    
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
        <tr>
            <td style="padding: 24px 0 0 0;">
                <p style="margin: 0 0 12px 0; font-size: 14px; color: #64748b; text-align: center;">
                    If the button doesn't work, copy and paste this link:
                </p>
                <p style="margin: 0; font-size: 14px; text-align: center;">
                    <a href="${verificationUrl}" style="color: #3b82f6; text-decoration: none; word-break: break-all;">
                        ${verificationUrl}
                    </a>
                </p>
            </td>
        </tr>
    </table>
    
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
        <tr>
            <td style="padding: 32px 0 0 0;">
                <p style="margin: 0; font-size: 14px; color: #94a3b8; text-align: center; line-height: 1.5;">
                    This verification link expires in 24 hours. If you didn't create this account, you can safely ignore this email.
                </p>
            </td>
        </tr>
    </table>
  `;

  try {
    await resend.emails.send({
      from: process.env.EMAIL_FROM!,
      to,
      subject: 'Verify your email address',
      html: createEmailTemplate('Verify Your Email Address', content),
    });
  } catch (error) {
    console.error('Failed to send verification email:', error);
    throw new Error('Failed to send verification email');
  }
}

export async function sendWelcomeEmail(to: string): Promise<void> {
  const content = `
    <p style="margin: 0 0 24px 0; font-size: 16px; line-height: 1.6; color: #475569; text-align: center;">
      🎉 Your email has been successfully verified! Welcome to Umans - your new collaborative workspace.
    </p>
    
    ${createButton(getBaseUrl(), 'Start Exploring', 'success')}
    
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
        <tr>
            <td style="padding: 24px 0 0 0;">
                <p style="margin: 0; font-size: 16px; color: #475569; text-align: center; line-height: 1.5;">
                  Need help getting started? Our support team is here to assist you every step of the way.
                </p>
            </td>
        </tr>
    </table>
  `;

  try {
    await resend.emails.send({
      from: process.env.EMAIL_FROM!,
      to,
      subject: 'Welcome to Umans! 🎉',
      html: createEmailTemplate('Welcome to Umans!', content),
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
  const spaceInfo = `
    <h3 style="margin: 0 0 8px 0; font-size: 18px; font-weight: 600; color: #1a1a1a;">
      ${spaceName}
    </h3>
    <p style="margin: 0; font-size: 16px; color: #475569;">
      <strong>${inviterEmail}</strong> has invited you to collaborate in this space.
    </p>
  `;

  const content = `
    ${createInfoBox(spaceInfo, 'info')}
    
    <p style="margin: 24px 0; font-size: 16px; line-height: 1.6; color: #475569; text-align: center;">
      You now have access to collaborate in this space. Sign in to start exploring and working together with your team!
    </p>
    
    ${createButton(getBaseUrl(), 'Access Your Space', 'primary')}
    
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
        <tr>
            <td style="padding: 24px 0 0 0;">
                <p style="margin: 0 0 12px 0; font-size: 14px; color: #64748b; text-align: center; line-height: 1.5;">
                  Questions about this space? Reach out to ${inviterEmail} or our support team.
                </p>
                <p style="margin: 0; font-size: 12px; color: #94a3b8; text-align: center;">
                  You received this email because ${inviterEmail} added you to "${spaceName}" on Umans.
                </p>
            </td>
        </tr>
    </table>
  `;

  try {
    await resend.emails.send({
      from: process.env.EMAIL_FROM!,
      to,
      subject: `You've been invited to "${spaceName}" space`,
      html: createEmailTemplate("You've been invited to a space! 🚀", content),
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
      const content = `
        <p style="margin: 0 0 24px 0; font-size: 16px; line-height: 1.6; color: #475569; text-align: center;">
          Your account is connected to Google. No password reset needed - just sign in using your Google account.
        </p>
        
        ${createButton(`${getBaseUrl()}/login`, 'Sign in with Google', 'google')}
        
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
            <tr>
                <td style="padding: 24px 0 0 0;">
                    <p style="margin: 0; font-size: 14px; color: #94a3b8; text-align: center;">
                      If you didn't request this email, you can safely ignore it.
                    </p>
                </td>
            </tr>
        </table>
      `;

      await resend.emails.send({
        from: process.env.EMAIL_FROM!,
        to,
        subject: 'Sign in with Google',
        html: createEmailTemplate('Sign in with Google', content),
      });
      return;
    }

    // Regular password reset email for credential users
    const resetUrl = `${getBaseUrl()}/reset-password?token=${resetToken}`;

    const content = `
      <p style="margin: 0 0 24px 0; font-size: 16px; line-height: 1.6; color: #475569; text-align: center;">
        We received a request to reset your password. Click the button below to create a new password for your account.
      </p>
      
      ${createButton(resetUrl, 'Reset Password', 'primary')}
      
      <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
          <tr>
              <td style="padding: 24px 0 0 0;">
                  <p style="margin: 0 0 12px 0; font-size: 14px; color: #64748b; text-align: center;">
                      If the button doesn't work, copy and paste this link:
                  </p>
                  <p style="margin: 0; font-size: 14px; text-align: center;">
                      <a href="${resetUrl}" style="color: #3b82f6; text-decoration: none; word-break: break-all;">
                          ${resetUrl}
                      </a>
                  </p>
              </td>
          </tr>
      </table>
      
      <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
          <tr>
              <td style="padding: 32px 0 0 0;">
                  <p style="margin: 0; font-size: 14px; color: #94a3b8; text-align: center; line-height: 1.5;">
                    This reset link expires in 24 hours. If you didn't request this password reset, you can safely ignore this email.
                  </p>
              </td>
          </tr>
      </table>
    `;

    await resend.emails.send({
      from: process.env.EMAIL_FROM!,
      to,
      subject: 'Reset your password',
      html: createEmailTemplate('Reset Your Password', content),
    });
  } catch (error) {
    console.error('Failed to send password reset email:', error);
    throw new Error('Failed to send password reset email');
  }
}
