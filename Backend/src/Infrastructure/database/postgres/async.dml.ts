
import type { ContextLogger } from "../../logging/logging.service";
import type { QueryRunner } from "typeorm";

import { PostgresConnectionManager } from "./async.connection";
import { InfrastructureFactoryInterface } from "../interfaces/factory.interface";

/**
 * Generic PostgreSQL data-access operations over a shared connection pool.
 *
 * @remarks
 * This is infrastructure, not a business/domain repository. It does not
 * manage connection startup or shutdown and has no NestJS dependency.
 */
export class PostgresDML {
    private constructor(
        private readonly conn: PostgresConnectionManager,
        private readonly logger: ContextLogger,
    ) { }

    // -----------------------------------
    // Factory initialization
    // -----------------------------------

    /**
     * Create a data-access object from an already initialized manager.
     *
     * @param conn - Shared connection manager.
     * @param logger - Contextual logger supplied by the composition module.
     * @returns A reusable DML instance.
     * @throws If the supplied connection manager is not initialized.
     */
    static async init_class(
        conn: PostgresConnectionManager,
        logger: ContextLogger,
    ): Promise<PostgresDML> {
        if (!conn.getAppDataSource().isInitialized) {
            throw new Error("PostgreSQL connection is not initialized");
        }

        logger.info("PostgresDML initialized successfully");

        return new PostgresDML(conn, logger);
    }

    // -----------------------------------
    // Internal utilities
    // -----------------------------------

    private quoteIdentifier(name: string): string {
        if (
            typeof name !== "string" ||
            !name.trim() ||
            name.includes("\0")
        ) {
            throw new Error("Invalid PostgreSQL identifier");
        }

        return `"${name.replace(/"/g, '""')}"`;
    }

    private tablePath(table_name: string, schema?: string): string {
        const table = this.quoteIdentifier(table_name);

        return schema
            ? `${this.quoteIdentifier(schema)}.${table}`
            : table;
    }

    private assertRecord(value: Record<string, unknown>, label: string,
    ): void {
        if (
            !value ||
            typeof value !== "object" ||
            Array.isArray(value) ||
            Object.keys(value).length === 0
        ) {
            throw new Error(`${label} must be a non-empty object`);
        }

        if (Object.values(value).some((item) => item === undefined)) {
            throw new Error(`${label} cannot contain undefined values`);
        }
    }

    private async withQueryRunner<T>(operation: (runner: QueryRunner) => Promise<T>,
    ): Promise<T> {
        const runner = this.conn.getAppDataSource().createQueryRunner();

        try {
            await runner.connect();
            return await operation(runner);
        } catch (error) {
            this.logger.error(
                { err: error },
                "PostgreSQL operation failed",
            );
            throw error;
        } finally {
            if (!runner.isReleased) {
                await runner.release();
            }
        }
    }

    // -----------------------------------
    // Schema operations
    // -----------------------------------

    /**
     * List PostgreSQL schemas visible to the current connection.
     *
     * @returns Schema names in alphabetical order.
     * @throws If PostgreSQL cannot execute the schema query.
     */
    async list_all_schemas(): Promise<string[]> {
        return this.withQueryRunner(async (runner) => {
            const rows: { schema_name: string }[] =
                await runner.query(`
          SELECT schema_name
          FROM information_schema.schemata
          ORDER BY schema_name;
        `);

            return rows.map((row) => row.schema_name);
        });
    }

    /**
     * List base tables within a schema.
     *
     * @param schema_name - PostgreSQL schema to inspect.
     * @returns Table names in alphabetical order.
     */
    async list_tables_names(schema_name: string): Promise<string[]> {
        return this.withQueryRunner(async (runner) => {
            const rows: { table_name: string }[] =
                await runner.query(
                    `
          SELECT table_name
          FROM information_schema.tables
          WHERE table_schema = $1
            AND table_type = 'BASE TABLE'
          ORDER BY table_name;
          `,
                    [schema_name],
                );

            return rows.map((row) => row.table_name);
        });
    }

    // -----------------------------------
    // Update table
    // -----------------------------------


