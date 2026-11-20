
import type { ContextLogger } from "../../logging/logging.service";
import { PostgresConnectionManager } from "./async.connection";
import { InfrastructureFactoryInterface } from "../interfaces/factory.interface";

/**
 * Framework-independent PostgreSQL schema inspection operations.
 *
 * @remarks
 * Uses a DataSource owned by PostgresConnectionManager and releases each
 * query runner even when an operation throws.
 */
export class PostgresDDL {
    private constructor(
        private readonly conn: PostgresConnectionManager,
        private readonly logger: ContextLogger,
    ) { }

    /** Create a DDL accessor using the existing PostgreSQL manager. */
    static async init_class(
        conn: PostgresConnectionManager,
        logger: ContextLogger,
    ): Promise<PostgresDDL> {
        return new PostgresDDL(conn, logger);
    }

    async list_all_schemas(): Promise<string[]> {
        const dataSource = this.conn.getAppDataSource();
        const runner = dataSource.createQueryRunner();

        try {
            await runner.connect();

            this.logger.info("Listing all PostgreSQL schemas");

            const rows: { schema_name: string }[] = await runner.query(`
        SELECT schema_name
        FROM information_schema.schemata
        ORDER BY schema_name;
      `);

            return rows.map((row) => row.schema_name);
        } catch (error) {
            this.logger.error({ err: error }, "Failed to list schemas");
            throw error;
        } finally {
            await runner.release();
        }
    }

    async list_tables_names(schema_name: string): Promise<string[]> {
        const dataSource = this.conn.getAppDataSource();
        const runner = dataSource.createQueryRunner();

        try {
            await runner.connect();

            this.logger.info({ schema_name }, "Listing PostgreSQL tables");

            const rows: { table_name: string }[] = await runner.query(
                `
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = $1
        ORDER BY table_name;
        `,
                [schema_name],
            );

            return rows.map((row) => row.table_name);
        } catch (error) {
            this.logger.error(
                { err: error, schema_name },
                "Failed to list tables",
            );
            throw error;
        } finally {
            await runner.release();
        }
    }
}

// Compile-time validation of the static factory
const _check: InfrastructureFactoryInterface<
    PostgresDDL,
    [PostgresConnectionManager, ContextLogger]
> = PostgresDDL;
