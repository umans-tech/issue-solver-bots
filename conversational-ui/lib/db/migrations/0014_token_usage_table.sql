CREATE TABLE IF NOT EXISTS "token_usage" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"user_id" text NOT NULL,
	"space_id" text,
	"message_id" uuid NOT NULL,
	"chat_id" text,
	"provider" text NOT NULL,
	"model" text NOT NULL,
	"operation_type" text NOT NULL,
	"operation_id" text,
	"raw_usage_data" jsonb NOT NULL,
	"provider_metadata" jsonb,
	"finish_reason" text,
	"request_id" text,
	"created_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
DO $$ BEGIN
 ALTER TABLE "token_usage" ADD CONSTRAINT "token_usage_message_id_Message_v2_id_fk" FOREIGN KEY ("message_id") REFERENCES "Message_v2"("id") ON DELETE no action ON UPDATE no action;
EXCEPTION
 WHEN duplicate_object THEN null;
END $$;