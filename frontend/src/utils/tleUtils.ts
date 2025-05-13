import { Cartesian3, SampledPositionProperty, TimeInterval, TimeIntervalCollection, JulianDate } from 'cesium';
import * as satellite from 'satellite.js';

export const propagateTLE = (line1: string, line2: string, startTime: Date, endTime: Date, stepMinutes: number = 1) => {
  const positionProperty = new SampledPositionProperty();
  const intervals = new TimeIntervalCollection();

  const satelliteObj = satellite.twoline2satrec(line1, line2);
  
  let currentTime = startTime;
  while (currentTime <= endTime) {
    // Calculate minutes since epoch
    const minutesSinceEpoch = (currentTime.getTime() - new Date(0).getTime()) / (1000 * 60);
    // @ts-ignore - satellite.js types are incorrect
    const position = satellite.propagate(satelliteObj, minutesSinceEpoch);
    
    if (position.position && typeof position.position !== 'boolean') {
      const cartesian = new Cartesian3(
        position.position.x * 1000, // Convert km to meters
        position.position.y * 1000,
        position.position.z * 1000
      );
      
      const time = JulianDate.fromDate(currentTime);
      positionProperty.addSample(time, cartesian);
      
      intervals.addInterval(
        new TimeInterval({
          start: time,
          stop: time,
          data: cartesian
        })
      );
    }
    
    currentTime = new Date(currentTime.getTime() + stepMinutes * 60 * 1000);
  }

  return { positionProperty, intervals };
}; 