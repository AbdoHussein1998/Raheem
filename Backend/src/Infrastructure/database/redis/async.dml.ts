import { WatchError } from 'redis';
import type { ContextLogger } from '../../logging/logging.service';

import { RedisConnectionManager } from './async.connection';
import type { InfrastructureFactoryInterface } from '../interfaces/factory.interface';

/** A Redis hash where each field is stored as a JSON-encoded string. */
export type RedisDocument = Record<string, unknown>;

type RedisClient = ReturnType<RedisConnectionManager['get_client']>;
type PreparedDocument = { key: string; fields: Record<string, string> };

/**
 * Implements reusable Redis hash operations without depending on NestJS.
 *
 * @remarks
 * - RedisConnectionManager owns all sockets and the bounded WATCH pool.
 * - Reads use bounded pipelines, rather than one transaction per document.
 * - Conditional writes use WATCH + one MULTI/EXEC per batch, without Lua.
 * - Each field is JSON encoded; the public storage format is unchanged.
 * - Bulk writes commit one batch at a time, not all batches atomically.
 */
export class RedisDML {
    private readonly client: RedisClient;
    private static readonly MAX_WATCH_RETRIES = 3;
    private static readonly MAX_BATCH_SIZE = 1_000;

    /**
     * Construct a DML helper using an existing Redis manager.
     *
     * @param manager - Owner of the shared Redis client and isolated pool.
     * @param logger - Contextual logger supplied by the composition module.
     */
    private constructor(
        private readonly manager: RedisConnectionManager,
        private readonly logger: ContextLogger,
    ) {
        this.client = manager.get_client();
    }

    // ======================================================
    // 1. FACTORY INITIALIZATION
    // ======================================================

    /**
     * Create a data-access helper after checking the shared Redis connection.
     *
     * @param manager - An already initialized connection manager.
     * @param logger - Contextual logger supplied by the composition module.
     * @returns A ready-to-use RedisDML instance.
     * @throws If the manager's Redis client fails its health check.
     */
    public static async init_class(
        manager: RedisConnectionManager,
        logger: ContextLogger,
    ): Promise<RedisDML> {
        if (!(await manager.ensure_connected())) {
            throw new Error('Redis connection is not ready');
        }
        return new RedisDML(manager, logger);
    }

    // ======================================================
    // 2. VALIDATION & SERIALIZATION
    // ======================================================

    /** Require a positive integer for TTL and batch-size arguments. */
    private static validate_positive(value: number, name: string): void {
        if (!Number.isSafeInteger(value) || value <= 0) {
            throw new RangeError(`${name} must be a positive integer`);
        }
    }

    /** Limit batch size so one operation cannot queue unbounded commands. */
    private static validate_batch_size(size: number): void {
        RedisDML.validate_positive(size, 'Batch size');
        if (size > RedisDML.MAX_BATCH_SIZE) {
            throw new RangeError(`Batch size cannot exceed ${RedisDML.MAX_BATCH_SIZE}`);
        }
    }

    /** Reject invalid keys before any writes are submitted. */
    private static validate_key(key: string): void {
        if (typeof key !== 'string' || key.length === 0) {
            throw new TypeError('Redis key must be a nonempty string');
        }
    }

    /**
     * Serialize a nonempty document to values suitable for Redis HSET.
     *
     * @throws For empty documents or values JSON cannot represent.
     */
    private static serialize_document(document: RedisDocument): Record<string, string> {
        if (document === null || typeof document !== 'object' || Array.isArray(document)) {
            throw new TypeError('Document must be a plain record');
        }

        const entries = Object.entries(document);
        if (entries.length === 0) {
            throw new Error('Document cannot be empty');
        }

        const fields: Record<string, string> = Object.create(null);
        for (const [field, value] of entries) {
            if (field.length === 0) {
                throw new TypeError('Document fields cannot be empty');
            }
            const serialized = JSON.stringify(value);
            if (serialized === undefined) {
                throw new TypeError(`Invalid JSON value for field: ${field}`);
            }
            fields[field] = serialized;
        }
        return fields;
    }

    /** Decode a hash and enrich JSON errors with key/field context. */
    private static deserialize_document(
        key: string,
        values: Record<string, string>,
    ): RedisDocument | null {
        if (Object.keys(values).length === 0) return null;

        const entries: Array<[string, unknown]> = [];
        for (const [field, serialized] of Object.entries(values)) {
            try {
                entries.push([field, JSON.parse(serialized)]);
            } catch (error) {
                throw new SyntaxError(
                    `Invalid JSON in Redis hash '${key}', field '${field}': ${String(error)}`,
                );
            }
        }
        return Object.fromEntries(entries);
    }

