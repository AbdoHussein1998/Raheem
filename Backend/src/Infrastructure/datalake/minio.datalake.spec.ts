import * as Minio from 'minio';
import { MinioDataLake } from './minio.datalake';

jest.mock('minio', () => ({ Client: jest.fn() }));

describe('MinioDataLake automatic bucket initialization', () => {
    const env = {
        MINIO_ENDPOINT: 'minio',
        MINIO_PORT: '9000',
        MINIO_USE_SSL: 'false',
        MINIO_API_KEY: 'test-access-key',
        MINIO_SECERT: 'test-secret-key',
        MINIO_BUCKET: 'generated-photos',
    };
    const originalEnv = Object.fromEntries(
        Object.keys(env).map((key) => [key, process.env[key]]),
    );
    const sdk = {
        bucketExists: jest.fn(),
        makeBucket: jest.fn(),
        putObject: jest.fn(),
    };

    beforeEach(() => {
        jest.resetAllMocks();
        Object.assign(process.env, env);
        (Minio.Client as unknown as jest.Mock).mockImplementation(() => sdk);
        sdk.bucketExists.mockResolvedValue(true);
        sdk.makeBucket.mockResolvedValue(undefined);
        sdk.putObject.mockResolvedValue(undefined);
    });

    afterAll(() => {
        for (const [key, value] of Object.entries(originalEnv)) {
            if (value === undefined) delete process.env[key];
            else process.env[key] = value;
        }
    });

    it('reuses an existing bucket for multiple uploads', async () => {
        const lake = new MinioDataLake();
        await lake.uploadObject('photos/a/image.jpg', Buffer.from('image'), 'image/jpeg');
        await lake.uploadObject('photos/a/index.html', Buffer.from('html'), 'text/html');
        expect(sdk.bucketExists).toHaveBeenCalledTimes(1);
        expect(sdk.makeBucket).not.toHaveBeenCalled();
        expect(sdk.putObject).toHaveBeenCalledTimes(2);
    });

    it('creates a missing bucket on first upload', async () => {
        sdk.bucketExists.mockResolvedValueOnce(false);
        const lake = new MinioDataLake();
        await lake.uploadObject('photos/a/image.jpg', Buffer.from('image'), 'image/jpeg');
        expect(sdk.makeBucket).toHaveBeenCalledWith('generated-photos');
        expect(sdk.putObject).toHaveBeenCalledTimes(1);
    });

    it('shares initialization across concurrent uploads', async () => {
        const lake = new MinioDataLake();
        await Promise.all([
            lake.uploadObject('photos/a/image.jpg', Buffer.from('image'), 'image/jpeg'),
            lake.uploadObject('photos/a/index.html', Buffer.from('html'), 'text/html'),
        ]);
        expect(sdk.bucketExists).toHaveBeenCalledTimes(1);
        expect(sdk.putObject).toHaveBeenCalledTimes(2);
    });

    it('retries initialization after a temporary failure', async () => {
        sdk.bucketExists.mockRejectedValueOnce(new Error('MinIO unavailable'));
        const lake = new MinioDataLake();
        await expect(lake.uploadObject('photos/a/1', Buffer.from('one'), 'text/plain')).rejects.toThrow('MinIO unavailable');
        await lake.uploadObject('photos/a/2', Buffer.from('two'), 'text/plain');
        expect(sdk.bucketExists).toHaveBeenCalledTimes(2);
    });
});
