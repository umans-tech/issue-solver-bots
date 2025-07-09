CREATE TABLE "token_usage" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"user_id" varchar(255) NOT NULL,
	"space_id" varchar(255) NOT NULL,
	"chat_id" varchar(255),
	"provider" varchar(50) NOT NULL,
	"model" varchar(100) NOT NULL,
	"input_tokens" varchar DEFAULT '0' NOT NULL,
	"output_tokens" varchar DEFAULT '0' NOT NULL,
	"total_tokens" varchar DEFAULT '0' NOT NULL,
	"cost_usd" varchar DEFAULT '0' NOT NULL,
	"operation_type" varchar(50) NOT NULL,
	"operation_id" varchar(255),
	"created_at" timestamp DEFAULT now() NOT NULL
);