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

// Umans logo SVG - embedded for email compatibility
const umansLogoSvg = `<svg width="120" height="39" viewBox="0 0 505 164" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M215 41.7C220.6 41.7 225.55 42.95 229.85 45.45C234.25 47.85 237.7 51.3 240.2 55.8C242.7 60.2 243.95 65.3 243.95 71.1V126H226.7V75.15C226.7 71.45 226.05 68.25 224.75 65.55C223.45 62.85 221.55 60.75 219.05 59.25C216.55 57.75 213.65 57 210.35 57C205.95 57 202.15 58.3 198.95 60.9C195.75 63.5 193.25 67.3 191.45 72.3C189.75 77.3 188.9 83.15 188.9 89.85V126H171.65V75.15C171.65 71.45 171 68.25 169.7 65.55C168.4 62.85 166.5 60.75 164 59.25C161.6 57.75 158.75 57 155.45 57C151.05 57 147.25 58.3 144.05 60.9C140.85 63.5 138.35 67.3 136.55 72.3C134.85 77.2 134 83.05 134 89.85V126H116.75V42.9H134V55.35C136.3 51.55 139.8 48.35 144.5 45.75C149.2 43.05 154.3 41.7 159.8 41.7C164 41.7 167.8 42.35 171.2 43.65C174.6 44.95 177.55 46.9 180.05 49.5C182.55 52 184.5 55.05 185.9 58.65C189.1 53.25 193.25 49.1 198.35 46.2C203.55 43.2 209.1 41.7 215 41.7ZM286.202 127.2C280.302 127.2 275.202 126.25 270.902 124.35C266.602 122.35 263.252 119.6 260.852 116.1C258.552 112.5 257.402 108.3 257.402 103.5C257.402 98.3 258.652 93.85 261.152 90.15C263.652 86.35 267.502 83.3 272.702 81C277.902 78.7 284.502 77.1 292.502 76.2L314.402 73.8V86.85L292.802 89.25C288.802 89.65 285.452 90.5 282.752 91.8C280.052 93 278.002 94.55 276.602 96.45C275.302 98.25 274.652 100.4 274.652 102.9C274.652 106 275.902 108.55 278.402 110.55C281.002 112.55 284.302 113.55 288.302 113.55C293.102 113.55 297.302 112.55 300.902 110.55C304.602 108.45 307.452 105.45 309.452 101.55C311.452 97.65 312.452 93 312.452 87.6V71.7C312.452 68.4 311.652 65.55 310.052 63.15C308.452 60.65 306.252 58.75 303.452 57.45C300.752 56.15 297.552 55.5 293.852 55.5C290.252 55.5 287.002 56.15 284.102 57.45C281.302 58.65 279.052 60.5 277.352 63C275.752 65.4 274.752 68.25 274.352 71.55H257.552C258.252 65.85 260.252 60.75 263.552 56.25C266.852 51.75 271.102 48.2 276.302 45.6C281.502 43 287.402 41.7 294.002 41.7C300.902 41.7 307.002 43 312.302 45.6C317.702 48.1 321.902 51.75 324.902 56.55C328.002 61.35 329.552 67.05 329.552 73.65V126H312.452V113.7C310.552 117.7 307.202 120.95 302.402 123.45C297.602 125.95 292.202 127.2 286.202 127.2ZM346.514 42.9H363.764V55.5C366.364 51.5 370.164 48.2 375.164 45.6C380.264 43 385.714 41.7 391.514 41.7C397.314 41.7 402.564 42.95 407.264 45.45C412.064 47.85 415.814 51.3 418.514 55.8C421.214 60.2 422.564 65.3 422.564 71.1V126H405.314V75.3C405.314 71.7 404.564 68.5 403.064 65.7C401.664 62.9 399.614 60.75 396.914 59.25C394.214 57.75 391.114 57 387.614 57C382.914 57 378.764 58.2 375.164 60.6C371.564 63 368.764 66.6 366.764 71.4C364.764 76.2 363.764 81.95 363.764 88.65V126H346.514V42.9ZM468.589 127.2C462.089 127.2 456.339 126.05 451.339 123.75C446.339 121.35 442.339 118.05 439.339 113.85C436.439 109.55 434.839 104.6 434.539 99H451.339C451.639 103.5 453.289 107 456.289 109.5C459.389 111.9 463.489 113.1 468.589 113.1C473.089 113.1 476.639 112.1 479.239 110.1C481.839 108.1 483.139 105.35 483.139 101.85C483.139 99.45 482.339 97.5 480.739 96C479.139 94.4 477.089 93.2 474.589 92.4C472.189 91.5 468.839 90.45 464.539 89.25C458.639 87.75 453.839 86.25 450.139 84.75C446.539 83.25 443.389 80.95 440.689 77.85C438.089 74.65 436.789 70.35 436.789 64.95C436.789 60.55 437.989 56.6 440.389 53.1C442.789 49.5 446.189 46.7 450.589 44.7C455.089 42.7 460.139 41.7 465.739 41.7C472.039 41.7 477.539 42.7 482.239 44.7C486.939 46.7 490.639 49.65 493.339 53.55C496.039 57.35 497.639 61.85 498.139 67.05H481.489C480.889 63.35 479.239 60.5 476.539 58.5C473.839 56.4 470.289 55.35 465.889 55.35C462.089 55.35 459.039 56.15 456.739 57.75C454.439 59.35 453.289 61.55 453.289 64.35C453.289 66.45 454.039 68.15 455.539 69.45C457.039 70.75 458.889 71.8 461.089 72.6C463.289 73.3 466.439 74.2 470.539 75.3C476.739 76.7 481.739 78.2 485.539 79.8C489.439 81.3 492.789 83.8 495.589 87.3C498.489 90.7 499.939 95.4 499.939 101.4C499.939 106.6 498.589 111.15 495.889 115.05C493.289 118.85 489.589 121.85 484.789 124.05C480.089 126.15 474.689 127.2 468.589 127.2Z" fill="#1a1a1a"/>
<path d="M0 127C0 126.448 0.447715 126 1 126H19V163C19 163.552 18.5523 164 18 164H1C0.447715 164 0 163.552 0 163V127Z" fill="#FA75AA"/>
<path d="M78 126H96C96.5523 126 97 126.448 97 127V163C97 163.552 96.5523 164 96 164H79C78.4477 164 78 163.552 78 163V126Z" fill="#FA75AA"/>
<path d="M18.9268 108.694C18.9268 108.034 19.7126 107.5 20.3456 107.5H76.3678C77.0008 107.5 78.0732 108.047 78.0732 108.707V126C77.6789 126 77.8739 126 77.2409 126H18.9268C18.9268 125.5 19.3211 126 18.9268 126V108.694Z" fill="#1a1a1a"/>
<path d="M0 90.1935C0 89.5344 0.513186 89 1.14623 89H18.1965C18.8295 89 19 89.3408 19 90L18.9268 106.293C18.9268 106.953 18.8295 107.5 18.1965 107.5H1.14623C0.513186 107.5 0 106.966 0 106.306V90.1935Z" fill="#1a1a1a"/>
<path d="M78 90C78 89.3408 78.1705 89 78.8036 89H95.8538C96.4868 89 97 89.5344 97 90.1935V106.306C97 106.966 96.4868 107.5 95.8538 107.5H78.8036C78.1705 107.5 78.0732 106.908 78.0732 106.249L78 90Z" fill="#1a1a1a"/>
<path d="M18.9268 109.109C18.9268 107.676 18.1382 107.5 16.692 107.5L17.3368 106.232C17.886 105.411 18.9268 103.88 18.9268 105.087C18.9268 106.696 19.7154 107.5 21.2053 107.5L20.8471 108.246L20.2024 109.141L18.9268 109.109Z" fill="#1a1a1a"/>
<path d="M78.0732 109.511C78.0732 107.902 78.8036 107.5 80.2363 107.5L79.5609 106.249C78.9855 105.394 78.0662 103.685 78.0732 105.087C78.0803 106.524 77.2846 107.5 75.5798 107.5L75.8834 108.346L76.5588 109.278L78.0732 109.511Z" fill="#1a1a1a"/>
<path d="M0 44C0 43.4477 0.447715 43 1 43H18C18.5523 43 19 43.4477 19 44V92H0V44Z" fill="#1a1a1a"/>
<path d="M78 44C78 43.4477 78.4477 43 79 43H96C96.5523 43 97 43.4477 97 44V92H78V44Z" fill="#1a1a1a"/>
</svg>`;