    /**
     * Update rows matching explicit conditions.
     *
     * @param table_name - Target table.
     * @param updates - Columns and replacement values.
     * @param conditions - Required WHERE clause conditions.
     * @param schema - Optional PostgreSQL schema.
     * @returns Number of rows affected by the operation.
     * @throws If updates or conditions are empty or SQL fails.
     */
    async update_table(
        table_name: string,
        updates: Record<string, unknown>,
        conditions: Record<string, unknown>,
        schema?: string,
    ): Promise<number> {
        this.assertRecord(updates, "updates");
        this.assertRecord(conditions, "conditions");

        return this.withQueryRunner(async (runner) => {
            const params: unknown[] = [];

            const setClause = Object.entries(updates)
                .map(([column, value]) => {
                    params.push(value);

                    return `${this.quoteIdentifier(column)} = $${params.length}`;
                })
                .join(", ");

            const whereClause = Object.entries(conditions)
                .map(([column, value]) => {
                    const name = this.quoteIdentifier(column);

                    if (value === null) {
                        return `${name} IS NULL`;
                    }

                    if (Array.isArray(value)) {
                        if (value.length === 0) {
                            return "FALSE";
                        }

                        params.push(value);
                        return `${name} = ANY($${params.length})`;
                    }

                    params.push(value);
                    return `${name} = $${params.length}`;
                })
                .join(" AND ");

            const query = `
            UPDATE ${this.tablePath(table_name, schema)}
            SET ${setClause}
            WHERE ${whereClause}
            RETURNING 1;
        `;

            // Request a structured QueryResult from TypeORM.
            const result = await runner.query(query, params, true);

            // Get the actual number of affected database rows.
            const affected = result.affected ?? 0;

            this.logger.info(
                { table_name, affected },
                "Table updated",
            );

            return affected;
        });
    }


    // -----------------------------------
    // Atomic conditional decrement
    // -----------------------------------

    /**
     * Decrement a positive integer column in one atomic PostgreSQL statement.
     *
     * This is a generic DML operation, not quota-specific. The duplicate guard
     * refuses the update if multiple rows match the provided key. The database
     * should also enforce a UNIQUE constraint on that key for full integrity.
     *
     * @returns Number of matching key rows (up to 2), and number actually changed.
     */
    async decrement_positive_integer_column(
        table_name: string,
        key_column: string,
        key_value: unknown,
        counter_column: string,
        schema?: string,
    ): Promise<{ matchingRows: number; affectedRows: number }> {
        if (key_value === null || key_value === undefined) {
            throw new Error('Key value is required for conditional decrement');
        }

        return this.withQueryRunner(async (runner) => {
            const table = this.tablePath(table_name, schema);
            const key = this.quoteIdentifier(key_column);
            const counter = this.quoteIdentifier(counter_column);

            // The condition is rechecked after PostgreSQL waits on a locked row.
            // A second request cannot decrement a counter already reduced to zero.
            const rows: Array<{ matchingRows: number; affectedRows: number }> =
                await runner.query(
                    `WITH matching AS MATERIALIZED (
                        SELECT 1 FROM ${table} WHERE ${key} = $1 LIMIT 2
                    ), changed AS (
                        UPDATE ${table}
                        SET ${counter} = ${counter} - 1
                        WHERE ${key} = $1
                          AND ${counter} > 0
                          AND (SELECT COUNT(*) FROM matching) = 1
                        RETURNING 1
                    )
                    SELECT
                        (SELECT COUNT(*) FROM matching)::integer AS "matchingRows",
                        (SELECT COUNT(*) FROM changed)::integer AS "affectedRows"`,
                    [key_value],
                );

            if (rows.length !== 1) {
                throw new Error('Unexpected PostgreSQL decrement result');
            }

            const matchingRows = Number(rows[0].matchingRows);
            const affectedRows = Number(rows[0].affectedRows);
            this.logger.info({ table_name, affected: affectedRows }, 'Conditional decrement completed');
            return { matchingRows, affectedRows };
        });
    }

    // -----------------------------------
    // Internal insert implementation
    // -----------------------------------

