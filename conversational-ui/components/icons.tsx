import * as React from 'react';
import { useEffect } from 'react';
import { cn } from '@/lib/utils';
import {
  AlertCircle as LucideAlertCircle,
  ArrowUp,
  Box,
  ChevronDown,
  CodeXml as LucideCode,
  Copy,
  Download,
  Edit,
  Eye,
  File,
  Globe,
  Home,
  Image,
  Info,
  Loader,
  Lock,
  Maximize,
  Menu,
  MessageCircle,
  MoreHorizontal,
  MoreVertical,
  Navigation,
  PanelLeft,
  Paperclip,
  Play,
  Plus,
  Receipt,
  Redo,
  RotateCcw,
  Search,
  Share,
  Sparkles,
  Square,
  Terminal,
  ThumbsDown,
  ThumbsUp,
  Undo,
  Upload,
  X,
} from 'lucide-react';
import { IoCheckmarkCircle } from 'react-icons/io5';
import { TbTerminal2 } from 'react-icons/tb';

export const BotIcon = () => {
  return (
    <svg
      height="16"
      strokeLinejoin="round"
      viewBox="0 0 16 16"
      width="16"
      style={{ color: 'currentcolor' }}
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M8.75 2.79933C9.19835 2.53997 9.5 2.05521 9.5 1.5C9.5 0.671573 8.82843 0 8 0C7.17157 0 6.5 0.671573 6.5 1.5C6.5 2.05521 6.80165 2.53997 7.25 2.79933V5H7C4.027 5 1.55904 7.16229 1.08296 10H0V13H1V14.5V16H2.5H13.5H15V14.5V13H16V10H14.917C14.441 7.16229 11.973 5 9 5H8.75V2.79933ZM7 6.5C4.51472 6.5 2.5 8.51472 2.5 11V14.5H13.5V11C13.5 8.51472 11.4853 6.5 9 6.5H7ZM7.25 11.25C7.25 12.2165 6.4665 13 5.5 13C4.5335 13 3.75 12.2165 3.75 11.25C3.75 10.2835 4.5335 9.5 5.5 9.5C6.4665 9.5 7.25 10.2835 7.25 11.25ZM10.5 13C11.4665 13 12.25 12.2165 12.25 11.25C12.25 10.2835 11.4665 9.5 10.5 9.5C9.5335 9.5 8.75 10.2835 8.75 11.25C8.75 12.2165 9.5335 13 10.5 13Z"
        fill="currentColor"
      />
    </svg>
  );
};

export const UserIcon = ({ size = 16 }: { size?: number }) => {
  return (
    <svg
      data-testid="geist-icon"
      height={size}
      strokeLinejoin="round"
      viewBox="0 0 16 16"
      width={size}
      style={{ color: 'currentcolor' }}
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M7.75 0C5.95507 0 4.5 1.45507 4.5 3.25V3.75C4.5 5.54493 5.95507 7 7.75 7H8.25C10.0449 7 11.5 5.54493 11.5 3.75V3.25C11.5 1.45507 10.0449 0 8.25 0H7.75ZM6 3.25C6 2.2835 6.7835 1.5 7.75 1.5H8.25C9.2165 1.5 10 2.2835 10 3.25V3.75C10 4.7165 9.2165 5.5 8.25 5.5H7.75C6.7835 5.5 6 4.7165 6 3.75V3.25ZM2.5 14.5V13.1709C3.31958 11.5377 4.99308 10.5 6.82945 10.5H9.17055C11.0069 10.5 12.6804 11.5377 13.5 13.1709V14.5H2.5ZM6.82945 9C4.35483 9 2.10604 10.4388 1.06903 12.6857L1 12.8353V13V15.25V16H1.75H14.25H15V15.25V13V12.8353L14.931 12.6857C13.894 10.4388 11.6452 9 9.17055 9H6.82945Z"
        fill="currentColor"
      />
    </svg>
  );
};

export const AttachmentIcon = () => {
  return (
    <svg
      height="16"
      strokeLinejoin="round"
      viewBox="0 0 16 16"
      width="16"
      style={{ color: 'currentcolor' }}
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M14.5 6.5V13.5C14.5 14.8807 13.3807 16 12 16H4C2.61929 16 1.5 14.8807 1.5 13.5V1.5V0H3H8H9.08579C9.351 0 9.60536 0.105357 9.79289 0.292893L14.2071 4.70711C14.3946 4.89464 14.5 5.149 14.5 5.41421V6.5ZM13 6.5V13.5C13 14.0523 12.5523 14.5 12 14.5H4C3.44772 14.5 3 14.0523 3 13.5V1.5H8V5V6.5H9.5H13ZM9.5 2.12132V5H12.3787L9.5 2.12132Z"
        fill="currentColor"
      />
    </svg>
  );
};

export const VercelIcon = ({ size = 17 }) => {
  return (
    <svg
      height={size}
      strokeLinejoin="round"
      viewBox="0 0 16 16"
      width={size}
      style={{ color: 'currentcolor' }}
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M8 1L16 15H0L8 1Z"
        fill="currentColor"
      />
    </svg>
  );
};