    /**
     * Validate matching inputs and reject duplicate keys for conditional writes.
     *
     * @remarks
     * All keys and documents in a given batch are validated before its transaction.
     * Previously completed batches remain committed if a later batch fails.
     */
    private static prepare_batch(keys: string[], docs: RedisDocument[]): PreparedDocument[] {
        if (keys.length !== docs.length) {
            throw new Error('Keys and documents must have the same length');
        }
        return keys.map((key, index) => {
            RedisDML.validate_key(key);
            return { key, fields: RedisDML.serialize_document(docs[index]) };
        });
    }

    private static validate_keys_unique(keys: string[]): void {
        const visited = new Set<string>();
        for (const key of keys) {
            RedisDML.validate_key(key);
            if (visited.has(key)) {
                throw new Error(`Duplicate key in bulk write: ${key}`);
            }
            visited.add(key);
        }
    }

    /**
     * Execute one conditional batch with an exclusive Redis client.
     *
     * @remarks
     * WATCH state belongs to one physical connection. The manager's pool
     * guarantees that another request cannot corrupt the watched key set.
     * Conflicts retry the complete batch with fresh reads, up to a bound.
     */
    private async with_watched_batch<T>(
        keys: string[],
        operation: (client: RedisClient) => Promise<T>,
    ): Promise<T> {
        for (let attempt = 0; attempt <= RedisDML.MAX_WATCH_RETRIES; attempt++) {
            try {
                return await this.manager.with_isolated_client(async (client) => {
                    await client.watch(keys);
                    try {
                        return await operation(client);
                    } finally {
                        // A successful EXEC clears WATCH automatically. UNWATCH
                        // is still needed when operation returns without EXEC.
                        if (client.isReady) {
                            try {
                                await client.unwatch();
                            } catch (error) {
                                this.logger.warn({ err: error }, 'Redis UNWATCH cleanup failed');
                            }
                        }
                    }
                });
            } catch (error) {
                if (!(error instanceof WatchError) || attempt === RedisDML.MAX_WATCH_RETRIES) {
                    throw error;
                }
                this.logger.warn({ attempt: attempt + 1 }, 'Redis WATCH conflict; retrying batch');
            }
        }
        // The final retry always returns or throws.
        throw new Error('Redis WATCH retries exhausted');
    }

    // ======================================================
    // 3. INSERT OPERATIONS
    // ======================================================

    /**
     * Insert one hash without overwriting any existing Redis key.
     *
     * @returns True when inserted; false if the key already exists.
     */
    public async insert_one(
        key: string,
        document: RedisDocument,
        ttl?: number,
    ): Promise<boolean> {
        return (await this.insert_many([key], [document], 1, ttl)) === 1;
    }

    /**
     * Insert hashes in bounded, optimistic transactions.
     *
     * @remarks
     * Every batch uses one WATCH + one MULTI/EXEC (when there are new keys),
     * not one transaction for every hash. Existing keys are never modified.
     * Individual batches commit independently; the entire method is not atomic.
     *
     * @returns Number of hashes inserted by successfully committed batches.
     */
    public async insert_many(
        keys: string[],
        documents: RedisDocument[],
        batch_size = 500,
        ttl?: number,
    ): Promise<number> {
        if (keys.length !== documents.length) {
            throw new Error('Keys and documents must have the same length');
        }
        RedisDML.validate_batch_size(batch_size);
        if (ttl !== undefined) RedisDML.validate_positive(ttl, 'TTL');
        RedisDML.validate_keys_unique(keys);

        let inserted = 0;
        for (let index = 0; index < keys.length; index += batch_size) {
            const batch = RedisDML.prepare_batch(
                keys.slice(index, index + batch_size),
                documents.slice(index, index + batch_size),
            );

            inserted += await this.with_watched_batch(batch.map(item => item.key), async (client) => {
                // These existence checks are pipelined automatically by node-redis.
                const exists = await Promise.all(batch.map(item => client.exists(item.key)));
                const pending = batch.filter((_item, i) => exists[i] === 0);
                if (pending.length === 0) return 0;

                const transaction = client.multi();
                for (const item of pending) {
                    transaction.hSet(item.key, item.fields);
                    if (ttl !== undefined) transaction.expire(item.key, ttl);
                }
                await transaction.exec();
                return pending.length;
            });
        }

        this.logger.debug({ requested: keys.length, inserted }, 'Redis batch insert completed');
        return inserted;
    }

