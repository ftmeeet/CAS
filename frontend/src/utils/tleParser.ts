export interface TLE {
  line1: string;
  line2: string;
  epoch: Date;
  meanMotion: number;
  eccentricity: number;
  inclination: number;
  rightAscension: number;
  argumentOfPerigee: number;
  meanAnomaly: number;
  bstar: number;
}

export function parseTLE(line1: string, line2: string): TLE | null {
  try {
    // Parse line 1
    const epochYear = parseInt(line1.substring(18, 20));
    const epochDay = parseFloat(line1.substring(20, 32));
    const meanMotion = parseFloat(line1.substring(52, 63));
    const bstar = parseFloat(line1.substring(53, 61)) * 1e-5;

    // Parse line 2
    const inclination = parseFloat(line2.substring(8, 16));
    const rightAscension = parseFloat(line2.substring(17, 25));
    const eccentricity = parseFloat('0.' + line2.substring(26, 33));
    const argumentOfPerigee = parseFloat(line2.substring(34, 42));
    const meanAnomaly = parseFloat(line2.substring(43, 51));

    // Calculate epoch date
    const epoch = new Date();
    epoch.setFullYear(2000 + epochYear);
    epoch.setMonth(0);
    epoch.setDate(1);
    epoch.setHours(0, 0, 0, 0);
    epoch.setDate(epoch.getDate() + epochDay - 1);

    return {
      line1,
      line2,
      epoch,
      meanMotion,
      eccentricity,
      inclination,
      rightAscension,
      argumentOfPerigee,
      meanAnomaly,
      bstar
    };
  } catch (error) {
    console.error('Error parsing TLE:', error);
    return null;
  }
} 