export const IconUmansLogo = ({
  className,
  ...props
}: React.ComponentProps<'svg'>) => {
  return (
    <svg
      aria-label="Umans logomark"
      width="505"
      height="164"
      viewBox="0 0 505 164"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn('h-4 w-4', className)}
      {...props}
    >
      <path
        d="M215 41.7C220.6 41.7 225.55 42.95 229.85 45.45C234.25 47.85 237.7 51.3 240.2 55.8C242.7 60.2 243.95 65.3 243.95 71.1V126H226.7V75.15C226.7 71.45 226.05 68.25 224.75 65.55C223.45 62.85 221.55 60.75 219.05 59.25C216.55 57.75 213.65 57 210.35 57C205.95 57 202.15 58.3 198.95 60.9C195.75 63.5 193.25 67.3 191.45 72.3C189.75 77.3 188.9 83.15 188.9 89.85V126H171.65V75.15C171.65 71.45 171 68.25 169.7 65.55C168.4 62.85 166.5 60.75 164 59.25C161.6 57.75 158.75 57 155.45 57C151.05 57 147.25 58.3 144.05 60.9C140.85 63.5 138.35 67.3 136.55 72.3C134.85 77.2 134 83.05 134 89.85V126H116.75V42.9H134V55.35C136.3 51.55 139.8 48.35 144.5 45.75C149.2 43.05 154.3 41.7 159.8 41.7C164 41.7 167.8 42.35 171.2 43.65C174.6 44.95 177.55 46.9 180.05 49.5C182.55 52 184.5 55.05 185.9 58.65C189.1 53.25 193.25 49.1 198.35 46.2C203.55 43.2 209.1 41.7 215 41.7Z"
        fill="currentColor"
      />
      <path
        d="M286.202 127.2C280.302 127.2 275.202 126.25 270.902 124.35C266.602 122.35 263.252 119.6 260.852 116.1C258.552 112.5 257.402 108.3 257.402 103.5C257.402 98.3 258.652 93.85 261.152 90.15C263.652 86.35 267.502 83.3 272.702 81C277.902 78.7 284.502 77.1 292.502 76.2L314.402 73.8V86.85L292.802 89.25C288.802 89.65 285.452 90.5 282.752 91.8C280.052 93 278.002 94.55 276.602 96.45C275.302 98.25 274.652 100.4 274.652 102.9C274.652 106 275.902 108.55 278.402 110.55C281.002 112.55 284.302 113.55 288.302 113.55C293.102 113.55 297.302 112.55 300.902 110.55C304.602 108.45 307.452 105.45 309.452 101.55C311.452 97.65 312.452 93 312.452 87.6V71.7C312.452 68.4 311.652 65.55 310.052 63.15C308.452 60.65 306.252 58.75 303.452 57.45C300.752 56.15 297.552 55.5 293.852 55.5C290.252 55.5 287.002 56.15 284.102 57.45C281.302 58.65 279.052 60.5 277.352 63C275.752 65.4 274.752 68.25 274.352 71.55H257.552C258.252 65.85 260.252 60.75 263.552 56.25C266.852 51.75 271.102 48.2 276.302 45.6C281.502 43 287.402 41.7 294.002 41.7C300.902 41.7 307.002 43 312.302 45.6C317.702 48.1 321.902 51.75 324.902 56.55C328.002 61.35 329.552 67.05 329.552 73.65V126H312.452V113.7C310.552 117.7 307.202 120.95 302.402 123.45C297.602 125.95 292.202 127.2 286.202 127.2Z"
        fill="currentColor"
      />
      <path
        d="M346.514 42.9H363.764V55.5C366.364 51.5 370.164 48.2 375.164 45.6C380.264 43 385.714 41.7 391.514 41.7C397.314 41.7 402.564 42.95 407.264 45.45C412.064 47.85 415.814 51.3 418.514 55.8C421.214 60.2 422.564 65.3 422.564 71.1V126H405.314V75.3C405.314 71.7 404.564 68.5 403.064 65.7C401.664 62.9 399.614 60.75 396.914 59.25C394.214 57.75 391.114 57 387.614 57C382.914 57 378.764 58.2 375.164 60.6C371.564 63 368.764 66.6 366.764 71.4C364.764 76.2 363.764 81.95 363.764 88.65V126H346.514V42.9Z"
        fill="currentColor"
      />
      <path
        d="M468.589 127.2C462.089 127.2 456.339 126.05 451.339 123.75C446.339 121.35 442.339 118.05 439.339 113.85C436.439 109.55 434.839 104.6 434.539 99H451.339C451.639 103.5 453.289 107 456.289 109.5C459.389 111.9 463.489 113.1 468.589 113.1C473.089 113.1 476.639 112.1 479.239 110.1C481.839 108.1 483.139 105.35 483.139 101.85C483.139 99.45 482.339 97.5 480.739 96C479.139 94.4 477.089 93.2 474.589 92.4C472.189 91.5 468.839 90.45 464.539 89.25C458.639 87.75 453.839 86.25 450.139 84.75C446.539 83.25 443.389 80.95 440.689 77.85C438.089 74.65 436.789 70.35 436.789 64.95C436.789 60.55 437.989 56.6 440.389 53.1C442.789 49.5 446.189 46.7 450.589 44.7C455.089 42.7 460.139 41.7 465.739 41.7C472.039 41.7 477.539 42.7 482.239 44.7C486.939 46.7 490.639 49.65 493.339 53.55C496.039 57.35 497.639 61.85 498.139 67.05H481.489C480.889 63.35 479.239 60.5 476.539 58.5C473.839 56.4 470.289 55.35 465.889 55.35C462.089 55.35 459.039 56.15 456.739 57.75C454.439 59.35 453.289 61.55 453.289 64.35C453.289 66.45 454.039 68.15 455.539 69.45C457.039 70.75 458.889 71.8 461.089 72.6C463.289 73.3 466.439 74.2 470.539 75.3C476.739 76.7 481.739 78.2 485.539 79.8C489.439 81.3 492.789 83.8 495.589 87.3C498.489 90.7 499.939 95.4 499.939 101.4C499.939 106.6 498.589 111.15 495.889 115.05C493.289 118.85 489.589 121.85 484.789 124.05C480.089 126.15 474.689 127.2 468.589 127.2Z"
        fill="currentColor"
      />
      <path
        d="M0 127C0 126.448 0.447715 126 1 126H19V163C19 163.552 18.5523 164 18 164H1C0.447715 164 0 163.552 0 163V127Z"
        fill="#FA75AA"
      />
      <path
        d="M78 126H96C96.5523 126 97 126.448 97 127V163C97 163.552 96.5523 164 96 164H79C78.4477 164 78 163.552 78 163V126Z"
        fill="#FA75AA"
      />
      <path
        d="M18.9268 108.694C18.9268 108.034 19.7126 107.5 20.3456 107.5H76.3678C77.0008 107.5 78.0732 108.047 78.0732 108.707V126C77.6789 126 77.8739 126 77.2409 126H18.9268C18.9268 125.5 19.3211 126 18.9268 126V108.694Z"
        fill="currentColor"
      />
      <path
        d="M0 90.1935C0 89.5344 0.513186 89 1.14623 89H18.1965C18.8295 89 19 89.3408 19 90L18.9268 106.293C18.9268 106.953 18.8295 107.5 18.1965 107.5H1.14623C0.513186 107.5 0 106.966 0 106.306V90.1935Z"
        fill="currentColor"
      />
      <path
        d="M78 90C78 89.3408 78.1705 89 78.8036 89H95.8538C96.4868 89 97 89.5344 97 90.1935V106.306C97 106.966 96.4868 107.5 95.8538 107.5H78.8036C78.1705 107.5 78.0732 106.908 78.0732 106.249L78 90Z"
        fill="currentColor"
      />
      <path
        d="M18.9268 109.109C18.9268 107.676 18.1382 107.5 16.692 107.5L17.3368 106.232C17.886 105.411 18.9268 103.88 18.9268 105.087C18.9268 106.696 19.7154 107.5 21.2053 107.5L20.8471 108.246L20.2024 109.141L18.9268 109.109Z"
        fill="currentColor"
      />
      <path
        d="M78.0732 109.511C78.0732 107.902 78.8036 107.5 80.2363 107.5L79.5609 106.249C78.9855 105.394 78.0662 103.685 78.0732 105.087C78.0803 106.524 77.2846 107.5 75.5798 107.5L75.8834 108.346L76.5588 109.278L78.0732 109.511Z"
        fill="currentColor"
      />
      <path
        d="M0 44C0 43.4477 0.447715 43 1 43H18C18.5523 43 19 43.4477 19 44V92H0V44Z"
        fill="currentColor"
      />
      <path
        d="M78 44C78 43.4477 78.4477 43 79 43H96C96.5523 43 97 43.4477 97 44V92H78V44Z"
        fill="currentColor"
      />
    </svg>
  );
};

