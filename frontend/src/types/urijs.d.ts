declare module 'urijs' {
  export class URI {
    constructor(uri?: string);
    toString(): string;
    absoluteTo(relative: string): URI;
    relativeTo(absolute: string): URI;
    normalize(): URI;
    normalizePath(): URI;
    addQuery(name: string, value: string): URI;
    addSearch(name: string, value: string): URI;
    setQuery(query: string | object): URI;
    setSearch(search: string | object): URI;
    removeQuery(name: string): URI;
    removeSearch(name: string): URI;
    query(): string;
    search(): string;
    path(): string;
    pathname(): string;
    segment(): string[];
    segment(index: number): string;
    segment(index: number, value: string): URI;
    directory(): string;
    filename(): string;
    suffix(): string;
    protocol(): string;
    protocol(value: string): URI;
    username(): string;
    username(value: string): URI;
    password(): string;
    password(value: string): URI;
    hostname(): string;
    hostname(value: string): URI;
    port(): string;
    port(value: string | number): URI;
    host(): string;
    host(value: string): URI;
    origin(): string;
    origin(value: string): URI;
    hash(): string;
    hash(value: string): URI;
    authority(): string;
    authority(value: string): URI;
    resource(): string;
    resource(value: string): URI;
    clone(): URI;
  }

  export function URI(uri?: string): URI;
  export default URI;
} 