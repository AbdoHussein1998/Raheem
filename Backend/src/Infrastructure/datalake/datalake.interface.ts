/** Generic object-storage contract. No dependency on photos, Facebook, or NestJS. */
export interface DataLakeInterface {
    uploadObject(key: string, bytes: Buffer, contentType: string): Promise<void>;
    objectExists(key: string): Promise<boolean>;
    getObject(key: string): Promise<Buffer>;
    deleteObject(key: string): Promise<void>;
}

/** Runtime injection token; TypeScript interfaces are erased at runtime. */
export const DATA_LAKE = Symbol('DATA_LAKE');
