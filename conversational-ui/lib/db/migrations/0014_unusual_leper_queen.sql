CREATE TABLE "UserMemory" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"userId" uuid NOT NULL,
	"spaceId" uuid NOT NULL,
	"content" text DEFAULT '' NOT NULL,
	"summary" text DEFAULT '' NOT NULL,
	"createdAt" timestamp DEFAULT now() NOT NULL,
	"updatedAt" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
ALTER TABLE "UserMemory" ADD CONSTRAINT "UserMemory_userId_User_id_fk" FOREIGN KEY ("userId") REFERENCES "public"."User"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "UserMemory" ADD CONSTRAINT "UserMemory_spaceId_Space_id_fk" FOREIGN KEY ("spaceId") REFERENCES "public"."Space"("id") ON DELETE no action ON UPDATE no action;