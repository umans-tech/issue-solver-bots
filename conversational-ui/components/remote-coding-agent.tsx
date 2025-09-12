import Link from "next/link";
import { RouteIcon } from "./icons";
import { ArrowUpRight, ChevronRight } from 'lucide-react';
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from "@radix-ui/react-collapsible";
import { Markdown } from "./markdown";



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
          <ArrowUpRight size={14} />
        </Link>
      </div>
    );
  };

  export const RemoteCodingAgentAnimation = () => (
    <div className="flex flex-col w-full">
      <div className="text-muted-foreground">
        <span className="animate-pulse">Launching the remote coding agent...</span>
      </div>
    </div>
  );

  export interface IssueExplanationProps {
    toolCallId: string | number;
    issueTitle: string;
    issueDescription: string;
    /** opens by default unless you pass false */
    isStreaming?: boolean;
    result: any;
  }

  export function RemoteCodingStream({
    toolCallId,
    issueTitle,
    issueDescription,
    isStreaming = true,
    result,
  }: IssueExplanationProps) {
    return (
      <Collapsible
        key={toolCallId}
        defaultOpen={isStreaming}
        className="group w-full flex flex-col
        rounded-xl 
        border border-muted/40 bg-muted/5
        shadow-sm overflow-hidden
        [&>*]:!transition-none [&>*]:!transform-none [&>*]:!animate-none"
      >
        {/* ─ summary line ─────────────────────────────────── */}
        <CollapsibleTrigger
          className="
            group flex w-full items-center justify-between gap-2 px-4 py-2
            text-left font-medium
            focus:outline-none
            overflow-hidden
            hover:bg-accent/20 cursor-pointer
            group-data-[state=closed]:rounded-xl
            group-data-[state=open]:rounded-t-xl group-data-[state=open]:rounded-b-none
          "
        >
          {isStreaming ? (
            <span className="flex-1 whitespace-normal break-words animate-pulse">
              Specifying the issue…
            </span>
          ) : (
            <div className="flex items-center gap-1 hover:text-primary transition-colors">
              <span className="whitespace-normal break-words">
                Issue description
              </span>
              {/* chevron rotates when open */}
              <ChevronRight size={16}
                className="
                  shrink-0
                  group-data-[state=open]:rotate-90
                "
              />
            </div>
          )}
                    {result && (
                            <Link target="_blank"
                 href={`/tasks/${result.processId}`} 
                 className="bg-secondary hover:bg-blue-100 dark:hover:bg-blue-900/30 border py-1.5 px-2.5 rounded-lg w-fit flex flex-row gap-2 items-center pointer-events-auto transition-colors"
               >
               <div className="text-muted-foreground">
                 <RouteIcon size={16} />
               </div>
               <span className="text-primary">resolution progress</span>
               <ArrowUpRight size={16} className="text-primary" />
             </Link>
           )}
        </CollapsibleTrigger>
  
        {/* ─ collapsible markdown body ────────────────────── */}
        <CollapsibleContent
          className={`
            ${isStreaming ? 'max-h-none' : 'max-h-[24rem]'} overflow-auto px-4 py-3
            data-[state=closed]:hidden
          `}
        >
          <div className="prose prose-sm dark:prose-invert">
            <Markdown>
              {`# ${issueTitle}\n${issueDescription}`}
            </Markdown>
          </div>
        </CollapsibleContent>
      </Collapsible>
    );
  }