declare module 'lerc' {
  interface LercDecodeOptions {
    inputOffset?: number;
    returnType?: 'array' | 'object';
    noDataValue?: number;
    pixelType?: 'U8' | 'U16' | 'F32';
    dimension?: number;
    width?: number;
    height?: number;
    bands?: number;
  }

  interface LercDecodeResult {
    width: number;
    height: number;
    pixels: number[][];
    noDataValue?: number;
    minValue?: number;
    maxValue?: number;
    statistics?: {
      min: number;
      max: number;
      mean: number;
      stdDev: number;
    };
  }

  export function decode(data: ArrayBuffer | Uint8Array, options?: LercDecodeOptions): LercDecodeResult;
  export default decode;
} 