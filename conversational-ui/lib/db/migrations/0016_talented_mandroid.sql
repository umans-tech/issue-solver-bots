CREATE TABLE "WaitlistSignups" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"waitlistId" text NOT NULL,
	"email" varchar(255) NOT NULL,
	"role" text,
	"goal" text,
	"reposCount" text,
	"needVpc" boolean,
	"repoLink" text,
	"utmSource" text,
	"utmMedium" text,
	"utmCampaign" text,
	"utmContent" text,
	"utmTerm" text,
	"referrer" text,
	"pagePath" text,
	"createdAt" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX "unique_waitlist_email" ON "WaitlistSignups" USING btree ("waitlistId","email");