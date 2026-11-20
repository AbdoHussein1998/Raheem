import { Writable } from 'node:stream';

/**
 * Lightweight terminal formatter for Pino's newline-delimited JSON output.
 *
 * @remarks
 * This adapter is intentionally independent of NestJS and requires no
 * additional runtime package. Production logs bypass it and remain JSON.
 * It is a presentation layer, not the source of logging semantics.
 */
export function createColoredOutput(
    destination: NodeJS.WritableStream = process.stdout,
    colorize = true,
): Writable {
    const colors = {
        reset: '\u001b[0m',
        dim: '\u001b[2m',
        trace: '\u001b[90m',
        debug: '\u001b[36m',
        info: '\u001b[32m',
        warn: '\u001b[33m',
        error: '\u001b[31m',
        fatal: '\u001b[35m',
    } as const;

    const levelNames: Record<number, keyof typeof colors> = {
        10: 'trace',
        20: 'debug',
        30: 'info',
        40: 'warn',
        50: 'error',
        60: 'fatal',
    };

    /** Apply terminal color only when the caller requests it. */
    const paint = (value: string, color: keyof typeof colors): string =>
        colorize ? `${colors[color]}${value}${colors.reset}` : value;

    /** Format a single Pino record, preserving structured extra fields. */
    const format = (line: string): string => {
        try {
            const record = JSON.parse(line) as Record<string, unknown>;
            if (typeof record.level !== 'number') return line;

            const level = levelNames[record.level] ?? 'info';
            const stamp = typeof record.time === 'string'
                ? record.time
                : typeof record.time === 'number'
                    ? new Date(record.time).toISOString()
                    : new Date().toISOString();
            const context = typeof record.context === 'string'
                ? `[${record.context}] `
                : '';
            const message = typeof record.msg === 'string' ? record.msg : '';

            // Pino owns the structured data. We only hide metadata in the
            // human-readable rendering; the original JSON is untouched.
            const { level: _level, time: _time, msg: _msg,
                context: _context, pid: _pid, hostname: _hostname,
                application: _application, ...extra } = record;
            const details = Object.keys(extra).length > 0
                ? ` ${JSON.stringify(extra)}`
                : '';

            return `${paint(stamp, 'dim')} ${paint(level.toUpperCase().padEnd(5), level)} ${paint(context, 'debug')}${message}${details}`;
        } catch {
            // Do not lose a log entry if a line is not valid JSON.
            return line;
        }
    };

    // Stream chunks do not have to align with newline boundaries.
    let pending = '';
    return new Writable({
        write(chunk: Buffer | string, _encoding, callback) {
            try {
                pending += chunk.toString();
                const lines = pending.split('\n');
                pending = lines.pop() ?? '';
                for (const line of lines) {
                    if (line) destination.write(`${format(line)}\n`);
                }
                callback();
            } catch (error) {
                callback(error as Error);
            }
        },
        final(callback) {
            if (pending) destination.write(`${format(pending)}\n`);
            pending = '';
            callback();
        },
    });
}
