import { TLE } from './tleParser';
import { propagateSatellite } from './satellitePropagator';

interface SatelliteData {
  name: string;
  tle: TLE;
}

interface CzmlPacket {
  id: string;
  name?: string;
  version?: string;
  clock?: {
    interval: string;
    currentTime: string;
    multiplier: number;
    range: string;
    step: string;
  };
  availability?: string;
  position?: {
    epoch: string;
    interpolationAlgorithm: string;
    interpolationDegree: number;
    referenceFrame: string;
    cartesian: number[];
  };
  point?: {
    pixelSize: number;
    color: { rgba: number[] };
    outlineColor: { rgba: number[] };
    outlineWidth: number;
    scaleByDistance: {
      near: number;
      nearValue: number;
      far: number;
      farValue: number;
    };
  };
  path?: {
    resolution: number;
    material: {
      polylineGlow: {
        glowPower: number;
        color: { rgba: number[] };
      };
    };
    width: number;
    leadTime: number;
    trailTime: number;
    show: boolean;
    distanceDisplayCondition: {
      near: number;
      far: number;
    };
  };
}

export function generateCZML(satellites: SatelliteData[]): string {
  const startTime = new Date();
  const stopTime = new Date(startTime.getTime() + 24 * 3600 * 1000); // 24 hours from now

  // Create the CZML document
  const czml: CzmlPacket[] = [
    {
      id: "document",
      name: "Satellite Visualization",
      version: "1.0",
      clock: {
        interval: `${startTime.toISOString()}/${stopTime.toISOString()}`,
        currentTime: startTime.toISOString(),
        multiplier: 60, // Speed up time by 60x
        range: "LOOP_STOP",
        step: "SYSTEM_CLOCK_MULTIPLIER"
      }
    }
  ];

  // Add each satellite
  satellites.forEach((satellite, index) => {
    const orbitalPeriod = 24 * 3600 / satellite.tle.meanMotion; // Period in seconds
    const numPoints = 300; // Increased number of points for smoother interpolation
    const timeStep = orbitalPeriod / numPoints;
    
    // Calculate positions for one orbit with improved sampling
    const positions: any[] = [];
    const startDate = new Date(startTime);
    
    for (let i = 0; i < numPoints; i++) {
      const time = new Date(startDate.getTime() + i * timeStep * 1000);
      const position = propagateSatellite(satellite.tle, time);
      if (position) {
        positions.push({
          time: time.toISOString(),
          position: {
            epoch: startTime.toISOString(),
            cartesian: [position.x, position.y, position.z]
          }
        });
      }
    }

    // Add the satellite packet with improved settings
    czml.push({
      id: satellite.name,
      name: satellite.name,
      availability: `${startTime.toISOString()}/${stopTime.toISOString()}`,
      position: {
        epoch: startTime.toISOString(),
        interpolationAlgorithm: "LAGRANGE",
        interpolationDegree: 9, // Increased for smoother movement
        referenceFrame: "INERTIAL",
        cartesian: positions.map(p => p.position.cartesian).flat()
      },
      point: {
        pixelSize: 4,
        color: {
          rgba: [255, 255, 0, 255]
        },
        outlineColor: {
          rgba: [255, 255, 255, 255]
        },
        outlineWidth: 1,
        scaleByDistance: {
          near: 1000,
          nearValue: 4,
          far: 10000000,
          farValue: 2
        }
      },
      path: {
        resolution: 1,
        material: {
          polylineGlow: {
            glowPower: 0.25,
            color: {
              rgba: [255, 255, 0, 128]
            }
          }
        },
        width: 2,
        leadTime: orbitalPeriod * 0.1, // Show 10% of the orbit ahead
        trailTime: orbitalPeriod * 0.9, // Show 90% of the orbit behind
        show: true,
        distanceDisplayCondition: {
          near: 0,
          far: 10000000
        }
      }
    });
  });

  return JSON.stringify(czml);
}