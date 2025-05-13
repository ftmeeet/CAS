declare module 'grapheme-splitter' {
  export class GraphemeSplitter {
    constructor();
    splitGraphemes(string: string): string[];
    iterateGraphemes(string: string): IterableIterator<string>;
    countGraphemes(string: string): number;
  }

  export default GraphemeSplitter;
} 