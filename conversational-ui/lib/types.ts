import { z } from 'zod';
import type { getWeather } from './ai/tools/get-weather';
import type { createDocument } from './ai/tools/create-document';
import type { updateDocument } from './ai/tools/update-document';
import type { requestSuggestions } from './ai/tools/request-suggestions';
import type { InferUITool, UIMessage } from 'ai';

import type { ArtifactKind } from '@/components/artifact';
import type { Suggestion } from './db/schema';
import type { codebaseSearch } from './ai/tools/codebase-search';
import type { webSearch } from './ai/tools/web-search';
import type { remoteCodingAgent } from './ai/tools/remote-coding-agent';
import type { fetchWebpage } from './ai/tools/fetch-webpage';

export type DataPart = { type: 'append-message'; message: string };

export const messageMetadataSchema = z.object({
  createdAt: z.string(),
});

export type MessageMetadata = z.infer<typeof messageMetadataSchema>;

type weatherTool = InferUITool<typeof getWeather>;
type createDocumentTool = InferUITool<ReturnType<typeof createDocument>>;
type updateDocumentTool = InferUITool<ReturnType<typeof updateDocument>>;
type requestSuggestionsTool = InferUITool<
  ReturnType<typeof requestSuggestions>
>;
type codebaseSearchTool = InferUITool<ReturnType<typeof codebaseSearch>>;
type webSearchTool = InferUITool<ReturnType<typeof webSearch>>;
type remoteCodingAgentTool = InferUITool<ReturnType<typeof remoteCodingAgent>>;
type fetchWebpageTool = InferUITool<ReturnType<typeof fetchWebpage>>;

export type ChatTools = {
  getWeather: weatherTool;
  createDocument: createDocumentTool;
  updateDocument: updateDocumentTool;
  requestSuggestions: requestSuggestionsTool;
  codebaseSearch: codebaseSearchTool;
  webSearch: webSearchTool;
  remoteCodingAgent: remoteCodingAgentTool;
  fetchWebpage: fetchWebpageTool;
};

export type CustomUIDataTypes = {
  textDelta: string;
  imageDelta: string;
  sheetDelta: string;
  codeDelta: string;
  suggestion: Suggestion;
  appendMessage: string;
  id: string;
  title: string;
  kind: ArtifactKind;
  clear: null;
  finish: null;
};

export type ChatMessage = UIMessage<
  MessageMetadata,
  CustomUIDataTypes,
  ChatTools
>;

export interface Attachment {
  name: string;
  url: string;
  contentType: string;
}
