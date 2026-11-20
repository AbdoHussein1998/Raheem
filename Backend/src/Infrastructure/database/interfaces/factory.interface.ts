export interface InfrastructureFactoryInterface<
    TLayer,
    TArgs extends unknown[] = [],
> {
    init_class(...args: TArgs): Promise<TLayer>;
}