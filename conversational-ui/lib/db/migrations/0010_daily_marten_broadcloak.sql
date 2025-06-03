ALTER TABLE "Chat" ADD COLUMN "spaceId" uuid;--> statement-breakpoint
ALTER TABLE "Chat" ADD CONSTRAINT "Chat_spaceId_Space_id_fk" FOREIGN KEY ("spaceId") REFERENCES "public"."Space"("id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint

-- Link existing chats to their user's default space
UPDATE "Chat" 
SET "spaceId" = (
  SELECT s."id" 
  FROM "Space" s 
  JOIN "SpaceToUser" stu ON s."id" = stu."spaceId" 
  WHERE stu."userId" = "Chat"."userId" 
  AND s."isDefault" = true 
  LIMIT 1
)
WHERE "spaceId" IS NULL;