// Modern email template with consistent branding
const createEmailTemplate = (title: string, content: string, showLogo: boolean = true) => `
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
                    ${showLogo ? `
                    <!-- Header with Logo -->
                    <tr>
                        <td align="center" style="padding: 48px 40px 32px 40px; background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);">
                            ${umansLogoSvg}
                        </td>
                    </tr>
                    ` : ''}
                    
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
const createButton = (href: string, text: string, style: 'primary' | 'secondary' | 'success' | 'google' = 'primary') => {
  const styles = {
    primary: 'background-color: #1a1a1a; color: #ffffff;',
    secondary: 'background-color: #f1f5f9; color: #1a1a1a; border: 1px solid #e2e8f0;',
    success: 'background-color: #10b981; color: #ffffff;',
    google: 'background-color: #4285f4; color: #ffffff;'
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
const createInfoBox = (content: string, variant: 'info' | 'warning' | 'success' = 'info') => {
  const styles = {
    info: 'background-color: #eff6ff; border-left: 4px solid #3b82f6; color: #1e40af;',
    warning: 'background-color: #fefce8; border-left: 4px solid #eab308; color: #a16207;',
    success: 'background-color: #f0fdf4; border-left: 4px solid #22c55e; color: #166534;'
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
      html: createEmailTemplate('You\'ve been invited to a space! 🚀', content),
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