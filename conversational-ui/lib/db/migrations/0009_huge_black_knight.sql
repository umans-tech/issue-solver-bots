ALTER TABLE "User" ADD COLUMN "emailVerified" timestamp;--> statement-breakpoint
ALTER TABLE "User" ADD COLUMN "emailVerificationToken" varchar(255);--> statement-breakpoint
UPDATE "User" SET "emailVerified" = NOW() WHERE "emailVerified" IS NULL;