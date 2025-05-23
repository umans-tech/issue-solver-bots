After adding the resumable stream feature I got 3 errors (see below), the resumable stream feature is working really well with my code and redis is connect, but I have this error on shared public chats, also keep in mind you don't have access to env var and sensitive data, so don't assume they don't exist.

Error 1, when opening a public chat from non authenticated user I have this one, but I can see the chat (this exact same chat can be viewed without error for authenticated users):

 Error: Failed to parse stream string. No separator found.
    at parseDataStreamPart (http://localhost:3000/_next/static/chunks/node_modules__pnpm_b29ed4ce._.js:3303:15)
    at Array.map (<anonymous>)
    at processDataStream (http://localhost:3000/_next/static/chunks/node_modules__pnpm_b29ed4ce._.js:3355:52)
    at async processChatResponse (http://localhost:3000/_next/static/chunks/node_modules__pnpm_b29ed4ce._.js:3478:5)
    at async callChatApi (http://localhost:3000/_next/static/chunks/node_modules__pnpm_b29ed4ce._.js:3792:17)
    at async useChat.useCallback2[triggerRequest] (http://localhost:3000/_next/static/chunks/node_modules__pnpm_b29ed4ce._.js:6173:17)


Error 2, when a use is authanticated and open a public chat I have no error and can view the chat without any issue, but as soon as I continue the conversation of clone it I have the errors below:


Refreshed session data on mount: {knowledgeBaseId: null, processId: null}
chat.tsx:103 
            
            
           GET http://localhost:3000/api/chat?chatId=f0ad4d02-c5b3-48b8-8c4f-1c91d5cbca7f 404 (Not Found)
callChatApi @ call-chat-api.ts:47
useChat.useCallback2[triggerRequest] @ use-chat.ts:299
useChat.useCallback2[experimental_resume] @ use-chat.ts:472
Chat.useEffect @ chat.tsx:103
react-stack-bottom-frame @ react-dom-client.development.js:24035
runWithFiberInDEV @ react-dom-client.development.js:1510

app-sidebar.tsx:125 Current session: {user: {…}, expires: '2025-06-22T13:52:23.272Z'}
app-sidebar.tsx:126 Current spaces: [{…}]
chat-header.tsx:45 Attempting to refresh session from server...
hot-reloader-client.tsx:371 [Fast Refresh] rebuilding
chat.tsx:95 Error in useChat:
 No streams found
error @ intercept-console-error.ts:41
Chat.useChat @ chat.tsx:95
useChat.useCallback2[triggerRequest] @ use-chat.ts:366
await in useChat.useCallback2[triggerRequest]
useChat.useCallback2[experimental_resume] @ use-chat.ts:472
Chat.useEffect @ chat.tsx:103
react-stack-bottom-frame @ react-dom-client.development.js:24035
runWithFiberInDEV @ react-dom-client.development.js:1510
commitHookEffectListMount @ react-dom-client.development.js:10514
commitHookPassiveMountEffects @ react-dom-client.development.js:10635


chat.tsx:96 Call stack:
 Error: No streams found
    at callChatApi (http://localhost:3000/_next/static/chunks/node_modules__pnpm_b29ed4ce._.js:3774:15)
    at async useChat.useCallback2[triggerRequest] (http://localhost:3000/_next/static/chunks/node_modules__pnpm_b29ed4ce._.js:6173:17)
error @ intercept-console-error.ts:41
Chat.useChat @ chat.tsx:96
useChat.useCallback2[triggerRequest] @ use-chat.ts:366
await in useChat.useCallback2[triggerRequest]
useChat.useCallback2[experimental_resume] @ use-chat.ts:472
Chat.useEffect @ chat.tsx:103
react-stack-bottom-frame @ react-dom-client.development.js:24035

recursivelyTraversePassiveMountEffects @ react-dom-client.development.js:12415
commitPassiveMountOnFiber @ react-dom-client.development.js:12434Understand this error
message.tsx:181 Rendering message 36b82d31-a988-4a36-87df-271402451952: {role: 'assistant', hasContent: true, hasToolInvocations: false, toolCount: 0, isLoading: false}
chat.tsx:103 
            
            
           GET http://localhost:3000/api/chat?chatId=f0ad4d02-c5b3-48b8-8c4f-1c91d5cbca7f 404 (Not Found)
callChatApi @ call-chat-api.ts:47
useChat.useCallback2[triggerRequest] @ use-chat.ts:299
useChat.useCallback2[experimental_resume] @ use-chat.ts:472
Chat.useEffect @ chat.tsx:103
react-stack-bottom-frame @ react-dom-client.development.js:24035
runWithFiberInDEV @ react-dom-client.development.js:1510


commitDoubleInvokeEffectsInDEV @ react-dom-client.development.js:16035
flushPassiveEffects @ react-dom-client.development.js:15805
flushPendingEffects @ react-dom-client.development.js:15760
performSyncWorkOnRoot @ react-dom-client.development.js:16286
flushSyncWorkAcrossRoots_impl @ react-dom-client.development.js:16137
flushSpawnedWork @ react-dom-client.development.js:15664
commitRoot @ react-dom-client.development.js:15390
commitRootWhenReady @ react-dom-client.development.js:14643
performWorkOnRoot @ react-dom-client.development.js:14566
performWorkOnRootViaSchedulerTask @ react-dom-client.development.js:16274
performWorkUntilDeadline @ scheduler.development.js:45
"use client"
Page @ page.tsx:42
(anonymous) @ react-server-dom-turbopack-client.browser.development.js:2328
initializeModelChunk @ react-server-dom-turbopack-client.browser.development.js:1027
performWorkUntilDeadline @ scheduler.development.js:45
<Page>
buildFakeTask @ react-server-dom-turbopack-client.browser.development.js:2013
initializeFakeTask @ react-server-dom-turbopack-client.browser.development.js:2000
resolveDebugInfo @ react-server-dom-turbopack-client.browser.development.js:2036
processFullStringRow @ react-server-dom-turbopack-client.browser.development.js:2234
processFullBinaryRow @ react-server-dom-turbopack-client.browser.development.js:2206
progress @ react-server-dom-turbopack-client.browser.development.js:2452
"use server"
ResponseInstance @ react-server-dom-turbopack-client.browser.development.js:1560
createResponseFromOptions @ react-server-dom-turbopack-client.browser.development.js:2369
exports.createFromReadableStream @ react-server-dom-turbopack-client.browser.development.js:2681
createFromNextReadableStream @ fetch-server-response.ts:297
fetchServerResponse @ fetch-server-response.ts:226
await in fetchServerResponse
(anonymous) @ prefetch-cache-utils.ts:323
task @ promise-queue.ts:33
processNext @ promise-queue.ts:66
enqueue @ promise-queue.ts:46
createLazyPrefetchEntry @ prefetch-cache-utils.ts:322
getOrCreatePrefetchCacheEntry @ prefetch-cache-utils.ts:227
navigateReducer @ navigate-reducer.ts:216
clientReducer @ router-reducer.ts:32
action @ action-queue.ts:188
runAction @ action-queue.ts:76
dispatchAction @ action-queue.ts:141
dispatch @ action-queue.ts:186
(anonymous) @ use-reducer.ts:31
startTransition @ react-dom-client.development.js:6248
(anonymous) @ use-reducer.ts:30
(anonymous) @ app-router.tsx:201
(anonymous) @ app-router.tsx:328
exports.startTransition @ react.development.js:1127
push @ app-router.tsx:327
onClick @ chat.tsx:184
await in onClick
executeDispatch @ react-dom-client.development.js:16426
runWithFiberInDEV @ react-dom-client.development.js:1510
processDispatchQueue @ react-dom-client.development.js:16476
(anonymous) @ react-dom-client.development.js:17074
batchedUpdates$1 @ react-dom-client.development.js:3253
dispatchEventForPluginEventSystem @ react-dom-client.development.js:16630
dispatchEvent @ react-dom-client.development.js:20716
dispatchDiscreteEvent @ react-dom-client.development.js:20684Understand this error
hot-reloader-client.tsx:116 [Fast Refresh] done in 69ms
chat-header.tsx:58 Refreshed session data on mount: {knowledgeBaseId: null, processId: null}
hot-reloader-client.tsx:371 [Fast Refresh] rebuilding
chat.tsx:95 Error in useChat:
 No streams found
error @ intercept-console-error.ts:41
Chat.useChat @ chat.tsx:95
useChat.useCallback2[triggerRequest] @ use-chat.ts:366
await in useChat.useCallback2[triggerRequest]
useChat.useCallback2[experimental_resume] @ use-chat.ts:472
Chat.useEffect @ chat.tsx:103
react-stack-bottom-frame @ react-dom-client.development.js:24035
runWithFiberInDEV @ react-dom-client.development.js:1510
commitHookEffectListMount @ react-dom-client.development.js:10514
commitHookPassiveMountEffects @ react-dom-client.development.js:10635


commitDoubleInvokeEffectsInDEV @ react-dom-client.development.js:16035
flushPassiveEffects @ react-dom-client.development.js:15805
flushPendingEffects @ react-dom-client.development.js:15760
performSyncWorkOnRoot @ react-dom-client.development.js:16286
flushSyncWorkAcrossRoots_impl @ react-dom-client.development.js:16137
flushSpawnedWork @ react-dom-client.development.js:15664
commitRoot @ react-dom-client.development.js:15390
commitRootWhenReady @ react-dom-client.development.js:14643
performWorkOnRoot @ react-dom-client.development.js:14566
performWorkOnRootViaSchedulerTask @ react-dom-client.development.js:16274
performWorkUntilDeadline @ scheduler.development.js:45Understand this error
chat.tsx:96 Call stack:
 Error: No streams found
    at callChatApi (http://localhost:3000/_next/static/chunks/node_modules__pnpm_b29ed4ce._.js:3774:15)
    at async useChat.useCallback2[triggerRequest] (http://localhost:3000/_next/static/chunks/node_modules__pnpm_b29ed4ce._.js:6173:17)
error @ intercept-console-error.ts:41
Chat.useChat @ chat.tsx:96
useChat.useCallback2[triggerRequest] @ use-chat.ts:366
await in useChat.useCallback2[triggerRequest]
useChat.useCallback2[experimental_resume] @ use-chat.ts:472
Chat.useEffect @ chat.tsx:103
react-stack-bottom-frame @ react-dom-client.development.js:24035
runWithFiberInDEV @ react-dom-client.development.js:1510
commitHookEffectListMount @ react-dom-client.development.js:10514


Error 3, if I open a past chat the was here before the resumable stream feature was added I have the errors below, but I can continue the conversation without any problem:


GET http://localhost:3000/api/chat?chatId=6de4fcbf-2d04-4cdb-8cf9-3817f936e2e0 404 (Not Found)
callChatApi @ call-chat-api.ts:47
useChat.useCallback2[triggerRequest] @ use-chat.ts:299
useChat.useCallback2[experimental_resume] @ use-chat.ts:472
Chat.useEffect @ chat.tsx:103
react-stack-bottom-frame @ react-dom-client.development.js:24035
runWithFiberInDEV @ react-dom-client.development.js:1510
...
Page @ page.tsx:42
(anonymous) @ react-server-dom-turbopack-client.browser.development.js:2328
initializeModelChunk @ react-server-dom-turbopack-client.browser.development.js:1027
readChunk @ react-server-dom-turbopack-client.browser.development.js:922
react-stack-bottom-frame @ react-dom-client.development.js:24058
createChild @ react-dom-client.development.js:6871
reconcileChildrenArray @ react-dom-client.development.js:7178
reconcileChildFibersImpl @ react-dom-client.development.js:7501
(anonymous) @ react-dom-client.development.js:7606
reconcileChildren @ react-dom-client.development.js:8047
beginWork @ react-dom-client.development.js:10292
runWithFiberInDEV @ react-dom-client.development.js:1510
performUnitOfWork @ react-dom-client.development.js:15119
workLoopConcurrentByScheduler @ react-dom-client.development.js:15113
renderRootConcurrent @ react-dom-client.development.js:15088
performWorkOnRoot @ react-dom-client.development.js:14409
performWorkOnRootViaSchedulerTask @ react-dom-client.development.js:16274
performWorkUntilDeadline @ scheduler.development.js:45Understand this error
chat-header.tsx:58 



chat.tsx:95 Error in useChat:
 No streams found
error @ intercept-console-error.ts:41
Chat.useChat @ chat.tsx:95
useChat.useCallback2[triggerRequest] @ use-chat.ts:366
await in useChat.useCallback2[triggerRequest]
useChat.useCallback2[experimental_resume] @ use-chat.ts:472
Chat.useEffect @ chat.tsx:103
react-stack-bottom-frame @ react-dom-client.development.js:24035
runWithFiberInDEV @ react-dom-client.development.js:1510
commitHookEffectListMount @ react-dom-client.development.js:10514
...
recursivelyTraversePassiveMountEffects @ react-dom-client.development.js:12415
commitPassiveMountOnFiber @ react-dom-client.development.js:12434Understand this error
chat.tsx:96 Call stack:
 Error: No streams found
    at callChatApi (http://localhost:3000/_next/static/chunks/node_modules__pnpm_b29ed4ce._.js:3774:15)
    at async useChat.useCallback2[triggerRequest] (http://localhost:3000/_next/static/chunks/node_modules__pnpm_b29ed4ce._.js:6173:17)


chat.tsx:103 
            
            
           GET http://localhost:3000/api/chat?chatId=6de4fcbf-2d04-4cdb-8cf9-3817f936e2e0 404 (Not Found)
callChatApi @ call-chat-api.ts:47
useChat.useCallback2[triggerRequest] @ use-chat.ts:299
useChat.useCallback2[experimental_resume] @ use-chat.ts:472
Chat.useEffect @ chat.tsx:103
react-stack-bottom-frame @ react-dom-client.development.js:24035
runWithFiberInDEV @ react-dom-client.development.js:1510
commitHookEffectListMount @ react-dom-client.development.js:10514
commitHookPassiveMountEffects @ react-dom-client.development.js:10635
reconnectPassiveEffects @ react-dom-client.development.js:12604
recursivelyTraverseReconnectPassiveEffects @ react-dom-client.development.js:12576
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ react-dom-client.development.js:15993
commitDoubleInvokeEffectsInDEV @ react-dom-client.development.js:16035
flushPassiveEffects @ react-dom-client.development.js:15805
flushPendingEffects @ react-dom-client.development.js:15760
performSyncWorkOnRoot @ react-dom-client.development.js:16286
flushSyncWorkAcrossRoots_impl @ react-dom-client.development.js:16137
flushSpawnedWork @ react-dom-client.development.js:15664
commitRoot @ react-dom-client.development.js:15390
commitRootWhenReady @ react-dom-client.development.js:14643
performWorkOnRoot @ react-dom-client.development.js:14566
performWorkOnRootViaSchedulerTask @ react-dom-client.development.js:16274
performWorkUntilDeadline @ scheduler.development.js:45
"use client"
Page @ page.tsx:42
(anonymous) @ react-server-dom-turbopack-client.browser.development.js:2328
initializeModelChunk @ react-server-dom-turbopack-client.browser.development.js:1027
readChunk @ react-server-dom-turbopack-client.browser.development.js:922
react-stack-bottom-frame @ react-dom-client.development.js:24058
createChild @ react-dom-client.development.js:6871
reconcileChildrenArray @ react-dom-client.development.js:7178
reconcileChildFibersImpl @ react-dom-client.development.js:7501
(anonymous) @ react-dom-client.development.js:7606
reconcileChildren @ react-dom-client.development.js:8047
beginWork @ react-dom-client.development.js:10292
runWithFiberInDEV @ react-dom-client.development.js:1510
performUnitOfWork @ react-dom-client.development.js:15119
workLoopConcurrentByScheduler @ react-dom-client.development.js:15113
renderRootConcurrent @ react-dom-client.development.js:15088
performWorkOnRoot @ react-dom-client.development.js:14409
performWorkOnRootViaSchedulerTask @ react-dom-client.development.js:16274
performWorkUntilDeadline @ scheduler.development.js:45Understand this error
chat.tsx:95 Error in useChat:
 No streams found
error @ intercept-console-error.ts:41
Chat.useChat @ chat.tsx:95
useChat.useCallback2[triggerRequest] @ use-chat.ts:366
await in useChat.useCallback2[triggerRequest]
useChat.useCallback2[experimental_resume] @ use-chat.ts:472
Chat.useEffect @ chat.tsx:103
react-stack-bottom-frame @ react-dom-client.development.js:24035
runWithFiberInDEV @ react-dom-client.development.js:1510
commitHookEffectListMount @ react-dom-client.development.js:10514
commitHookPassiveMountEffects @ react-dom-client.development.js:10635
recursivelyTraverseAndDoubleInvokeEffectsInDEV @ react-dom-client.development.js:15993
commitDoubleInvokeEffectsInDEV @ react-dom-client.development.js:16035
flushPassiveEffects @ react-dom-client.development.js:15805
flushPendingEffects @ react-dom-client.development.js:15760
performSyncWorkOnRoot @ react-dom-client.development.js:16286
flushSyncWorkAcrossRoots_impl @ react-dom-client.development.js:16137
flushSpawnedWork @ react-dom-client.development.js:15664
commitRoot @ react-dom-client.development.js:15390
commitRootWhenReady @ react-dom-client.development.js:14643
performWorkOnRoot @ react-dom-client.development.js:14566
performWorkOnRootViaSchedulerTask @ react-dom-client.development.js:16274
performWorkUntilDeadline @ scheduler.development.js:45Understand this error
chat.tsx:96 Call stack:
 Error: No streams found
    at callChatApi (http://localhost:3000/_next/static/chunks/node_modules__pnpm_b29ed4ce._.js:3774:15)
    at async useChat.useCallback2[triggerRequest] (http://localhost:3000/_next/static/chunks/node_modules__pnpm_b29ed4ce._.js:6173:17)

don't make any change, identify the root cause and propose how it can be fixed