export const IconUmansAssistant = ({
  className,
  ...props
}: React.ComponentProps<'svg'>) => {
  return (
    <svg
      role="img"
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 256 256"
      fill="none"
      className={cn('h-4 w-4', className)}
      {...props}
    >
      <title>Umans Assistant icon</title>

      {/* Head with no stroke */}
      <path
        d="M72 96a56 56 0 1 1 56 56 56.06 56.06 0 0 1-56-96Z"
        stroke="currentColor"
        strokeWidth="16"
      />
      <g
        transform={`
          translate(4, -120)
          scale(2.5)
        `}
      >
        <path
          d="M0 127C0 126.448 0.447715 126 1 126H19V163C19 163.552 18.5523 164 18 164H1C0.447715 164 0 163.552 0 163V127Z"
          fill="#FA75AA"
        />
        <path
          d="M78 126H96C96.5523 126 97 126.448 97 127V163C97 163.552 96.5523 164 96 164H79C78.4477 164 78 163.552 78 163V126Z"
          fill="#FA75AA"
        />
        <path
          d="M18.9268 108.694C18.9268 108.034 19.7126 107.5 20.3456 107.5H76.3678C77.0008 107.5 78.0732 108.047 78.0732 108.707V126C77.6789 126 77.8739 126 77.2409 126H18.9268C18.9268 125.5 19.3211 126 18.9268 126V108.694Z"
          fill="currentColor"
        />
      </g>
    </svg>
  );
};

export const IconUmansULogo = ({
  className,
  ...props
}: React.ComponentProps<'svg'>) => {
  return (
    <svg
      viewBox="0 0 24 24"
      role="img"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      {...props}
    >
      <title>Umans Assistant icon</title>
      <g
        transform={`
          translate(6, 0)
          scale(0.12)
        `}
      >
        <path
          d="M0 127C0 126.448 0.447715 126 1 126H19V163C19 163.552 18.5523 164 18 164H1C0.447715 164 0 163.552 0 163V127Z"
          fill="#FA75AA"
        />
        <path
          d="M78 126H96C96.5523 126 97 126.448 97 127V163C97 163.552 96.5523 164 96 164H79C78.4477 164 78 163.552 78 163V126Z"
          fill="#FA75AA"
        />
        <path
          d="M18.9268 108.694C18.9268 108.034 19.7126 107.5 20.3456 107.5H76.3678C77.0008 107.5 78.0732 108.047 78.0732 108.707V126C77.6789 126 77.8739 126 77.2409 126H18.9268C18.9268 125.5 19.3211 126 18.9268 126V108.694Z"
          fill="currentColor"
        />
        <path
          d="M0 90.1935C0 89.5344 0.513186 89 1.14623 89H18.1965C18.8295 89 19 89.3408 19 90L18.9268 106.293C18.9268 106.953 18.8295 107.5 18.1965 107.5H1.14623C0.513186 107.5 0 106.966 0 106.306V90.1935Z"
          fill="currentColor"
        />
        <path
          d="M78 90C78 89.3408 78.1705 89 78.8036 89H95.8538C96.4868 89 97 89.5344 97 90.1935V106.306C97 106.966 96.4868 107.5 95.8538 107.5H78.8036C78.1705 107.5 78.0732 106.908 78.0732 106.249L78 90Z"
          fill="currentColor"
        />
        <path
          d="M18.9268 109.109C18.9268 107.676 18.1382 107.5 16.692 107.5L17.3368 106.232C17.886 105.411 18.9268 103.88 18.9268 105.087C18.9268 106.696 19.7154 107.5 21.2053 107.5L20.8471 108.246L20.2024 109.141L18.9268 109.109Z"
          fill="currentColor"
        />
        <path
          d="M78.0732 109.511C78.0732 107.902 78.8036 107.5 80.2363 107.5L79.5609 106.249C78.9855 105.394 78.0662 103.685 78.0732 105.087C78.0803 106.524 77.2846 107.5 75.5798 107.5L75.8834 108.346L76.5588 109.278L78.0732 109.511Z"
          fill="currentColor"
        />
        <path
          d="M0 44C0 43.4477 0.447715 43 1 43H18C18.5523 43 19 43.4477 19 44V92H0V44Z"
          fill="currentColor"
        />
        <path
          d="M78 44C78 43.4477 78.4477 43 79 43H96C96.5523 43 97 43.4477 97 44V92H78V44Z"
          fill="currentColor"
        />
      </g>
    </svg>
  );
};

export const IconUmansChat = ({
  className,
  inverted,
  ...props
}: React.ComponentProps<'svg'> & { inverted?: boolean }) => {
  const id = React.useId();

  return (
    <svg
      viewBox="0 0 17 17"
      aria-label="Umans chat icon"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn('h-4 w-4', className)}
      {...props}
    >
      <path
        d="M1 16L2.58314 11.2506C1.83084 9.74642 1.63835 8.02363 2.04013 6.39052C2.4419 4.75741 3.41171 3.32057 4.776 2.33712C6.1403 1.35367 7.81003 0.887808 9.4864 1.02289C11.1628 1.15798 12.7364 1.8852 13.9256 3.07442C15.1148 4.26363 15.842 5.83723 15.9771 7.5136C16.1122 9.18997 15.6463 10.8597 14.6629 12.224C13.6794 13.5883 12.2426 14.5581 10.6095 14.9599C8.97637 15.3616 7.25358 15.1692 5.74942 14.4169L1 16Z"
        stroke={inverted ? 'black' : 'CurrentColor'}
        strokeWidth={0.5}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <g
        transform="
      translate(8.5, 8.5)
      scale(0.065)
      translate(-41, -105)
    "
      >
        <path
          d="M0 127C0 126.448 0.447715 126 1 126H19V163C19 163.552 18.5523 164 18 164H1C0.447715 164 0 163.552 0 163V127Z"
          fill="#FA75AA"
        />
        <path
          d="M78 126H96C96.5523 126 97 126.448 97 127V163C97 163.552 96.5523 164 96 164H79C78.4477 164 78 163.552 78 163V126Z"
          fill="#FA75AA"
        />
        <path
          d="M18.9268 108.694C18.9268 108.034 19.7126 107.5 20.3456 107.5H76.3678C77.0008 107.5 78.0732 108.047 78.0732 108.707V126C77.6789 126 77.8739 126 77.2409 126H18.9268C18.9268 125.5 19.3211 126 18.9268 126V108.694Z"
          fill="CurrentColor"
        />
        <path
          d="M0 90.1935C0 89.5344 0.513186 89 1.14623 89H18.1965C18.8295 89 19 89.3408 19 90L18.9268 106.293C18.9268 106.953 18.8295 107.5 18.1965 107.5H1.14623C0.513186 107.5 0 106.966 0 106.306V90.1935Z"
          fill="CurrentColor"
        />
        <path
          d="M78 90C78 89.3408 78.1705 89 78.8036 89H95.8538C96.4868 89 97 89.5344 97 90.1935V106.306C97 106.966 96.4868 107.5 95.8538 107.5H78.8036C78.1705 107.5 78.0732 106.908 78.0732 106.249L78 90Z"
          fill="CurrentColor"
        />
        <path
          d="M18.9268 109.109C18.9268 107.676 18.1382 107.5 16.692 107.5L17.3368 106.232C17.886 105.411 18.9268 103.88 18.9268 105.087C18.9268 106.696 19.7154 107.5 21.2053 107.5L20.8471 108.246L20.2024 109.141L18.9268 109.109Z"
          fill="CurrentColor"
        />
        <path
          d="M78.0732 109.511C78.0732 107.902 78.8036 107.5 80.2363 107.5L79.5609 106.249C78.9855 105.394 78.0662 103.685 78.0732 105.087C78.0803 106.524 77.2846 107.5 75.5798 107.5L75.8834 108.346L76.5588 109.278L78.0732 109.511Z"
          fill="CurrentColor"
        />
        <path
          d="M0 44C0 43.4477 0.447715 43 1 43H18C18.5523 43 19 43.4477 19 44V92H0V44Z"
          fill="CurrentColor"
        />
        <path
          d="M78 44C78 43.4477 78.4477 43 79 43H96C96.5523 43 97 43.4477 97 44V92H78V44Z"
          fill="CurrentColor"
        />
      </g>
    </svg>
  );
};

