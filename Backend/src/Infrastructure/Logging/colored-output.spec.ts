import { Writable } from 'node:stream';
import { createColoredOutput } from './colored-output';

/** Verifies colored console formatting without opening a network connection. */
describe('createColoredOutput', () => {
    it('formats colored Pino records and handles split stream chunks', async () => {
        const chunks: string[] = [];
        const destination = new Writable({
            write(chunk, _encoding, callback) {
                chunks.push(chunk.toString());
                callback();
            },
        });
        const output = createColoredOutput(destination);
        // Split input inside the JSON record to validate line buffering.
        output.write('{"level":30,"time":"2026-10-19T10:00:00Z",');
        output.write('"context":"WelcomeService","msg":"Hello"}\n');
        output.end();
        await new Promise<void>((resolve) => output.on('finish', resolve));

        const text = chunks.join('');
        expect(text).toContain('WelcomeService');
        expect(text).toContain('Hello');
        expect(text).toContain('\u001b[32m'); // Green INFO level.
    });

    it('can disable colors and preserves structured detail fields', async () => {
        const chunks: string[] = [];
        const destination = new Writable({
            write(chunk, _encoding, callback) {
                chunks.push(chunk.toString());
                callback();
            },
        });
        const output = createColoredOutput(destination, false);
        output.end('{"level":50,"msg":"Failure","errorCode":"E_FAIL"}\n');
        await new Promise<void>((resolve) => output.on('finish', resolve));

        expect(chunks.join('')).not.toContain('\u001b[');
        expect(chunks.join('')).toContain('"errorCode":"E_FAIL"');
    });
});
