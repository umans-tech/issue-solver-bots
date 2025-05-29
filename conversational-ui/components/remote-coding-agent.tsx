import Link from "next/link";
import { RouteIcon } from "./icons";


export const RemoteCodingAgentResult = ({
    state,
    result
  }: {
    state: string;
    result: any;
  }) => {
    return (
      <div className="bg-background border py-2 px-3 rounded-xl w-fit flex flex-row gap-3 items-center">
        <div className="text-muted-foreground">
          <RouteIcon size={16} />
        </div>
        <Link 
          href={`/tasks/${result.processId}`} 
          className="text-primary hover:text-primary/80 flex items-center gap-2 transition-colors"
        >
          <span>View remote task progress</span>
          <svg 
            width="14" 
            height="14" 
            viewBox="0 0 24 24" 
            fill="none" 
            xmlns="http://www.w3.org/2000/svg"
            className="text-primary"
          >
            <path 
              d="M7 17L17 7M17 7H8M17 7V16" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
            />
          </svg>
        </Link>
      </div>
    );
  };
  