    // ======================================================
    // 4. READ OPERATIONS
    // ======================================================

    /**
     * Read either one hash field or the complete document.
     *
     * @returns The decoded value/document, or null for missing data.
     */
    public async get_one(key: string, field?: string): Promise<unknown | null> {
        RedisDML.validate_key(key);
        if (field !== undefined) {
            const value = await this.client.hGet(key, field);
            if (value === null || value === undefined) return null;
            try {
                return JSON.parse(value);
            } catch (error) {
                throw new SyntaxError(
                    `Invalid JSON in Redis hash '${key}', field '${field}': ${String(error)}`,
                );
            }
        }
        const values = await this.client.hGetAll(key);
        return RedisDML.deserialize_document(key, values);
    }

    /**
     * Read multiple hashes using bounded pipelined HGETALL commands.
     *
     * @remarks
     * Redis has no native multi-key HGETALL. Pipelining reduces network
     * overhead but still performs one HGETALL command per key on the server.
     * Missing hashes are skipped; existing hashes retain input order.
     */
    public async get_many(keys: string[], batch_size = 500): Promise<RedisDocument[]> {
        RedisDML.validate_batch_size(batch_size);
        const documents: RedisDocument[] = [];

        for (let index = 0; index < keys.length; index += batch_size) {
            const batch = keys.slice(index, index + batch_size);
            batch.forEach(RedisDML.validate_key);

            // node-redis automatically pipelines commands issued together.
            // Promise.all preserves each HGETALL reply's precise TypeScript type.
            const results = await Promise.all(
                batch.map(key => this.client.hGetAll(key)),
            );

            for (let i = 0; i < batch.length; i++) {
                const document = RedisDML.deserialize_document(
                    batch[i],
                    results[i],
                );
                if (document !== null) documents.push(document);
            }
        }
        return documents;
    }

    /**
     * Scan hash keys and yield decoded document batches.
     *
     * @remarks
     * SCAN is not a snapshot and may repeat/omit keys during concurrent writes.
     * The iterator does not hold the entire Redis keyspace in application memory.
     */
    public async *stream_many_docs(
        pattern = '*',
        batch_size = 1000,
    ): AsyncGenerator<RedisDocument[], void, unknown> {
        RedisDML.validate_batch_size(batch_size);
        let pendingKeys: string[] = [];

        for await (const keys of this.client.scanIterator({
            MATCH: pattern,
            COUNT: batch_size,
            TYPE: 'hash',
        })) {
            for (const key of keys) {
                pendingKeys.push(key);
                if (pendingKeys.length === batch_size) {
                    const result = await this.get_many(pendingKeys, batch_size);
                    if (result.length) yield result;
                    pendingKeys = [];
                }
            }
        }
        if (pendingKeys.length) {
            const result = await this.get_many(pendingKeys, batch_size);
            if (result.length) yield result;
        }
    }

    /** Collect matching documents in memory; prefer streaming for large keyspaces. */
    public async get_many_by_pattern(
        pattern = '*',
        batch_size = 1000,
    ): Promise<RedisDocument[]> {
        const documents: RedisDocument[] = [];
        for await (const batch of this.stream_many_docs(pattern, batch_size)) {
            documents.push(...batch);
        }
        return documents;
    }

    // ======================================================
    // 5. TTL OPERATIONS
    // ======================================================

    /** Set expiration in seconds; return false when the key does not exist. */
    public async set_ttl(key: string, duration_seconds: number): Promise<boolean> {
        RedisDML.validate_key(key);
        RedisDML.validate_positive(duration_seconds, 'TTL');
        // Redis EXPIRE returns 1 when updated, or 0 when the key is missing.
        return (await this.client.expire(key, duration_seconds)) === 1;
    }

    /** Return remaining TTL in seconds, -1 for no expiry, null for missing keys. */
    public async get_ttl(key: string): Promise<number | null> {
        RedisDML.validate_key(key);
        const ttl = await this.client.ttl(key);
        return ttl === -2 ? null : ttl;
    }

    // ======================================================
    // 6. UPDATE OPERATIONS
    // ======================================================

