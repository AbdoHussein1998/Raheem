import pino, { type Logger, type LevelWithSilent } from 'pino';
import { createColoredOutput } from './colored-output';

/** Structured logger contract exposed by the existing shared logging service. */
export type LogMethod = {
    (message: string): void;
    (fields: Record<string, unknown>, message: string): void;
};

export interface ContextLogger {
    trace: LogMethod;
    debug: LogMethod;
    info: LogMethod;
    warn: LogMethod;
    error: LogMethod;
    fatal: LogMethod;
}


/** Configuration for the application's shared Pino logger. */
export interface LoggingConfig {
    /** Minimum severity level. Defaults to debug in development, info otherwise. */
    level?: LevelWithSilent;
    /** Human-readable output. Defaults to true outside production and tests. */
    pretty?: boolean;
    /** ANSI terminal colors in pretty mode. Defaults to true. */
    colorize?: boolean;
    /** Name used to identify this application in structured logs. */
    applicationName?: string;
}

/**
 * Framework-independent owner of a single configured Pino root logger.
 *
 * @remarks
 * This service can be instantiated in NestJS, a CLI, another framework,
 * or a background worker. Call `get_logger()` to obtain immutable child
 * loggers with separate contexts; never mutate a shared logger context.
 *
 * The root logger is shared per LoggingService instance, not globally
 * across multiple Node.js processes or application containers.
 */
export class LoggingService {
    private constructor(private readonly root: Logger) {}

    /**
     * Create the logging service for one application process.
     *
     * @param config - Pino configuration and development formatting options.
     * @returns A service holding the configured Pino root logger.
     */
    public static init_class(config: LoggingConfig = {}): LoggingService {
        const isProduction = process.env.NODE_ENV === 'production';
        const isTest = process.env.NODE_ENV === 'test';
        const pretty = config.pretty ?? (!isProduction && !isTest);

        const options: pino.LoggerOptions = {
            level: config.level ?? (isProduction ? 'info' : 'debug'),
            base: { application: config.applicationName ?? 'Al-Hakim Application' },
            timestamp: pino.stdTimeFunctions.isoTime,
            // Never intentionally print common credentials or HTTP auth data.
            redact: {
                paths: [
                    'password', '*.password', 'config.password',
                    'token', '*.token', 'secret', '*.secret',
                    'req.headers.authorization', 'req.headers.cookie',
                    'headers.authorization', 'headers.cookie',
                ],
                censor: '[REDACTED]',
            },
            serializers: { err: pino.stdSerializers.err },
        };

        // Pretty-print only for interactive development; production uses
        // newline-delimited JSON for log aggregation and indexing.
        const destination = pretty
            ? createColoredOutput(process.stdout, config.colorize ?? true)
            : process.stdout;

        return new LoggingService(pino(options, destination));
    }

    /**
     * Return the shared Pino root logger for integrations like pino-http.
     *
     * @returns The same underlying Pino instance on every call.
     */
    public get_root_logger(): Logger {
        return this.root;
    }

    /**
     * Create a lightweight, context-labelled child of the shared logger.
     *
     * @param context - Service or component name shown beside every log.
     * @returns A Pino child logger with independent context bindings.
     */
    public get_logger(context: string): ContextLogger {
        if (!context.trim()) {
            throw new Error('Logger context must not be empty');
        }
        return this.root.child({ context });
    }
}