export const IconMoon = ({
  className,
  ...props
}: React.ComponentProps<'svg'>) => {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 256 256"
      fill="currentColor"
      className={cn('h-4 w-4', className)}
      {...props}
    >
      <path d="M233.54 142.23a8 8 0 0 0-8-2 88.08 88.08 0 0 1-109.8-109.8 8 8 0 0 0-10-10 104.84 104.84 0 0 0-52.91 37A104 104 0 0 0 136 224a103.09 103.09 0 0 0 62.52-20.88 104.84 104.84 0 0 0 37-52.91 8 8 0 0 0-1.98-7.98Zm-44.64 48.11A88 88 0 0 1 65.66 67.11a89 89 0 0 1 31.4-26A106 106 0 0 0 96 56a104.11 104.11 0 0 0 104 104 106 106 0 0 0 14.92-1.06 89 89 0 0 1-26.02 31.4Z" />
    </svg>
  );
};

export const IconSun = ({
  className,
  ...props
}: React.ComponentProps<'svg'>) => {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 256 256"
      fill="currentColor"
      className={cn('h-4 w-4', className)}
      {...props}
    >
      <path d="M120 40V16a8 8 0 0 1 16 0v24a8 8 0 0 1-16 0Zm72 88a64 64 0 1 1-64-64 64.07 64.07 0 0 1 64 64Zm-16 0a48 48 0 1 0-48 48 48.05 48.05 0 0 0 48-48ZM58.34 69.66a8 8 0 0 0 11.32-11.32l-16-16a8 8 0 0 0-11.32 11.32Zm0 116.68-16 16a8 8 0 0 0 11.32 11.32l16-16a8 8 0 0 0-11.32-11.32ZM192 72a8 8 0 0 0 5.66-2.34l16-16a8 8 0 0 0-11.32-11.32l-16 16A8 8 0 0 0 192 72Zm5.66 114.34a8 8 0 0 0-11.32 11.32l16 16a8 8 0 0 0 11.32-11.32ZM48 128a8 8 0 0 0-8-8H16a8 8 0 0 0 0 16h24a8 8 0 0 0 8-8Zm80 80a8 8 0 0 0-8 8v24a8 8 0 0 0 16 0v-24a8 8 0 0 0-8-8Zm112-88h-24a8 8 0 0 0 0 16h24a8 8 0 0 0 0-16Z" />
    </svg>
  );
};

export const GitIcon = ({
  status = 'none',
}: {
  status?: 'none' | 'indexing' | 'indexed';
}) => {
  // Always use the same color for the Git icon itself, regardless of status
  const iconColor = 'currentColor';

  // Define status indicator colors
  const statusColors = {
    indexing: '#FA75AA', // Pink color from Umans logo for indexing
    indexed: '#FA75AA', // Pink color from Umans logo
  };

  // Log status changes for debugging
  useEffect(() => {
    console.log(`GitIcon status: ${status}`);
  }, [status]);

  return (
    <div className="relative">
      {/* Main Git icon - always uses the default color */}
      <svg
        height="16"
        strokeLinejoin="round"
        viewBox="0 0 16 16"
        width="16"
        style={{ color: iconColor }}
      >
        <g clipPath="url(#clip0_872_3147)">
          <path
            fillRule="evenodd"
            clipRule="evenodd"
            d="M8 0C3.58 0 0 3.57879 0 7.99729C0 11.5361 2.29 14.5251 5.47 15.5847C5.87 15.6547 6.02 15.4148 6.02 15.2049C6.02 15.0149 6.01 14.3851 6.01 13.7154C4 14.0852 3.48 13.2255 3.32 12.7757C3.23 12.5458 2.84 11.836 2.5 11.6461C2.22 11.4961 1.82 11.1262 2.49 11.1162C3.12 11.1062 3.57 11.696 3.72 11.936C4.44 13.1455 5.59 12.8057 6.05 12.5957C6.12 12.0759 6.33 11.726 6.56 11.5261C4.78 11.3262 2.92 10.6364 2.92 7.57743C2.92 6.70773 3.23 5.98797 3.74 5.42816C3.66 5.22823 3.38 4.40851 3.82 3.30888C3.82 3.30888 4.49 3.09895 6.02 4.1286C6.66 3.94866 7.34 3.85869 8.02 3.85869C8.7 3.85869 9.38 3.94866 10.02 4.1286C11.55 3.08895 12.22 3.30888 12.22 3.30888C12.66 4.40851 12.38 5.22823 12.3 5.42816C12.81 5.98797 13.12 6.69773 13.12 7.57743C13.12 10.6464 11.25 11.3262 9.47 11.5261C9.76 11.776 10.01 12.2558 10.01 13.0056C10.01 14.0752 10 14.9349 10 15.2049C10 15.4148 10.15 15.6647 10.55 15.5847C12.1381 15.0488 13.5182 14.0284 14.4958 12.6673C15.4735 11.3062 15.9996 9.67293 16 7.99729C16 3.57879 12.42 0 8 0Z"
            fill="currentColor"
          />
        </g>
        <defs>
          <clipPath id="clip0_872_3147">
            <rect width="16" height="16" fill="white" />
          </clipPath>
        </defs>
      </svg>

      {/* Status indicators - show indexing animation only for indexing status */}
      {status === 'indexing' && (
        <div
          className="absolute -bottom-1 -right-1 w-2 h-2 rounded-full animate-pulse"
          style={{ backgroundColor: statusColors.indexing }}
        />
      )}

      {/* Show checkmark for indexed status - now without the background circle */}
      {status === 'indexed' && (
        <div className="absolute -bottom-1 -right-1 flex items-center justify-center w-2.5 h-2.5">
          <svg
            width="10"
            height="10"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M20 6L9 17L4 12"
              stroke={statusColors.indexed}
              strokeWidth="4"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
      )}
    </div>
  );
};

export const BoxIcon = ({ size = 16 }: { size: number }) => {
  return <Box size={size} />;
};

export const HomeIcon = ({ size = 16 }: { size: number }) => {
  return <Home size={size} />;
};

export const GPSIcon = ({ size = 16 }: { size: number }) => {
  return <Navigation size={size} />;
};

export const InvoiceIcon = ({ size = 16 }: { size: number }) => {
  return <Receipt size={size} />;
};

