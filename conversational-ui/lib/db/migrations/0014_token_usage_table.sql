CREATE TABLE IF NOT EXISTS "TokenUsage" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"chatId" uuid NOT NULL,
	"userId" uuid NOT NULL,
	"spaceId" uuid,
	"model" varchar(255) NOT NULL,
	"provider" varchar(100) NOT NULL,
	"promptTokens" integer,
	"completionTokens" integer,
	"totalTokens" integer,
	"reasoningTokens" integer,
	"thinkingTokens" integer,
	"thinkingBudgetTokens" integer,
	"cachedTokens" integer,
	"cacheCreationTokens" integer,
	"cacheReadTokens" integer,
	"rawUsageData" json,
	"createdAt" timestamp DEFAULT now() NOT NULL
);

DO $$ BEGIN
 ALTER TABLE "TokenUsage" ADD CONSTRAINT "TokenUsage_chatId_Chat_id_fk" FOREIGN KEY ("chatId") REFERENCES "Chat"("id") ON DELETE no action ON UPDATE no action;
EXCEPTION
 WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
 ALTER TABLE "TokenUsage" ADD CONSTRAINT "TokenUsage_userId_User_id_fk" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE no action ON UPDATE no action;
EXCEPTION
 WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
 ALTER TABLE "TokenUsage" ADD CONSTRAINT "TokenUsage_spaceId_Space_id_fk" FOREIGN KEY ("spaceId") REFERENCES "Space"("id") ON DELETE no action ON UPDATE no action;
EXCEPTION
 WHEN duplicate_object THEN null;
END $$;