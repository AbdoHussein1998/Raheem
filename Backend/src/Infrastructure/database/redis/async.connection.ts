
import { createClient } from 'redis';
import type { ContextLogger } from '../../logging/logging.service';

import type { ConnectionManagerInterface, } from '../interfaces/connection.manager';

type RedisClient = ReturnType<typeof createClient>;
type RedisIsolationPool = ReturnType<RedisClient['createPool']>;

/**
 * Manages a reusable Redis client and its reconnect/shutdown lifecycle.
 *
 * @remarks
 * This class is framework-independent. Its factory attempts to establish
 * the connection before returning the manager to a caller.
 */
export class RedisConnectionManager implements ConnectionManagerInterface {

    private readonly client: RedisClient;
    // WATCH requires an exclusive connection per concurrent transaction.
    // The pool is initialized only when the first conditional write needs it.
    private isolationPoolPromise?: Promise<RedisIsolationPool>;

    // Concurrent callers must reuse a single pending connection attempt.
    private connecting?: Promise<boolean>;

    private constructor(
        url: string,
        private readonly logger: ContextLogger,
    ) {

        this.client = createClient({
            url,

            socket: {
                connectTimeout: 10_000,

                reconnectStrategy: (retries: number) => {
                    const delay = Math.min(
                        100 * 2 ** Math.min(retries, 5),
                        3000,
                    );

                    const jitter = Math.floor(
                        Math.random() * 100,
                    );

                    return delay + jitter;
                },
            },
        });

        this.client.on('connect', () => {
            this.logger.info('Connecting to Redis');
        });

        this.client.on('ready', () => {
            this.logger.info('Redis connection ready');
        });

        this.client.on('reconnecting', () => {
            this.logger.warn('Redis reconnecting');
        });

        this.client.on('end', () => {
            this.logger.info('Redis connection closed');
        });

        this.client.on('error', (error: Error) => {
            this.logger.error(
                { err: error },
                'Redis connection error',
            );
        });
    }

    // ----------------------------------
    // Factory Initialization
    // ----------------------------------

    /**
     * Create and connect one Redis manager.
     *
     * @param url - Redis connection URL.
     * @param logger - Contextual logger supplied by the composition module.
     * @returns An initialized Redis manager.
     * @throws If Redis cannot establish a usable connection.
     */
    public static async init_class(
        url: string,
        logger: ContextLogger,
    ): Promise<RedisConnectionManager> {

        const manager = new RedisConnectionManager(
            url,
            logger,
        );

        const connected = await manager.connect();
        if (!connected) {
            throw new Error('Redis connection was not ready after initialization');
        }

        return manager;
    }

    // ----------------------------------
    // Connect
    // ----------------------------------

    /**
     * Connect once; concurrent callers await the same pending attempt.
     *
     * @returns True when the shared Redis client is ready.
     * @throws When the Redis client fails to connect.
     */
    public async connect(): Promise<boolean> {
        if (this.client.isReady) return true;
        if (this.connecting) return this.connecting;
        if (this.client.isOpen) {
            this.logger.warn('Redis is open but not ready (possibly reconnecting)');
            return false;
        }

        this.connecting = (async (): Promise<boolean> => {
            try {
                await this.client.connect();
                return this.client.isReady;
            } catch (error) {
                this.logger.error({ err: error }, 'Redis connection failed');
                throw error;
            }
        })();

        try {
            return await this.connecting;
        } finally {
            this.connecting = undefined;
        }
    }

    // ----------------------------------
    // Isolated WATCH Transactions
    // ----------------------------------

    /**
     * Run a transaction callback on a dedicated pooled Redis connection.
     *
     * @remarks
     * WATCH state belongs to a physical Redis connection. Sharing the
     * ordinary Redis client for concurrent WATCH operations is unsafe.
     * The bounded pool creates at most four additional connections and is
     * owned (and closed) by this connection manager, not by RedisDML.
     *
     * @param action - Work to perform using one isolated client.
     * @returns The callback's result.
     * @throws If the pool cannot connect or a connection cannot be acquired.
     */
    public async with_isolated_client<T>(
        action: (client: RedisClient) => Promise<T>,
    ): Promise<T> {
        if (!this.client.isReady) {
            throw new Error('Redis is not ready');
        }

        if (!this.isolationPoolPromise) {
            this.isolationPoolPromise = (async (): Promise<RedisIsolationPool> => {
                const pool = this.client.createPool({
                    minimum: 1,
                    maximum: 4,
                    acquireTimeout: 3_000,
                });

                pool.on('error', (error: Error) => {
                    this.logger.error({ err: error }, 'Redis isolation pool error');
                });

                try {
                    await pool.connect();
                    return pool;
                } catch (error) {
                    pool.destroy();
                    throw error;
                }
            })();
        }

        let pool: RedisIsolationPool;
        try {
            pool = await this.isolationPoolPromise;
        } catch (error) {
            this.isolationPoolPromise = undefined;
            throw error;
        }

        return pool.execute(action);
    }

    // ----------------------------------
    // Disconnect
    // ----------------------------------

    public async disconnect(): Promise<boolean> {
        try {
            // Allow a pending connection attempt to finish before shutdown.
            if (this.connecting) {
                try {
                    await this.connecting;
                } catch {
                    // Cleanup still proceeds if connection initialization failed.
                }
            }
            // Always attempt to close the main client, even if pool cleanup
            // fails. Pool initialization is lazy and can itself be in flight.
            let poolClosed = true;
            if (this.isolationPoolPromise) {
                const pendingPool = this.isolationPoolPromise;
                this.isolationPoolPromise = undefined;
                try {
                    const pool = await pendingPool;
                    await pool.close();
                } catch (error) {
                    poolClosed = false;
                    this.logger.error({ err: error }, 'Redis isolation pool shutdown failed');
                }
            }

            if (this.client.isOpen) {
                await this.client.close();
            }

            this.logger.info('Redis disconnected');
            return poolClosed;

        } catch (error) {
            this.logger.error(
                { err: error },
                'Failed to disconnect Redis',
            );

            return false;
        }
    }

    // ----------------------------------
    // Reconnect
    // ----------------------------------

    public async reconnect(): Promise<boolean> {

        this.logger.warn(
            'Manual Redis reconnection requested',
        );

        const disconnected = await this.disconnect();

        if (!disconnected) {
            return false;
        }

        return this.connect();
    }

    // ----------------------------------
    // Health Check
    // ----------------------------------

    public async ensure_connected(): Promise<boolean> {

        if (!this.client.isReady) {
            this.logger.warn('Redis client is not ready');
            return false;
        }

        try {
            const response = await this.client.ping();

            return response === 'PONG';

        } catch (error) {
            this.logger.error(
                { err: error },
                'Redis health check failed',
            );

            return false;
        }
    }

    // ----------------------------------
    // Client Access
    // ----------------------------------

    public get_client(): RedisClient {
        return this.client;
    }
}
