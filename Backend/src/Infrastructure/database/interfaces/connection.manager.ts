/**
 * Defines the lifecycle operations that every
 * database connection manager must implement.
 *
 * @remarks
 * This interface is framework-independent.
 * It can be implemented by PostgreSQL, Redis,
 * or other connection managers.
 */
export interface ConnectionManagerInterface {

    /** Connect to the database. */
    connect(): Promise<boolean>;

    /** Disconnect from the database. */
    disconnect(): Promise<boolean>;

    /** Disconnect and establish a new connection. */
    reconnect(): Promise<boolean>;

    /** Ensure an active database connection exists. */
    ensure_connected(): Promise<boolean>;
}