export const LogoOpenAI = ({ size = 16 }: { size?: number }) => {
  return (
    <svg
      height={size}
      strokeLinejoin="round"
      viewBox="0 0 16 16"
      width={size}
      style={{ color: 'currentcolor' }}
    >
      <path
        d="M14.9449 6.54871C15.3128 5.45919 15.1861 4.26567 14.5978 3.27464C13.7131 1.75461 11.9345 0.972595 10.1974 1.3406C9.42464 0.481584 8.3144 -0.00692594 7.15045 7.42132e-05C5.37487 -0.00392587 3.79946 1.1241 3.2532 2.79113C2.11256 3.02164 1.12799 3.72615 0.551837 4.72468C-0.339497 6.24071 -0.1363 8.15175 1.05451 9.45178C0.686626 10.5413 0.813308 11.7348 1.40162 12.7258C2.28637 14.2459 4.06498 15.0279 5.80204 14.6599C6.5743 15.5189 7.68504 16.0074 8.849 15.9999C10.6256 16.0044 12.2015 14.8754 12.7478 13.2069C13.8884 12.9764 14.873 12.2718 15.4491 11.2733C16.3394 9.75728 16.1357 7.84774 14.9454 6.54771L14.9449 6.54871ZM8.85001 14.9544C8.13907 14.9554 7.45043 14.7099 6.90468 14.2604C6.92951 14.2474 6.97259 14.2239 7.00046 14.2069L10.2293 12.3668C10.3945 12.2743 10.4959 12.1008 10.4949 11.9133V7.42173L11.8595 8.19925C11.8742 8.20625 11.8838 8.22025 11.8858 8.23625V11.9558C11.8838 13.6099 10.5263 14.9509 8.85001 14.9544ZM2.32133 12.2028C1.9651 11.5958 1.8369 10.8843 1.95902 10.1938C1.98284 10.2078 2.02489 10.2333 2.05479 10.2503L5.28366 12.0903C5.44733 12.1848 5.65003 12.1848 5.81421 12.0903L9.75604 9.84429V11.3993C9.75705 11.4153 9.74945 11.4308 9.73678 11.4408L6.47295 13.3004C5.01915 14.1264 3.1625 13.6354 2.32184 12.2028H2.32133ZM1.47155 5.24819C1.82626 4.64017 2.38619 4.17516 3.05305 3.93366C3.05305 3.96116 3.05152 4.00966 3.05152 4.04366V7.72424C3.05051 7.91124 3.15186 8.08475 3.31654 8.17725L7.25838 10.4228L5.89376 11.2003C5.88008 11.2093 5.86285 11.2108 5.84765 11.2043L2.58331 9.34327C1.13255 8.51426 0.63494 6.68272 1.47104 5.24869L1.47155 5.24819ZM12.6834 7.82274L8.74157 5.57669L10.1062 4.79968C10.1199 4.79068 10.1371 4.78918 10.1523 4.79568L13.4166 6.65522C14.8699 7.48373 15.3681 9.31827 14.5284 10.7523C14.1732 11.3593 13.6138 11.8243 12.9474 12.0663V8.27575C12.9489 8.08875 12.8481 7.91574 12.6839 7.82274H12.6834ZM14.0414 5.8057C14.0176 5.7912 13.9756 5.7662 13.9457 5.7492L10.7168 3.90916C10.5531 3.81466 10.3504 3.81466 10.1863 3.90916L6.24442 6.15521V4.60017C6.2434 4.58417 6.251 4.56867 6.26367 4.55867L9.52751 2.70063C10.9813 1.87311 12.84 2.36563 13.6781 3.80066C14.0323 4.40667 14.1605 5.11618 14.0404 5.8057H14.0414ZM5.50257 8.57726L4.13744 7.79974C4.12275 7.79274 4.11312 7.77874 4.11109 7.76274V4.04316C4.11211 2.38713 5.47368 1.0451 7.15197 1.0461C7.86189 1.0461 8.54902 1.2921 9.09476 1.74011C9.06993 1.75311 9.02737 1.77661 8.99899 1.79361L5.77012 3.63365C5.60493 3.72615 5.50358 3.89916 5.50459 4.08666L5.50257 8.57626V8.57726ZM6.24391 7.00022L7.99972 5.9997L9.75553 6.99972V9.00027L7.99972 10.0003L6.24391 9.00027V7.00022Z"
        fill="currentColor"
      />
    </svg>
  );
};

export const LogoGoogle = ({ size = 16 }: { size?: number }) => {
  return (
    <svg
      data-testid="geist-icon"
      height={size}
      strokeLinejoin="round"
      viewBox="0 0 16 16"
      width={size}
      style={{ color: 'currentcolor' }}
    >
      <path
        d="M8.15991 6.54543V9.64362H12.4654C12.2763 10.64 11.709 11.4837 10.8581 12.0509L13.4544 14.0655C14.9671 12.6692 15.8399 10.6182 15.8399 8.18188C15.8399 7.61461 15.789 7.06911 15.6944 6.54552L8.15991 6.54543Z"
        fill="#4285F4"
      />
      <path
        d="M3.6764 9.52268L3.09083 9.97093L1.01807 11.5855C2.33443 14.1963 5.03241 16 8.15966 16C10.3196 16 12.1305 15.2873 13.4542 14.0655L10.8578 12.0509C10.1451 12.5309 9.23598 12.8219 8.15966 12.8219C6.07967 12.8219 4.31245 11.4182 3.67967 9.5273L3.6764 9.52268Z"
        fill="#34A853"
      />
      <path
        d="M1.01803 4.41455C0.472607 5.49087 0.159912 6.70543 0.159912 7.99995C0.159912 9.29447 0.472607 10.509 1.01803 11.5854C1.01803 11.5926 3.6799 9.51991 3.6799 9.51991C3.5199 9.03991 3.42532 8.53085 3.42532 7.99987C3.42532 7.46889 3.5199 6.95983 3.6799 6.47983L1.01803 4.41455Z"
        fill="#FBBC05"
      />
      <path
        d="M8.15982 3.18545C9.33802 3.18545 10.3853 3.59271 11.2216 4.37818L13.5125 2.0873C12.1234 0.792777 10.3199 0 8.15982 0C5.03257 0 2.33443 1.79636 1.01807 4.41455L3.67985 6.48001C4.31254 4.58908 6.07983 3.18545 8.15982 3.18545Z"
        fill="#EA4335"
      />
    </svg>
  );
};

export const LogoAnthropic = () => {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      xmlnsXlink="http://www.w3.org/1999/xlink"
      x="0px"
      y="0px"
      viewBox="0 0 92.2 65"
      style={{ color: 'currentcolor', fill: 'currentcolor' }}
      width="18px"
      height="18px"
    >
      <path
        d="M66.5,0H52.4l25.7,65h14.1L66.5,0z M25.7,0L0,65h14.4l5.3-13.6h26.9L51.8,65h14.4L40.5,0C40.5,0,25.7,0,25.7,0z
		M24.3,39.3l8.8-22.8l8.8,22.8H24.3z"
      />
    </svg>
  );
};

