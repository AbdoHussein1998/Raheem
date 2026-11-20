import { DataSource } from 'typeorm';
import type { ContextLogger } from '../../logging/logging.service';

import { ConnectionManagerInterface, } from '../interfaces/connection.manager';
import { InfrastructureFactoryInterface, } from '../interfaces/factory.interface';


/**
 * Configuration required to establish a PostgreSQL connection.
 */
export interface PostgresConnectionConfig {
    host: string;
    port: number;
    username: string;
    password: string;
    database: string;
    synchronize?: boolean;
    logging?: boolean;
    ssl?: boolean;
}


/**
 * Manages the PostgreSQL connection pool using TypeORM.
 *
 * @remarks
 * This class is framework-independent.
 *
 * Responsibilities:
 * - Initialize the PostgreSQL DataSource.
 * - Prevent duplicate concurrent initialization.
 * - Connect, disconnect, and reconnect.
 * - Provide the DataSource to DML/DDL classes.
 *
 * Use init_class() to create an initialized instance.
 */
export class PostgresConnectionManager implements ConnectionManagerInterface {

    private readonly dataSource: DataSource;
    // Tracks an ongoing connection attempt.
    private connecting?: Promise<boolean>;


    /**
     * Construct a PostgreSQL connection manager.
     *
     * @param config - PostgreSQL connection settings.
     * @param logger - Contextual logger supplied by the composition module.
     */

    constructor(
        config: PostgresConnectionConfig,
        private readonly logger: ContextLogger,
    ) {
        this.dataSource = new DataSource({
            type: 'postgres',
            host: config.host,
            port: config.port,
            username: config.username,
            password: config.password,
            database: config.database,
            synchronize: config.synchronize ?? false,
            logging: config.logging ?? false,

            // SSL configuration
            ssl: config.ssl ?? false,
        });
    }


    // ======================================================
    // 1. FACTORY INITIALIZATION
    // ======================================================

    /**
     * Create and initialize a PostgreSQL connection manager.
     *
     * @param config - PostgreSQL connection settings.
     * @param logger - Contextual logger supplied by the composition module.
     * @returns An initialized PostgreSQL manager.
     * @throws If the initial connection fails.
     */


    public static async init_class(
        config: PostgresConnectionConfig,
        logger: ContextLogger,
    ): Promise<PostgresConnectionManager> {

        const manager = new PostgresConnectionManager(
            config,
            logger,
        );

        const connected = await manager.connect();

        if (!connected) {
            throw new Error('Failed to initialize PostgreSQL');
        }

        return manager;
    }


    // ======================================================
    // 2. CONNECTION LIFECYCLE
    // ======================================================

    /**
     * Establish the PostgreSQL connection.
     *
     * @returns True if connected, otherwise false.
     */
    public async connect(): Promise<boolean> {

        if (this.dataSource.isInitialized) return true;

        // Reuse the pending initialization promise.
        if (this.connecting) return this.connecting;

        this.connecting = (async () => {
            try {
                this.logger.info('Connecting to PostgreSQL');

                await this.dataSource.initialize();

                this.logger.info('PostgreSQL connected');

                return true;

            } catch (error) {
                this.logger.error(
                    { err: error },
                    'PostgreSQL connection failed',
                );

                return false;
            }
        })();

        try {
            return await this.connecting;
        } finally {
            this.connecting = undefined;
        }
    }


    /**
     * Close the PostgreSQL connection pool.
     *
     * @returns True if disconnected successfully,
     * or already disconnected; otherwise false.
     */
    public async disconnect(): Promise<boolean> {

        try {
            // Wait for any pending connection attempt.
            if (this.connecting) {
                await this.connecting;
            }

            if (!this.dataSource.isInitialized) {
                return true;
            }

            await this.dataSource.destroy();

            this.logger.info('PostgreSQL disconnected');

            return true;

        } catch (error) {
            this.logger.error(
                { err: error },
                'PostgreSQL disconnection failed',
            );

            return false;
        }
    }


    /**
     * Restart the PostgreSQL connection.
     *
     * @returns True if reconnection succeeds,
     * otherwise false.
     */
    public async reconnect(): Promise<boolean> {

        const disconnected = await this.disconnect();

        if (!disconnected) return false;

        return this.connect();
    }


    /**
     * Ensure PostgreSQL is connected.
     *
     * @remarks
     * If the DataSource is already initialized,
     * no new initialization is performed.
     *
     * @returns True if connected, otherwise false.
     */
    public async ensure_connected(): Promise<boolean> {

        if (this.dataSource.isInitialized) {
            return true;
        }

        return this.connect();
    }


    // ======================================================
    // 3. DATASOURCE ACCESS
    // ======================================================

    /**
     * Get the managed TypeORM DataSource.
     *
     * @returns The shared PostgreSQL DataSource.
     *
     * @remarks
     * DML/DDL classes can use this DataSource to
     * execute database operations.
     *
     * This method does not establish a connection.
     */
    public getAppDataSource(): DataSource {
        return this.dataSource;
    }
}


/**
 * Verify that the class satisfies the static factory contract.
 *
 * @remarks
 * TypeScript checks this at compile time.
 * This does not create another manager instance.
 */
const _check = PostgresConnectionManager satisfies InfrastructureFactoryInterface<PostgresConnectionManager, [PostgresConnectionConfig, ContextLogger]>;