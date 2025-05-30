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

export interface LoginActionState {
  status: LoginStatus;
  error?: string;
}

export interface RegisterActionState {
  status: RegisterStatus;
  error?: string;
} 