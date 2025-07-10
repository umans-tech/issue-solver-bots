CREATE TABLE "token_usage" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"message_id" uuid NOT NULL,
	"provider" varchar(50) NOT NULL,
	"model" varchar(100) NOT NULL,
	"raw_usage_data" jsonb NOT NULL,
	"provider_metadata" jsonb,
	"created_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
ALTER TABLE "token_usage" ADD CONSTRAINT "token_usage_message_id_Message_v2_id_fk" FOREIGN KEY ("message_id") REFERENCES "public"."Message_v2"("id") ON DELETE no action ON UPDATE no action;