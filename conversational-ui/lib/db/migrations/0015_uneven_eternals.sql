ALTER TABLE "User" ADD COLUMN "plan" varchar(32) DEFAULT 'free' NOT NULL;--> statement-breakpoint
ALTER TABLE "User" ADD COLUMN "subscriptionStatus" varchar(32);--> statement-breakpoint
ALTER TABLE "User" ADD COLUMN "stripeCustomerId" varchar(255);