    private async executeInsert(
        runner: QueryRunner,
        table_name: string,
        data: Record<string, unknown>[],
        schema?: string,
        on_conflict: "do_nothing" | "do_update" = "do_nothing",
        conflict_columns?: string[],
        update_columns?: string[],
    ): Promise<number> {
        if (data.length === 0) {
            return 0;
        }

        for (const row of data) {
            this.assertRecord(row, "data row");
        }

        const columns = [
            ...new Set(data.flatMap((row) => Object.keys(row))),
        ];

        const params: unknown[] = [];

        const valuesClause = data
            .map((row) => {
                const placeholders = columns.map((column) => {
                    if (!Object.prototype.hasOwnProperty.call(row, column)) {
                        return "DEFAULT";
                    }

                    params.push(row[column]);
                    return `$${params.length}`;
                });

                return `(${placeholders.join(", ")})`;
            })
            .join(", ");

        if (params.length > 65535) {
            throw new Error(
                "Too many SQL parameters; reduce batch_size",
            );
        }

        let query = `
      INSERT INTO ${this.tablePath(table_name, schema)}
      (${columns.map((col) => this.quoteIdentifier(col)).join(", ")})
      VALUES ${valuesClause}
    `;

        if (on_conflict === "do_nothing") {
            const target = conflict_columns?.length
                ? `(${conflict_columns
                    .map((col) => this.quoteIdentifier(col))
                    .join(", ")})`
                : "";

            query += ` ON CONFLICT ${target} DO NOTHING`;
        } else if (on_conflict === "do_update") {
            if (!conflict_columns?.length) {
                throw new Error(
                    "conflict_columns is required for do_update",
                );
            }

            const columnsToUpdate =
                update_columns ??
                columns.filter((col) => !conflict_columns.includes(col));

            if (columnsToUpdate.length === 0) {
                throw new Error("No columns available for conflict update");
            }

            for (const column of columnsToUpdate) {
                if (!columns.includes(column)) {
                    throw new Error(
                        `Update column '${column}' is not in the input data`,
                    );
                }
            }

            const conflictTarget = conflict_columns
                .map((col) => this.quoteIdentifier(col))
                .join(", ");

            const updateClause = columnsToUpdate
                .map((column) => {
                    const quoted = this.quoteIdentifier(column);
                    return `${quoted} = EXCLUDED.${quoted}`;
                })
                .join(", ");

            query += `
        ON CONFLICT (${conflictTarget})
        DO UPDATE SET ${updateClause}
      `;
        } else {
            throw new Error(`Unsupported conflict action: ${on_conflict}`);
        }

        query += " RETURNING 1;";

        const rows: unknown[] = await runner.query(query, params);

        return rows.length;
    }

    // -----------------------------------
    // Insert into table
    // -----------------------------------

    /**
     * Insert one or more rows, optionally handling unique-key conflicts.
     *
     * @param table_name - Target table name.
     * @param data - One row or an array of rows.
     * @param schema - Optional PostgreSQL schema.
     * @param on_conflict - Conflict handling strategy.
     * @param conflict_columns - Columns that define the conflict target.
     * @param update_columns - Columns to update on a conflict.
     * @returns The number of inserted or affected rows.
     */
    async insert_into_table(
        table_name: string,
        data: Record<string, unknown> | Record<string, unknown>[],
        schema?: string,
        on_conflict: "do_nothing" | "do_update" = "do_nothing",
        conflict_columns?: string[],
        update_columns?: string[],
    ): Promise<number> {
        const rows = Array.isArray(data) ? data : [data];

        return this.withQueryRunner(async (runner) => {
            const affected = await this.executeInsert(
                runner,
                table_name,
                rows,
                schema,
                on_conflict,
                conflict_columns,
                update_columns,
            );

            this.logger.info(
                { table_name, affected },
                "Insert completed",
            );

            return affected;
        });
    }

    // -----------------------------------
    // Bulk insert
    // -----------------------------------