export const RouteIcon = ({ size = 16 }: { size?: number }) => {
  return (
    <svg
      height={size}
      strokeLinejoin="round"
      viewBox="0 0 16 16"
      width={size}
      style={{ color: 'currentcolor' }}
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M7.53033 0.719661L7 0.189331L5.93934 1.24999L6.46967 1.78032L6.68934 1.99999H3.375C1.51104 1.99999 0 3.51103 0 5.37499C0 7.23895 1.51104 8.74999 3.375 8.74999H12.625C13.6605 8.74999 14.5 9.58946 14.5 10.625C14.5 11.6605 13.6605 12.5 12.625 12.5H4.88555C4.56698 11.4857 3.61941 10.75 2.5 10.75C1.11929 10.75 0 11.8693 0 13.25C0 14.6307 1.11929 15.75 2.5 15.75C3.61941 15.75 4.56698 15.0143 4.88555 14H12.625C14.489 14 16 12.489 16 10.625C16 8.76103 14.489 7.24999 12.625 7.24999H3.375C2.33947 7.24999 1.5 6.41052 1.5 5.37499C1.5 4.33946 2.33947 3.49999 3.375 3.49999H6.68934L6.46967 3.71966L5.93934 4.24999L7 5.31065L7.53033 4.78032L8.85355 3.4571C9.24408 3.06657 9.24408 2.43341 8.85355 2.04288L7.53033 0.719661ZM2.5 14.25C3.05228 14.25 3.5 13.8023 3.5 13.25C3.5 12.6977 3.05228 12.25 2.5 12.25C1.94772 12.25 1.5 12.6977 1.5 13.25C1.5 13.8023 1.94772 14.25 2.5 14.25ZM14.5 2.74999C14.5 3.30228 14.0523 3.74999 13.5 3.74999C12.9477 3.74999 12.5 3.30228 12.5 2.74999C12.5 2.19771 12.9477 1.74999 13.5 1.74999C14.0523 1.74999 14.5 2.19771 14.5 2.74999ZM16 2.74999C16 4.1307 14.8807 5.24999 13.5 5.24999C12.1193 5.24999 11 4.1307 11 2.74999C11 1.36928 12.1193 0.249991 13.5 0.249991C14.8807 0.249991 16 1.36928 16 2.74999Z"
        fill="currentColor"
      />
    </svg>
  );
};

export const FileIcon = ({ size = 16 }: { size?: number }) => {
  return <File size={size} />;
};

export const LoaderIcon = ({ size = 16 }: { size?: number }) => {
  return <Loader size={size} />;
};

export const UploadIcon = ({ size = 16 }: { size?: number }) => {
  return <Upload size={size} />;
};

export const MenuIcon = ({ size = 16 }: { size?: number }) => {
  return <Menu size={size} />;
};

export const PencilEditIcon = ({ size = 16 }: { size?: number }) => {
  return <Edit size={size} />;
};

export const CheckedSquare = ({ size = 16 }: { size?: number }) => {
  return (
    <svg
      height={size}
      strokeLinejoin="round"
      viewBox="0 0 16 16"
      width={size}
      style={{ color: 'currentcolor' }}
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M15 16H1C0.447715 16 0 15.5523 0 15V1C0 0.447715 0.447716 0 1 0L15 8.17435e-06C15.5523 8.47532e-06 16 0.447724 16 1.00001V15C16 15.5523 15.5523 16 15 16ZM11.7803 6.28033L12.3107 5.75L11.25 4.68934L10.7197 5.21967L6.5 9.43935L5.28033 8.21967L4.75001 7.68934L3.68934 8.74999L4.21967 9.28033L5.96967 11.0303C6.11032 11.171 6.30109 11.25 6.5 11.25C6.69891 11.25 6.88968 11.171 7.03033 11.0303L11.7803 6.28033Z"
        fill="currentColor"
      />
    </svg>
  );
};

export const UncheckedSquare = ({ size = 16 }: { size?: number }) => {
  return (
    <svg
      height={size}
      strokeLinejoin="round"
      viewBox="0 0 16 16"
      width={size}
      style={{ color: 'currentcolor' }}
    >
      <rect
        x="1"
        y="1"
        width="14"
        height="14"
        stroke="currentColor"
        strokeWidth="1.5"
        fill="none"
      />
    </svg>
  );
};

export const MoreIcon = ({ size = 16 }: { size?: number }) => {
  return <MoreVertical size={size} />;
};

export const TrashIcon = ({ size = 16 }: { size?: number }) => {
  return (
    <svg
      height={size}
      strokeLinejoin="round"
      viewBox="0 0 16 16"
      width={size}
      style={{ color: 'currentcolor' }}
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M6.75 2.75C6.75 2.05964 7.30964 1.5 8 1.5C8.69036 1.5 9.25 2.05964 9.25 2.75V3H6.75V2.75ZM5.25 3V2.75C5.25 1.23122 6.48122 0 8 0C9.51878 0 10.75 1.23122 10.75 2.75V3H12.9201H14.25H15V4.5H14.25H13.8846L13.1776 13.6917C13.0774 14.9942 11.9913 16 10.6849 16H5.31508C4.00874 16 2.92263 14.9942 2.82244 13.6917L2.11538 4.5H1.75H1V3H1.75H3.07988H5.25ZM4.31802 13.5767L3.61982 4.5H12.3802L11.682 13.5767C11.6419 14.0977 11.2075 14.5 10.6849 14.5H5.31508C4.79254 14.5 4.3581 14.0977 4.31802 13.5767Z"
        fill="currentColor"
      />
    </svg>
  );
};

export const InfoIcon = ({ size = 16 }: { size?: number }) => {
  return <Info size={size} />;
};

export const ArrowUpIcon = ({ size = 16 }: { size?: number }) => {
  return <ArrowUp size={size} />;
};

export const StopIcon = ({ size = 16 }: { size?: number }) => {
  return <Square size={size} />;
};

export const PaperclipIcon = ({ size = 16 }: { size?: number }) => {
  return <Paperclip size={size} className="-rotate-45" />;
};

export const MoreHorizontalIcon = ({ size = 16 }: { size?: number }) => {
  return <MoreHorizontal size={size} />;
};

export const MessageIcon = ({ size = 16 }: { size?: number }) => {
  return <MessageCircle size={size} />;
};

export const CrossIcon = ({ size = 16 }: { size?: number }) => (
  <X size={size} />
);

export const CrossSmallIcon = ({ size = 16 }: { size?: number }) => (
  <X size={size} />
);

export const UndoIcon = ({ size = 16 }: { size?: number }) => (
  <Undo size={size} />
);

export const RedoIcon = ({ size = 16 }: { size?: number }) => (
  <Redo size={size} />
);

export const DeltaIcon = ({ size = 16 }: { size?: number }) => (
  <svg
    height={size}
    strokeLinejoin="round"
    viewBox="0 0 16 16"
    width={size}
    style={{ color: 'currentcolor' }}
  >
    <path
      fillRule="evenodd"
      clipRule="evenodd"
      d="M2.67705 15H1L1.75 13.5L6.16147 4.67705L6.15836 4.67082L6.16667 4.66667L7.16147 2.67705L8 1L8.83853 2.67705L14.25 13.5L15 15H13.3229H2.67705ZM7 6.3541L10.5729 13.5H3.42705L7 6.3541Z"
      fill="currentColor"
    />
  </svg>
);

