CREATE TABLE "TokenUsage" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"userId" uuid NOT NULL,
	"spaceId" uuid NOT NULL,
	"messageId" uuid NOT NULL,
	"chatId" uuid NOT NULL,
	"provider" varchar(50) NOT NULL,
	"model" varchar(100) NOT NULL,
	"operationType" varchar(50) NOT NULL,
	"operationId" varchar(255),
	"rawUsageData" jsonb NOT NULL,
	"providerMetadata" jsonb,
	"finishReason" varchar(50),
	"requestId" varchar(255),
	"createdAt" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
ALTER TABLE "TokenUsage" ADD CONSTRAINT "TokenUsage_userId_User_id_fk" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "TokenUsage" ADD CONSTRAINT "TokenUsage_spaceId_Space_id_fk" FOREIGN KEY ("spaceId") REFERENCES "Space"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "TokenUsage" ADD CONSTRAINT "TokenUsage_messageId_Message_v2_id_fk" FOREIGN KEY ("messageId") REFERENCES "Message_v2"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "TokenUsage" ADD CONSTRAINT "TokenUsage_chatId_Chat_id_fk" FOREIGN KEY ("chatId") REFERENCES "Chat"("id") ON DELETE no action ON UPDATE no action;