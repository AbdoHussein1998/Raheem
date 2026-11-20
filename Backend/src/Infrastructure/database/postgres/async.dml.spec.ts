import type { QueryRunner } from 'typeorm';
import type { ContextLogger } from '../../logging/logging.service';
import type { PostgresConnectionManager } from './async.connection';
import { PostgresDML } from './async.dml';

describe('PostgresDML atomic conditional decrement', () => {
    const query = jest.fn();
    const runner = {
        connect: jest.fn().mockResolvedValue(undefined),
        query,
        release: jest.fn().mockResolvedValue(undefined),
        isReleased: false,
    } as unknown as QueryRunner;
    const manager = {
        getAppDataSource: () => ({ isInitialized: true, createQueryRunner: () => runner }),
    } as unknown as PostgresConnectionManager;
    const logger = { info: jest.fn(), error: jest.fn() } as unknown as ContextLogger;
    let dml: PostgresDML;

    beforeEach(async () => {
        query.mockReset();
        dml = await PostgresDML.init_class(manager, logger);
    });

    it('runs one parameterized, atomic statement using generic quoted identifiers', async () => {
        query.mockResolvedValue([{ matchingRows: 1, affectedRows: 1 }]);
        await expect(dml.decrement_positive_integer_column('codes', 'code', 'uuid-123', 'count', 'public'))
            .resolves.toEqual({ matchingRows: 1, affectedRows: 1 });
        expect(query).toHaveBeenCalledTimes(1);
        const [sql, params] = query.mock.calls[0];
        expect(sql).toContain('UPDATE "public"."codes"');
        expect(sql).toContain('SET "count" = "count" - 1');
        expect(sql).toContain('"count" > 0');
        expect(sql).toContain('COUNT(*) FROM matching');
        expect(params).toEqual(['uuid-123']);
    });

    it('reports no update for an exhausted key', async () => {
        query.mockResolvedValue([{ matchingRows: 1, affectedRows: 0 }]);
        await expect(dml.decrement_positive_integer_column('codes', 'code', 'uuid-123', 'count', 'public'))
            .resolves.toEqual({ matchingRows: 1, affectedRows: 0 });
    });

    it('reports duplicate key rows without decrementing them', async () => {
        query.mockResolvedValue([{ matchingRows: 2, affectedRows: 0 }]);
        await expect(dml.decrement_positive_integer_column('codes', 'code', 'uuid-123', 'count', 'public'))
            .resolves.toEqual({ matchingRows: 2, affectedRows: 0 });
    });

    it('rejects null keys before reaching the database', async () => {
        await expect(dml.decrement_positive_integer_column('codes', 'code', null, 'count', 'public'))
            .rejects.toThrow('Key value is required');
        expect(query).not.toHaveBeenCalled();
    });
});