export const PenIcon = ({ size = 16 }: { size?: number }) => (
  <svg
    height={size}
    strokeLinejoin="round"
    viewBox="0 0 16 16"
    width={size}
    style={{ color: 'currentcolor' }}
  >
    <path
      fillRule="evenodd"
      clipRule="evenodd"
      d="M8.75 0.189331L9.28033 0.719661L15.2803 6.71966L15.8107 7.24999L15.2803 7.78032L13.7374 9.32322C13.1911 9.8696 12.3733 9.97916 11.718 9.65188L9.54863 13.5568C8.71088 15.0648 7.12143 16 5.39639 16H0.75H0V15.25V10.6036C0 8.87856 0.935237 7.28911 2.4432 6.45136L6.34811 4.28196C6.02084 3.62674 6.13039 2.80894 6.67678 2.26255L8.21967 0.719661L8.75 0.189331ZM7.3697 5.43035L10.5696 8.63029L8.2374 12.8283C7.6642 13.8601 6.57668 14.5 5.39639 14.5H2.56066L5.53033 11.5303L4.46967 10.4697L1.5 13.4393V10.6036C1.5 9.42331 2.1399 8.33579 3.17166 7.76259L7.3697 5.43035ZM12.6768 8.26256C12.5791 8.36019 12.4209 8.36019 12.3232 8.26255L12.0303 7.96966L8.03033 3.96966L7.73744 3.67677C7.63981 3.57914 7.63981 3.42085 7.73744 3.32321L8.75 2.31065L13.6893 7.24999L12.6768 8.26256Z"
      fill="currentColor"
    />
  </svg>
);

export const SummarizeIcon = ({ size = 16 }: { size?: number }) => (
  <svg
    height={size}
    strokeLinejoin="round"
    viewBox="0 0 16 16"
    width={size}
    style={{ color: 'currentcolor' }}
  >
    <path
      fillRule="evenodd"
      clipRule="evenodd"
      d="M1.75 12H1V10.5H1.75H5.25H6V12H5.25H1.75ZM1.75 7.75H1V6.25H1.75H4.25H5V7.75H4.25H1.75ZM1.75 3.5H1V2H1.75H7.25H8V3.5H7.25H1.75ZM12.5303 14.7803C12.2374 15.0732 11.7626 15.0732 11.4697 14.7803L9.21967 12.5303L8.68934 12L9.75 10.9393L10.2803 11.4697L11.25 12.4393V2.75V2H12.75V2.75V12.4393L13.7197 11.4697L14.25 10.9393L15.3107 12L14.7803 12.5303L12.5303 14.7803Z"
      fill="currentColor"
    />
  </svg>
);

export const SidebarLeftIcon = ({ size = 16 }: { size?: number }) => (
  <PanelLeft size={size} />
);

export const PlusIcon = ({ size = 16 }: { size?: number }) => (
  <Plus size={size} />
);

export const CopyIcon = ({ size = 16 }: { size?: number }) => (
  <Copy size={size} />
);

export const ThumbUpIcon = ({ size = 16 }: { size?: number }) => (
  <ThumbsUp size={size} />
);

export const ThumbDownIcon = ({ size = 16 }: { size?: number }) => (
  <ThumbsDown size={size} />
);

export const ChevronDownIcon = ({ size = 16 }: { size?: number }) => (
  <ChevronDown size={size} />
);

export const SparklesIcon = ({ size = 16 }: { size?: number }) => (
  <Sparkles size={size} />
);

export const CheckCircleFillIcon = ({
  size = 16,
  className,
}: { size?: number; className?: string }) => {
  return <IoCheckmarkCircle size={size} className={className} />;
};

export const GlobeIcon = ({ size = 16 }: { size?: number }) => {
  return <Globe size={size} />;
};

export const LockIcon = ({ size = 16 }: { size?: number }) => {
  return <Lock size={size} />;
};

export const EyeIcon = ({ size = 16 }: { size?: number }) => {
  return <Eye size={size} />;
};

export const ShareIcon = ({ size = 16 }: { size?: number }) => {
  return <Share size={size} />;
};

export const CodeIcon = ({ size = 16 }: { size?: number }) => {
  return <LucideCode size={size} />;
};

export const SearchIcon = ({
  size = 16,
  className,
}: { size?: number; className?: string }) => {
  return <Search size={size} className={className} />;
};

export const PlayIcon = ({ size = 16 }: { size?: number }) => {
  return <Play size={size} />;
};

export const PythonIcon = ({ size = 16 }: { size?: number }) => {
  return (
    <svg
      height={size}
      strokeLinejoin="round"
      viewBox="0 0 16 16"
      width={size}
      style={{ color: 'currentcolor' }}
    >
      <path
        d="M7.90474 0.00013087C7.24499 0.00316291 6.61494 0.0588153 6.06057 0.15584C4.42745 0.441207 4.13094 1.0385 4.13094 2.14002V3.59479H7.9902V4.07971H4.13094H2.68259C1.56099 4.07971 0.578874 4.7465 0.271682 6.01496C-0.0826597 7.4689 -0.0983767 8.37619 0.271682 9.89434C0.546012 11.0244 1.20115 11.8296 2.32276 11.8296H3.64966V10.0856C3.64966 8.82574 4.75179 7.71441 6.06057 7.71441H9.91533C10.9884 7.71441 11.845 6.84056 11.845 5.77472V2.14002C11.845 1.10556 10.9626 0.328487 9.91533 0.15584C9.25237 0.046687 8.56448 -0.00290121 7.90474 0.00013087ZM5.81768 1.17017C6.21631 1.17017 6.54185 1.49742 6.54185 1.89978C6.54185 2.30072 6.21631 2.62494 5.81768 2.62494C5.41761 2.62494 5.09351 2.30072 5.09351 1.89978C5.09351 1.49742 5.41761 1.17017 5.81768 1.17017Z"
        fill="currentColor"
      />
      <path
        d="M12.3262 4.07971V5.77472C12.3262 7.08883 11.1997 8.19488 9.91525 8.19488H6.06049C5.0046 8.19488 4.13086 9.0887 4.13086 10.1346V13.7693C4.13086 14.8037 5.04033 15.4122 6.06049 15.709C7.28211 16.0642 8.45359 16.1285 9.91525 15.709C10.8868 15.4307 11.8449 14.8708 11.8449 13.7693V12.3145H7.99012V11.8296H11.8449H13.7745C14.8961 11.8296 15.3141 11.0558 15.7041 9.89434C16.1071 8.69865 16.0899 7.5488 15.7041 6.01495C15.4269 4.91058 14.8975 4.07971 13.7745 4.07971H12.3262ZM10.1581 13.2843C10.5582 13.2843 10.8823 13.6086 10.8823 14.0095C10.8823 14.4119 10.5582 14.7391 10.1581 14.7391C9.7595 14.7391 9.43397 14.4119 9.43397 14.0095C9.43397 13.6086 9.7595 13.2843 10.1581 13.2843Z"
        fill="currentColor"
      />
    </svg>
  );
};

export const TerminalWindowIcon = ({ size = 16 }: { size?: number }) => {
  return <TbTerminal2 size={size} />;
};

export const TerminalIcon = ({ size = 16 }: { size?: number }) => {
  return <Terminal size={size} />;
};

export const ClockRewind = ({ size = 16 }: { size?: number }) => {
  return <RotateCcw size={size} />;
};

export const LogsIcon = ({ size = 16 }: { size?: number }) => {
  return (
    <svg
      height={size}
      strokeLinejoin="round"
      viewBox="0 0 16 16"
      width={size}
      style={{ color: 'currentcolor' }}
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M9 2H9.75H14.25H15V3.5H14.25H9.75H9V2ZM9 12.5H9.75H14.25H15V14H14.25H9.75H9V12.5ZM9.75 7.25H9V8.75H9.75H14.25H15V7.25H14.25H9.75ZM1 12.5H1.75H2.25H3V14H2.25H1.75H1V12.5ZM1.75 2H1V3.5H1.75H2.25H3V2H2.25H1.75ZM1 7.25H1.75H2.25H3V8.75H2.25H1.75H1V7.25ZM5.75 12.5H5V14H5.75H6.25H7V12.5H6.25H5.75ZM5 2H5.75H6.25H7V3.5H6.25H5.75H5V2ZM5.75 7.25H5V8.75H5.75H6.25H7V7.25H6.25H5.75Z"
        fill="currentColor"
      />
    </svg>
  );
};

