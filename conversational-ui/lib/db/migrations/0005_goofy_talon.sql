CREATE TABLE "Space" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"name" text NOT NULL,
	"knowledgeBaseId" text,
	"processId" text,
	"createdAt" timestamp DEFAULT now() NOT NULL,
	"updatedAt" timestamp DEFAULT now() NOT NULL,
	"isDefault" boolean DEFAULT false NOT NULL
);
--> statement-breakpoint
CREATE TABLE "SpaceToUser" (
	"spaceId" uuid NOT NULL,
	"userId" uuid NOT NULL,
	CONSTRAINT "SpaceToUser_spaceId_userId_pk" PRIMARY KEY("spaceId","userId")
);
--> statement-breakpoint
ALTER TABLE "User" ADD COLUMN "selectedSpaceId" uuid;--> statement-breakpoint
ALTER TABLE "SpaceToUser" ADD CONSTRAINT "SpaceToUser_spaceId_Space_id_fk" FOREIGN KEY ("spaceId") REFERENCES "public"."Space"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "SpaceToUser" ADD CONSTRAINT "SpaceToUser_userId_User_id_fk" FOREIGN KEY ("userId") REFERENCES "public"."User"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "User" ADD CONSTRAINT "User_selectedSpaceId_Space_id_fk" FOREIGN KEY ("selectedSpaceId") REFERENCES "public"."Space"("id") ON DELETE no action ON UPDATE no action;