    /**
     * Insert many rows in bounded batches.
     *
     * @remarks
     * `commit_every_batch=true` commits independently. When false, all
     * batches share one transaction and roll back together on failure.
     *
     * @param table_name - Target table.
     * @param data - Rows to insert.
     * @param schema - Optional schema.
     * @param batch_size - Maximum rows per insert statement.
     * @param commit_every_batch - Whether to commit each batch separately.
     * @param on_conflict - Conflict strategy.
     * @param conflict_columns - Conflict target columns.
     * @param update_columns - Columns updated for conflicting records.
     * @returns Total inserted or affected rows.
     */
    async insert_into_table_bulk(
        table_name: string,
        data: Record<string, unknown> | Record<string, unknown>[],
        schema?: string,
        batch_size: number = 1000,
        commit_every_batch: boolean = true,
        on_conflict: "do_nothing" | "do_update" = "do_nothing",
        conflict_columns?: string[],
        update_columns?: string[],
    ): Promise<number> {
        if (!Number.isSafeInteger(batch_size) || batch_size <= 0) {
            throw new Error("batch_size must be a positive integer");
        }

        const rows = Array.isArray(data) ? data : [data];

        if (rows.length === 0) {
            return 0;
        }

        let total = 0;

        // Each batch is an independently committed statement.
        if (commit_every_batch) {
            for (let i = 0; i < rows.length; i += batch_size) {
                const batch = rows.slice(i, i + batch_size);

                total += await this.insert_into_table(
                    table_name,
                    batch,
                    schema,
                    on_conflict,
                    conflict_columns,
                    update_columns,
                );
            }
        } else {
            // All batches share one atomic transaction.
            total = await this.withQueryRunner(async (runner) => {
                await runner.startTransaction();

                try {
                    let affected = 0;

                    for (let i = 0; i < rows.length; i += batch_size) {
                        const batch = rows.slice(i, i + batch_size);

                        affected += await this.executeInsert(
                            runner,
                            table_name,
                            batch,
                            schema,
                            on_conflict,
                            conflict_columns,
                            update_columns,
                        );
                    }

                    await runner.commitTransaction();
                    return affected;
                } catch (error) {
                    if (runner.isTransactionActive) {
                        await runner.rollbackTransaction();
                    }
                    throw error;
                }
            });
        }

        this.logger.info(
            { table_name, affected: total },
            "Bulk insert completed",
        );

        return total;
    }

    // -----------------------------------
    // Get table data
    // -----------------------------------

    /**
     * Read a bounded set of rows from one PostgreSQL table.
     *
     * @param table_name - Table to query.
     * @param schema - Optional schema.
     * @param limit - Positive maximum number of returned rows.
     * @param order_by - Optional ordering column.
     * @param ascending - Sort direction if order_by is supplied.
     * @returns An array of database records.
     */
    async get_table_data(
        table_name: string,
        schema?: string,
        limit: number = 500,
        order_by?: string,
        ascending: boolean = true,
    ): Promise<Record<string, unknown>[]> {
        if (!Number.isSafeInteger(limit) || limit <= 0) {
            throw new Error("limit must be a positive integer");
        }

        return this.withQueryRunner(async (runner) => {
            const orderClause = order_by
                ? `ORDER BY ${this.quoteIdentifier(order_by)} ${ascending ? "ASC" : "DESC"
                }`
                : "";

            const query = `
        SELECT *
        FROM ${this.tablePath(table_name, schema)}
        ${orderClause}
        LIMIT $1;
      `;

            const rows: Record<string, unknown>[] =
                await runner.query(query, [limit]);

            this.logger.debug(
                { table_name, count: rows.length },
                "Table data retrieved",
            );

            return rows;
        });
    }


    // -----------------------------------
    // Get single row
    // -----------------------------------

    /**
     * Retrieve a single row matching a specific column value.
     *
     * @param table_name - Table to query.
     * @param schema - Optional PostgreSQL schema (pass undefined to use default).
     * @param column_name - Column to filter on.
     * @param value - Value to match (supports primitives and null).
     * @returns The first matching database record, or null if not found.
     * @throws If the value is undefined or identifiers are invalid.
     */
    async get_single_row<T extends Record<string, unknown> = Record<string, unknown>>(
        table_name: string,
        schema: string | undefined,
        column_name: string,
        value: unknown,
    ): Promise<Record<string, unknown> | null> {
        if (value === undefined) {
            throw new Error("Filter value cannot be undefined");
        }

        return this.withQueryRunner(async (runner) => {
            const column = this.quoteIdentifier(column_name);
            const params: unknown[] = [];

            let whereClause: string;

            if (value === null) {
                whereClause = `${column} IS NULL`;
            } else {
                params.push(value);
                whereClause = `${column} = $1`;
            }

            const query = `
        SELECT *
        FROM ${this.tablePath(table_name, schema)}
        WHERE ${whereClause}
        LIMIT 1;
      `;

            const rows: T[] = await runner.query(query, params);

            this.logger.debug(
                { table_name, schema, column_name, found: rows.length > 0 },
                "Single row query executed",
            );

            return rows[0] ?? null;
        });
    }
}

// -----------------------------------
// Static factory contract validation
// -----------------------------------

export const PostgresDMLFactory =
    PostgresDML satisfies InfrastructureFactoryInterface<
        PostgresDML,
        [PostgresConnectionManager, ContextLogger]
    >;
