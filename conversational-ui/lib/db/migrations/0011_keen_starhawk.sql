ALTER TABLE "Chat" ALTER COLUMN "spaceId" SET NOT NULL;--> statement-breakpoint
ALTER TABLE "User" ADD COLUMN "hasCompletedOnboarding" boolean DEFAULT false NOT NULL;--> statement-breakpoint
ALTER TABLE "User" ADD COLUMN "profileNotes" text;