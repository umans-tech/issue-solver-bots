import {PutObjectCommand, S3Client} from '@aws-sdk/client-s3';
import {NextResponse} from 'next/server';
import {z} from 'zod';

import {auth} from '@/app/(auth)/auth';

const FileSchema = z.object({
    file: z
        .instanceof(Blob)
        .refine((file) => file.size <= 5 * 1024 * 1024, {
            message: 'File size should be less than 5MB',
        })
        .refine((file) => ['image/jpeg', 'image/png'].includes(file.type), {
            message: 'File type should be JPEG or PNG',
        }),
});

export async function POST(request: Request) {
    const session = await auth();

    if (!session) {
        return NextResponse.json({error: 'Unauthorized'}, {status: 401});
    }

    if (request.body === null) {
        return new Response('Request body is empty', {status: 400});
    }

    try {
        const formData = await request.formData();
        const file = formData.get('file') as Blob;

        if (!file) {
            return NextResponse.json({error: 'No file uploaded'}, {status: 400});
        }

        const validatedFile = FileSchema.safeParse({file});

        if (!validatedFile.success) {
            const errorMessage = validatedFile.error.errors
                .map((error) => error.message)
                .join(', ');

            return NextResponse.json({error: errorMessage}, {status: 400});
        }

        // Get filename from formData since Blob doesn't have name property
        const filename = (formData.get('file') as File).name;
        const fileBuffer = await file.arrayBuffer();

        // Initialize S3 client
        const s3Client = new S3Client({
            region: process.env.BLOB_REGION || '',
            // Remove the endpoint for direct S3 access
            credentials: {
                accessKeyId: process.env.BLOB_ACCESS_KEY_ID || '',
                secretAccessKey: process.env.BLOB_READ_WRITE_TOKEN || '',
            },
        });

        const BUCKET_NAME = process.env.BLOB_BUCKET_NAME || '';

        try {
            // Upload to S3
            const command = new PutObjectCommand({
                Bucket: BUCKET_NAME,
                Key: filename,
                Body: Buffer.from(fileBuffer),
                ContentType: file.type,
            });

            await s3Client.send(command);

            // Construct the URL with the proper S3 URL format
            const s3Url = `https://${BUCKET_NAME}.s3.${process.env.BLOB_REGION}.amazonaws.com/${filename}`;

            // Return the data structure
            const data = {
                url: s3Url,
                pathname: filename,
                contentType: file.type,
                size: file.size,
            };

            return NextResponse.json(data);
        } catch (error) {
            console.error('Upload failed:', error);
            return NextResponse.json({error: 'Upload failed'}, {status: 500});
        }
    } catch (error) {
        return NextResponse.json(
            {error: 'Failed to process request'},
            {status: 500},
        );
    }
}