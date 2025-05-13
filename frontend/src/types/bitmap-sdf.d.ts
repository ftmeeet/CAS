declare module 'bitmap-sdf' {
  interface SDFOptions {
    cutoff?: number;
    radius?: number;
    size?: number;
    font?: string;
    fontSize?: number;
    textAlign?: 'left' | 'center' | 'right';
    textBaseline?: 'top' | 'middle' | 'bottom';
  }

  interface SDFResult {
    data: Uint8Array;
    width: number;
    height: number;
    glyphWidth: number;
    glyphHeight: number;
    glyphTop: number;
    glyphLeft: number;
  }

  export function generateSDF(text: string, options?: SDFOptions): SDFResult;
  export default generateSDF;
} 