// Enums for action statuses
export enum LoginStatus {
  IDLE = 'idle',
  IN_PROGRESS = 'in_progress',
  SUCCESS = 'success',
  FAILED = 'failed',
  INVALID_DATA = 'invalid_data',
  EMAIL_NOT_VERIFIED = 'email_not_verified',
}

export enum RegisterStatus {
  IDLE = 'idle',
  IN_PROGRESS = 'in_progress',
  SUCCESS = 'success',
  FAILED = 'failed',
  INVALID_DATA = 'invalid_data',
  USER_EXISTS = 'user_exists',
  VERIFICATION_SENT = 'verification_sent',
}

// Simple addition for password reset - reuse existing patterns
export enum PasswordResetStatus {
  IDLE = 'idle',
  SUCCESS = 'success',
  FAILED = 'failed',
  INVALID_DATA = 'invalid_data',
}

// Action state types
export type LoginActionState = {
  status: LoginStatus;
  error?: string;
};

export type RegisterActionState = {
  status: RegisterStatus;
  error?: string;
};

export type PasswordResetActionState = {
  status: PasswordResetStatus;
  message?: string;
  error?: string;
}; 