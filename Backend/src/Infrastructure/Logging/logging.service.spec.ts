import { LoggingService } from './logging.service';

/** Verifies shared Pino instances and isolated child contexts. */
describe('LoggingService', () => {
    it('reuses one root while returning context-specific child loggers', () => {
        const logging = LoggingService.init_class({
            level: 'silent',
            pretty: false,
        });
        const root = logging.get_root_logger();
        const redirect = logging.get_logger('RedirectService');
        const postgres = logging.get_logger('PostgresDML');

        expect(logging.get_root_logger()).toBe(root);
        // Inspect the Pino adapter only in the logging integration test.
        const bindings = (logger: unknown): Record<string, unknown> =>
            (logger as { bindings(): Record<string, unknown> }).bindings();
        expect(bindings(redirect).context).toBe('RedirectService');
        expect(bindings(postgres).context).toBe('PostgresDML');
        expect(redirect).not.toBe(postgres);
    });

    it('rejects empty context names', () => {
        const logging = LoggingService.init_class({ level: 'silent', pretty: false });
        expect(() => logging.get_logger(' ')).toThrow('Logger context must not be empty');
    });
});
