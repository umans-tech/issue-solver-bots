import { cn } from '@/lib/utils';
import { LoaderIcon } from './icons';
import { ImagePreview } from './image-preview';

interface ImageEditorProps {
  title: string;
  content: string;
  status: 'idle' | 'streaming';
  isInline?: boolean;
  isCurrentVersion?: boolean;
  currentVersionIndex?: number;
}

export function ImageEditor({
  title,
  content,
  status,
  isInline,
  isCurrentVersion,
  currentVersionIndex,
}: ImageEditorProps) {
  return (
    <div
      className={cn('flex flex-row items-center justify-center w-full', {
        'h-[calc(100dvh-60px)]': !isInline,
        'h-[200px]': isInline,
      })}
    >
      {status === 'streaming' ? (
        <div className="flex flex-row gap-4 items-center">
          {!isInline && (
            <div className="animate-spin">
              <LoaderIcon />
            </div>
          )}
          <div>Generating Image...</div>
        </div>
      ) : (
        <ImagePreview
          src={`data:image/png;base64,${content}`}
          alt={title}
          className={cn({
            'p-0 md:p-20': !isInline,
          })}
        />
      )}
    </div>
  );
}