export const ImageIcon = ({ size = 16 }: { size?: number }) => {
  return <Image size={size} />;
};

export const FullscreenIcon = ({ size = 16 }: { size?: number }) => (
  <Maximize size={size} />
);

export const DownloadIcon = ({ size = 16 }: { size?: number }) => (
  <Download size={size} />
);

export const LineChartIcon = ({ size = 16 }: { size?: number }) => (
  <svg
    height={size}
    strokeLinejoin="round"
    viewBox="0 0 16 16"
    width={size}
    style={{ color: 'currentcolor' }}
  >
    <path
      fill="currentColor"
      fillRule="evenodd"
      d="M1 1v11.75A2.25 2.25 0 0 0 3.25 15H15v-1.5H3.25a.75.75 0 0 1-.75-.75V1H1Zm13.297 5.013.513-.547-1.094-1.026-.513.547-3.22 3.434-2.276-2.275a1 1 0 0 0-1.414 0L4.22 8.22l-.53.53 1.06 1.06.53-.53L7 7.56l2.287 2.287a1 1 0 0 0 1.437-.023l3.573-3.811Z"
      clipRule="evenodd"
    />
  </svg>
);

interface IconProps extends React.ComponentProps<'svg'> {
  size?: number;
}

export function MermaidDiagramIcon({ size = 24, ...props }: IconProps) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <rect width="18" height="18" x="3" y="3" rx="2" />
      <path d="M3 9h18" />
      <path d="M9 21V9" />
    </svg>
  );
}

export function MermaidCodeIcon({ size = 24, ...props }: IconProps) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <polyline points="16 18 22 12 16 6" />
      <polyline points="8 6 2 12 8 18" />
    </svg>
  );
}

export const XIcon = ({ size = 16 }: { size?: number }) => {
  return <X size={size} />;
};

export const AlertCircle = ({ size = 16 }: { size?: number }) => {
  return <LucideAlertCircle size={size} />;
};

export const BranchIcon = () => {
  return (
    <svg
      width="32"
      height="32"
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      style={{ color: 'currentcolor' }}
    >
      <path
        d="M28 7.99994C27.9996 7.25189 27.7895 6.51894 27.3935 5.88432C26.9974 5.2497 26.4314 4.73884 25.7596 4.40977C25.0878 4.08071 24.3372 3.94661 23.5931 4.02271C22.8489 4.09881 22.141 4.38206 21.5497 4.84029C20.9585 5.29853 20.5075 5.91338 20.2482 6.61502C19.9888 7.31667 19.9314 8.07698 20.0824 8.80962C20.2334 9.54226 20.5869 10.2179 21.1026 10.7597C21.6184 11.3016 22.2757 11.6879 23 11.8749V12.9999C23 13.5304 22.7893 14.0391 22.4142 14.4142C22.0392 14.7892 21.5304 14.9999 21 14.9999H12C11.2974 14.9991 10.6071 15.185 10 15.5387V11.8749C10.9427 11.6315 11.7642 11.0527 12.3106 10.2469C12.857 9.44115 13.0908 8.46375 12.9681 7.49794C12.8455 6.53212 12.3747 5.64421 11.6442 5.00062C10.9137 4.35703 9.97358 4.00195 9.00001 4.00195C8.02644 4.00195 7.08628 4.35703 6.35578 5.00062C5.62527 5.64421 5.15457 6.53212 5.03189 7.49794C4.90922 8.46375 5.143 9.44115 5.68941 10.2469C6.23582 11.0527 7.05735 11.6315 8.00001 11.8749V20.1249C7.05735 20.3683 6.23582 20.9472 5.68941 21.7529C5.143 22.5587 4.90922 23.5361 5.03189 24.5019C5.15457 25.4678 5.62527 26.3557 6.35578 26.9993C7.08628 27.6429 8.02644 27.9979 9.00001 27.9979C9.97358 27.9979 10.9137 27.6429 11.6442 26.9993C12.3747 26.3557 12.8455 25.4678 12.9681 24.5019C13.0908 23.5361 12.857 22.5587 12.3106 21.7529C11.7642 20.9472 10.9427 20.3683 10 20.1249V18.9999C10 18.4695 10.2107 17.9608 10.5858 17.5857C10.9609 17.2107 11.4696 16.9999 12 16.9999H21C22.0609 16.9999 23.0783 16.5785 23.8284 15.8284C24.5786 15.0782 25 14.0608 25 12.9999V11.8749C25.8583 11.652 26.6185 11.1506 27.1613 10.4494C27.7042 9.74822 27.9992 8.88674 28 7.99994ZM7.00001 7.99994C7.00001 7.60438 7.11731 7.2177 7.33707 6.8888C7.55683 6.5599 7.86919 6.30355 8.23464 6.15218C8.6001 6.0008 9.00223 5.9612 9.39019 6.03837C9.77815 6.11554 10.1345 6.30602 10.4142 6.58572C10.6939 6.86543 10.8844 7.2218 10.9616 7.60976C11.0388 7.99772 10.9991 8.39985 10.8478 8.76531C10.6964 9.13076 10.44 9.44311 10.1111 9.66288C9.78225 9.88264 9.39557 9.99994 9.00001 9.99994C8.46958 9.99994 7.96087 9.78922 7.5858 9.41415C7.21072 9.03908 7.00001 8.53037 7.00001 7.99994ZM11 23.9999C11 24.3955 10.8827 24.7822 10.6629 25.1111C10.4432 25.44 10.1308 25.6963 9.76538 25.8477C9.39992 25.9991 8.99779 26.0387 8.60983 25.9615C8.22187 25.8843 7.8655 25.6939 7.5858 25.4142C7.30609 25.1344 7.11561 24.7781 7.03844 24.3901C6.96127 24.0022 7.00087 23.6 7.15225 23.2346C7.30363 22.8691 7.55997 22.5568 7.88887 22.337C8.21777 22.1172 8.60445 21.9999 9.00001 21.9999C9.53044 21.9999 10.0391 22.2107 10.4142 22.5857C10.7893 22.9608 11 23.4695 11 23.9999ZM24 9.99994C23.6044 9.99994 23.2178 9.88264 22.8889 9.66288C22.56 9.44311 22.3036 9.13076 22.1523 8.76531C22.0009 8.39985 21.9613 7.99772 22.0384 7.60976C22.1156 7.2218 22.3061 6.86543 22.5858 6.58572C22.8655 6.30602 23.2219 6.11554 23.6098 6.03837C23.9978 5.9612 24.3999 6.0008 24.7654 6.15218C25.1308 6.30355 25.4432 6.5599 25.6629 6.8888C25.8827 7.2177 26 7.60438 26 7.99994C26 8.53037 25.7893 9.03908 25.4142 9.41415C25.0392 9.78922 24.5304 9.99994 24 9.99994Z"
        fill="currentColor"
      />
    </svg>
  );
};