    /**
     * Update one document, optionally merging, replacing, or upserting it.
     *
     * @returns False when missing and upsert is disabled; otherwise true.
     */
    public async update_one(
        key: string,
        document: RedisDocument,
        merge = true,
        upsert = false,
        ttl?: number,
    ): Promise<boolean> {
        return (await this.update_many([key], [document], merge, upsert, 1, ttl)) === 1;
    }

    /**
     * Update or replace many hashes using conditional, batch-sized transactions.
     *
     * @remarks
     * - merge=true: HSET preserves other fields and existing TTL.
     * - merge=false: DEL + HSET replaces all fields.
     * - upsert=false: missing keys remain missing.
     * - ttl supplied: sets the new expiration.
     * - ttl omitted: replacement restores the prior absolute expiry estimate.
     * WATCH protects type, existence, and TTL decisions until EXEC.
     *
     * @returns Number of keys updated or inserted by committed batches.
     */
    public async update_many(
        keys: string[],
        documents: RedisDocument[],
        merge = true,
        upsert = false,
        batch_size = 500,
        ttl?: number,
    ): Promise<number> {
        if (keys.length !== documents.length) {
            throw new Error('Keys and documents must have the same length');
        }
        RedisDML.validate_batch_size(batch_size);
        if (ttl !== undefined) RedisDML.validate_positive(ttl, 'TTL');
        RedisDML.validate_keys_unique(keys);

        let updated = 0;
        for (let index = 0; index < keys.length; index += batch_size) {
            const batch = RedisDML.prepare_batch(
                keys.slice(index, index + batch_size),
                documents.slice(index, index + batch_size),
            );

            updated += await this.with_watched_batch(batch.map(item => item.key), async (client) => {
                const types = await Promise.all(batch.map(item => client.type(item.key)));

                // Avoid transaction-time WRONGTYPE errors, which Redis does not
                // roll back even when earlier MULTI commands have succeeded.
                for (let i = 0; i < types.length; i++) {
                    if (types[i] !== 'hash' && types[i] !== 'none') {
                        throw new TypeError(`Redis key '${batch[i].key}' is not a hash`);
                    }
                }

                const positions = batch
                    .map((_item, i) => i)
                    .filter(i => types[i] === 'hash' || upsert);
                if (positions.length === 0) return 0;

                // Record the prior expirations only when a full replacement
                // needs to delete and recreate an existing hash.
                const previousTtls = new Map<number, number>();
                if (!merge && ttl === undefined) {
                    const oldPositions = positions.filter(i => types[i] === 'hash');
                    const ttls = await Promise.all(oldPositions.map(i => client.pTTL(batch[i].key)));
                    oldPositions.forEach((position, i) => previousTtls.set(position, ttls[i]));
                }

                const transaction = client.multi();
                for (const position of positions) {
                    const item = batch[position];
                    const exists = types[position] === 'hash';

                    if (!merge && exists) transaction.del(item.key);
                    transaction.hSet(item.key, item.fields);

                    if (ttl !== undefined) {
                        transaction.expire(item.key, ttl);
                    } else if (!merge && exists) {
                        const remainingMs = previousTtls.get(position);
                        if (remainingMs !== undefined && remainingMs >= 0) {
                            // PEXPIREAT avoids accidentally resetting the TTL
                            // to a full interval after DEL + HSET.
                            transaction.pExpireAt(item.key, Date.now() + remainingMs);
                        }
                    }
                }
                await transaction.exec();
                return positions.length;
            });
        }

        this.logger.debug({ requested: keys.length, updated }, 'Redis batch update completed');
        return updated;
    }

    // ======================================================
    // 7. DELETE OPERATIONS
    // ======================================================

    /** Delete a single key and return whether it existed. */
    public async delete_one(key: string): Promise<boolean> {
        RedisDML.validate_key(key);
        return (await this.client.del(key)) > 0;
    }

    /**
     * Delete keys in bounded groups using Redis's native multi-key DEL.
     *
     * @returns Number of keys actually removed.
     */
    public async delete_many(keys: string[], batch_size = 500): Promise<number> {
        RedisDML.validate_batch_size(batch_size);
        let deleted = 0;
        for (let index = 0; index < keys.length; index += batch_size) {
            const batch = keys.slice(index, index + batch_size);
            batch.forEach(RedisDML.validate_key);
            deleted += await this.client.del(batch);
        }
        return deleted;
    }
}

/** Compile-time check of the static, framework-independent factory contract. */
const _check = RedisDML satisfies InfrastructureFactoryInterface<
    RedisDML,
    [manager: RedisConnectionManager, logger: ContextLogger]
>;
