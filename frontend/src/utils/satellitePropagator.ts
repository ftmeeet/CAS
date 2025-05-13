import { TLE } from './tleParser';
import * as satellite from 'satellite.js';

interface Position {
  x: number;
  y: number;
  z: number;
}

const EARTH_RADIUS = 6378137.0; // meters
const GM = 398600.4418; // km³/s²

export function propagateSatellite(tle: TLE, time: Date): Position | null {
  try {
    // Create satellite record from TLE
    const satrec = satellite.twoline2satrec(tle.line1, tle.line2);
    
    // Get position and velocity
    const positionAndVelocity = satellite.propagate(satrec, time);
    
    if (positionAndVelocity.position && typeof positionAndVelocity.position !== 'boolean') {
      // Convert from kilometers to meters
      return {
        x: positionAndVelocity.position.x * 1000,
        y: positionAndVelocity.position.y * 1000,
        z: positionAndVelocity.position.z * 1000
      };
    }
    
    return null;
  } catch (error) {
    console.error('Error propagating satellite:', error);
    return null;
  }
} 