import * as Minio from 'minio';
import type { DataLakeInterface } from './datalake.interface';

/**
 * MinIO implementation of generic object storage.
 *
 * Configuration and client creation are lazy so a temporary MinIO outage or
 * missing MinIO environment variables never stop AI image generation at startup.
 * The configured bucket is created on first upload if missing. It stays private:
 * only NestJS reads image and HTML objects for public delivery.
 */
export class MinioDataLake implements DataLakeInterface {
    // Bound object reads to prevent a malformed or unexpectedly large object
    // from exhausting backend memory when serving a public photo.
    private static readonly MAX_OBJECT_READ_BYTES = 25 * 1024 * 1024;

    private client?: Minio.Client;

    // Coalesce concurrent first uploads and allow retry if initialization fails.
    private bucketInitialization?: Promise<void>;

    async uploadObject(key: string, bytes: Buffer, contentType: string): Promise<void> {
        this.assertObjectKey(key);
        if (!Buffer.isBuffer(bytes) || bytes.length === 0) {
            throw new Error('Object content must be a nonempty Buffer');
        }
        await this.ensureBucketReady();
        await this.getClient().putObject(this.bucket(), key, bytes, bytes.length, {
            'Content-Type': contentType,
            'Content-Disposition': 'inline',
            'Cache-Control': 'public, max-age=300',
        });
    }

    async objectExists(key: string): Promise<boolean> {
        this.assertObjectKey(key);
        try {
            await this.getClient().statObject(this.bucket(), key);
            return true;
        } catch (error) {
            // An absent object is not an infrastructure failure. Authentication,
            // connectivity and bucket errors must propagate to the caller (503).
            const code = this.errorCode(error);
            if (code === 'NoSuchKey' || code === 'NoSuchObject') {
                return false;
            }
            if (code === 'NotFound') {
                // Some S3 gateways report the same generic 404 for a missing
                // bucket and a missing object; the former is a 503 condition.
                if (!(await this.getClient().bucketExists(this.bucket()))) {
                    throw new Error('Configured MinIO bucket does not exist');
                }
                return false;
            }
            throw error;
        }
    }

    async getObject(key: string): Promise<Buffer> {
        this.assertObjectKey(key);
        const stream = await this.getClient().getObject(this.bucket(), key);
        const chunks: Buffer[] = [];
        let totalBytes = 0;
        for await (const chunk of stream) {
            const bytes = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk);
            totalBytes += bytes.length;
            if (totalBytes > MinioDataLake.MAX_OBJECT_READ_BYTES) {
                stream.destroy();
                throw new Error('Stored object exceeds the maximum permitted response size');
            }
            chunks.push(bytes);
        }
        if (totalBytes === 0) throw new Error('Stored object is empty');
        return Buffer.concat(chunks, totalBytes);
    }

    async deleteObject(key: string): Promise<void> {
        this.assertObjectKey(key);
        await this.getClient().removeObject(this.bucket(), key);
    }

    /** Check/create the bucket once per running instance, without a startup dependency. */
    private async ensureBucketReady(): Promise<void> {
        if (!this.bucketInitialization) {
            const initialization = this.ensureBucketExists();
            this.bucketInitialization = initialization;

            // MinIO may recover after an outage; the next upload should retry.
            void initialization.catch(() => {
                if (this.bucketInitialization === initialization) {
                    this.bucketInitialization = undefined;
                }
            });
        }
        await this.bucketInitialization;
    }

    private async ensureBucketExists(): Promise<void> {
        const client = this.getClient();
        const bucket = this.bucket();
        if (await client.bucketExists(bucket)) return;

        try {
            await client.makeBucket(bucket);
        } catch (error) {
            // Another replica could have created the bucket concurrently.
            if (await client.bucketExists(bucket)) return;
            throw error;
        }
    }

    private getClient(): Minio.Client {
        if (!this.client) {
            const endPoint = this.requiredEnv('MINIO_ENDPOINT');
            if (!/^[a-z\d._-]+$/i.test(endPoint)) {
                throw new Error('MINIO_ENDPOINT must be a hostname, without scheme or port');
            }
            const port = Number(this.requiredEnv('MINIO_PORT'));
            if (!Number.isInteger(port) || port < 1 || port > 65535) {
                throw new Error('MINIO_PORT must be a valid port number');
            }
            const useSsl = this.requiredEnv('MINIO_USE_SSL');
            if (useSsl !== 'true' && useSsl !== 'false') {
                throw new Error('MINIO_USE_SSL must be true or false');
            }
            this.client = new Minio.Client({
                endPoint,
                port,
                useSSL: useSsl === 'true',
                accessKey: this.requiredEnv('MINIO_API_KEY'),
                // Preserve the environment variable name previously agreed upon.
                secretKey: this.requiredEnv('MINIO_SECERT'),
            });
        }
        return this.client;
    }

    private bucket(): string {
        const bucket = this.requiredEnv('MINIO_BUCKET');
        if (!/^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$/.test(bucket)) {
            throw new Error('MINIO_BUCKET is not a valid bucket name');
        }
        return bucket;
    }

    private assertObjectKey(key: string): void {
        if (!key || key.startsWith('/') || key.includes('\\') || key.split('/').some((part) => !part || part === '.' || part === '..')) {
            throw new Error('Invalid object key');
        }
    }

    private requiredEnv(name: string): string {
        const value = process.env[name]?.trim();
        if (!value) throw new Error(`${name} is required`);
        return value;
    }

    private errorCode(error: unknown): string | undefined {
        if (typeof error !== 'object' || error === null) return undefined;
        if (!('code' in error)) return undefined;
        return typeof error.code === 'string' ? error.code : undefined;
    }
}
