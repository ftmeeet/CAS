declare module 'satellite.js' {
  interface SatRec {
    // Add any specific properties you need from the satellite record
  }

  interface PositionAndVelocity {
    position: {
      x: number;
      y: number;
      z: number;
    } | boolean;
    velocity?: {
      x: number;
      y: number;
      z: number;
    };
  }

  export function twoline2satrec(line1: string, line2: string): SatRec;
  export function propagate(satrec: SatRec, time: Date): PositionAndVelocity;
} 