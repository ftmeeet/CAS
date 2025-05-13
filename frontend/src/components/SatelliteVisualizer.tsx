import React, { useEffect, useState, useCallback, useRef, useMemo } from 'react';
import { Viewer, Entity, CameraFlyTo, CesiumComponentRef } from 'resium';
import { Cartesian3, Color, Ion, createWorldImageryAsync, IonWorldImageryStyle, JulianDate, Clock, ClockRange, ClockStep, Viewer as CesiumViewer, PolylineMaterialAppearance, PolylineGeometry, Primitive, Material, DistanceDisplayCondition, ScreenSpaceEventHandler, ScreenSpaceEventType, Camera, SceneMode, CzmlDataSource, Entity as CesiumEntity } from 'cesium';
import { parseTLE } from '../utils/tleParser';
import { propagateSatellite } from '../utils/satellitePropagator';
import { generateCZML } from '../utils/czmlGenerator';

// Set Cesium ion access token
Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiIyMmMyYTBkNS0yMGZkLTQ3YzEtYjY3Yy1hY2M1MWQ5ZTQ0ZDkiLCJpZCI6MzAxMjQ2LCJpYXQiOjE3NDcwNDk1MjZ9.M13g4K52JwC9-AsoKIcMBBpJN0Bxy8PZpkOLD-hZwyI';

const SatelliteVisualizer: React.FC = () => {
  const [satellites, setSatellites] = useState<any[]>([]);
  const [positions, setPositions] = useState<{ [key: string]: Cartesian3[] }>({});
  const [imageryProvider, setImageryProvider] = useState<any>(null);
  const [currentTime, setCurrentTime] = useState<Date>(new Date());
  const viewerRef = useRef<CesiumComponentRef<CesiumViewer>>(null);
  const lastTickTime = useRef<number>(0);
  const TICK_INTERVAL = 100; // Update every 100ms
  const [selectedSatellite, setSelectedSatellite] = useState<string | null>(null);
  const [sceneMode, setSceneMode] = useState<SceneMode>(SceneMode.SCENE3D);
  const [selectedSatellitePath, setSelectedSatellitePath] = useState<Cartesian3[]>([]);

  useEffect(() => {
    // Initialize imagery provider
    createWorldImageryAsync({
      style: IonWorldImageryStyle.AERIAL_WITH_LABELS
    }).then(provider => {
      setImageryProvider(provider);
    });

    const fetchData = async () => {
      try {
        const response = await fetch('/data/tle_data.csv');
        const text = await response.text();
        const lines = text.split('\n').filter(line => line.trim());
        
        const newSatellites = [];
        const newPositions: { [key: string]: Cartesian3[] } = {};
        const seenNames = new Set<string>();
        
        // Skip header line
        for (let i = 1; i < lines.length; i++) {
          const [name, tleLine1, tleLine2] = lines[i].split(',').map(s => s.trim());
          
          if (tleLine1 && tleLine2) {
            const tle = parseTLE(tleLine1, tleLine2);
            if (tle) {
              // Create unique key by appending index if name is duplicate
              const baseName = name;
              let uniqueName = baseName;
              let counter = 1;
              while (seenNames.has(uniqueName)) {
                uniqueName = `${baseName}_${counter}`;
                counter++;
              }
              seenNames.add(uniqueName);
              
              newSatellites.push({ name: uniqueName, tle });
              
              // Calculate positions for one complete orbit
              const positions = [];
              const startTime = new Date();
              const orbitalPeriod = 24 * 3600 / tle.meanMotion; // Period in seconds
              const numPoints = 100; // Number of points to calculate
              const timeStep = orbitalPeriod / numPoints;
              
              for (let j = 0; j < numPoints; j++) {
                const time = new Date(startTime.getTime() + j * timeStep * 1000);
                const position = propagateSatellite(tle, time);
                if (position) {
                  positions.push(new Cartesian3(position.x, position.y, position.z));
                }
              }
              newPositions[uniqueName] = positions;
            }
          }
        }
        
        setSatellites(newSatellites);
        setPositions(newPositions);

        // Generate and load CZML data
        if (viewerRef.current?.cesiumElement) {
          const czmlString = generateCZML(newSatellites);
          const dataSource = await CzmlDataSource.load(JSON.parse(czmlString));
          viewerRef.current.cesiumElement.dataSources.add(dataSource);
        }
      } catch (error) {
        console.error('Error loading TLE data:', error);
      }
    };

    fetchData();
  }, []);

  // Set up clock when viewer is available
  useEffect(() => {
    const cesiumElement = viewerRef.current?.cesiumElement;
    if (cesiumElement) {
      const clock = cesiumElement.clock;
      clock.startTime = JulianDate.fromDate(new Date());
      clock.stopTime = JulianDate.addSeconds(clock.startTime, 24 * 3600, new JulianDate());
      clock.currentTime = clock.startTime;
      clock.clockRange = ClockRange.LOOP_STOP;
      clock.clockStep = ClockStep.SYSTEM_CLOCK_MULTIPLIER;
      clock.multiplier = 1; // Speed up time by 1x
      clock.shouldAnimate = true;

      // Configure scene settings for smoother animation
      const scene = cesiumElement.scene;
      scene.globe.enableLighting = true;
      scene.globe.maximumScreenSpaceError = 2; // Lower value for better quality
      scene.globe.baseColor = Color.BLACK;
      scene.globe.atmosphereBrightnessShift = 0.2;
      scene.globe.atmosphereSaturationShift = 0.8;
      scene.globe.atmosphereHueShift = 0.0;

      // Update current time when clock ticks with throttling
      const tickHandler = () => {
        const now = Date.now();
        if (now - lastTickTime.current >= TICK_INTERVAL) {
          setCurrentTime(JulianDate.toDate(clock.currentTime));
          lastTickTime.current = now;
        }
      };
      cesiumElement.clock.onTick.addEventListener(tickHandler);

      // Cleanup
      return () => {
        cesiumElement.clock.onTick.removeEventListener(tickHandler);
      };
    }
  }, [viewerRef.current?.cesiumElement]);

  // Memoize current positions to avoid unnecessary recalculations
  const currentPositions = useMemo(() => {
    return satellites.reduce((acc, satellite) => {
      const position = propagateSatellite(satellite.tle, currentTime);
      if (position) {
        acc[satellite.name] = new Cartesian3(position.x, position.y, position.z);
      }
      return acc;
    }, {} as { [key: string]: Cartesian3 });
  }, [satellites, currentTime]);

  // Create distance display condition
  const distanceDisplayCondition = useMemo(() => {
    return new DistanceDisplayCondition(0, 10000000);
  }, []);

  // Calculate orbital path when a satellite is selected
  useEffect(() => {
    if (selectedSatellite) {
      const satellite = satellites.find(s => s.name === selectedSatellite);
      if (satellite) {
        const positions: Cartesian3[] = [];
        const startTime = new Date();
        const orbitalPeriod = 24 * 3600 / satellite.tle.meanMotion; // Period in seconds
        const numPoints = 200; // Increased number of points for smoother path
        const timeStep = orbitalPeriod / numPoints;
        
        for (let j = 0; j < numPoints; j++) {
          const time = new Date(startTime.getTime() + j * timeStep * 1000);
          const position = propagateSatellite(satellite.tle, time);
          if (position) {
            positions.push(new Cartesian3(position.x, position.y, position.z));
          }
        }
        setSelectedSatellitePath(positions);
      }
    } else {
      setSelectedSatellitePath([]);
    }
  }, [selectedSatellite, satellites]);

  // Set up camera controls
  useEffect(() => {
    const cesiumElement = viewerRef.current?.cesiumElement;
    if (cesiumElement) {
      // Configure camera settings
      const camera = cesiumElement.camera;
      
      // Set initial view
      camera.setView({
        destination: Cartesian3.fromDegrees(-75.59777, 40.03883, 10000000.0),
        orientation: {
          heading: 0.0,
          pitch: -Math.PI / 2,
          roll: 0.0
        }
      });

      // Set up camera event handlers
      const handler = new ScreenSpaceEventHandler(cesiumElement.canvas);
      
      // Handle mouse wheel for zoom
      handler.setInputAction((movement: any) => {
        const camera = cesiumElement.camera;
        const zoomFactor = 1.5;
        const direction = camera.direction;
        const movementAmount = movement.endPosition.y - movement.startPosition.y;
        
        if (movementAmount > 0) {
          camera.move(direction, -zoomFactor * camera.positionCartographic.height * 0.1);
        } else {
          camera.move(direction, zoomFactor * camera.positionCartographic.height * 0.1);
        }
      }, ScreenSpaceEventType.WHEEL);

      // Handle mouse movement for rotation and panning
      handler.setInputAction((movement: any) => {
        const camera = cesiumElement.camera;
        const windowPosition = movement.endPosition;
        const previousWindowPosition = movement.startPosition;
        
        const scene = cesiumElement.scene;
        const windowWidth = scene.canvas.clientWidth;
        const windowHeight = scene.canvas.clientHeight;
        
        const x = (windowPosition.x - previousWindowPosition.x) / windowWidth;
        const y = -(windowPosition.y - previousWindowPosition.y) / windowHeight;
        
        // Left click for rotation
        if (movement.button === 0) {
          camera.rotateRight(x * Math.PI);
          camera.rotateUp(y * Math.PI);
        }
        // Right click for panning
        else if (movement.button === 2) {
          const moveRate = camera.positionCartographic.height * 0.1;
          camera.moveRight(x * moveRate);
          camera.moveUp(y * moveRate);
        }
      }, ScreenSpaceEventType.MOUSE_MOVE);

      // Cleanup
      return () => {
        handler.destroy();
      };
    }
  }, [viewerRef.current?.cesiumElement]);

  // Handle satellite selection
  const handleEntitySelected = (entity: CesiumEntity | undefined) => {
    if (entity) {
      setSelectedSatellite(entity.name || null);
    } else {
      setSelectedSatellite(null);
    }
  };

  return (
    <div style={{ width: '100%', height: '100vh' }}>
      <Viewer
        full
        timeline={true}
        animation={true}
        baseLayerPicker={true}
        geocoder={true}
        homeButton={true}
        infoBox={true}
        sceneModePicker={true}
        selectionIndicator={true}
        navigationHelpButton={true}
        navigationInstructionsInitiallyVisible={false}
        ref={viewerRef}
        onSelectedEntityChange={handleEntitySelected}
      >
        {satellites.map((satellite) => {
          const isSelected = selectedSatellite === satellite.name;
          const tle = satellite.tle;
          
          // Create description HTML for info box
          const description = `
            <h2>${satellite.name}</h2>
            <table>
              <tr><td>Epoch:</td><td>${tle.epoch.toLocaleString()}</td></tr>
              <tr><td>Mean Motion:</td><td>${tle.meanMotion} rev/day</td></tr>
              <tr><td>Eccentricity:</td><td>${tle.eccentricity}</td></tr>
              <tr><td>Inclination:</td><td>${tle.inclination}°</td></tr>
              <tr><td>Right Ascension:</td><td>${tle.rightAscension}°</td></tr>
              <tr><td>Argument of Perigee:</td><td>${tle.argumentOfPerigee}°</td></tr>
              <tr><td>Mean Anomaly:</td><td>${tle.meanAnomaly}°</td></tr>
            </table>
          `;

          return (
            <React.Fragment key={satellite.name}>
              <Entity
                name={satellite.name}
                position={currentPositions[satellite.name]}
                description={description}
                point={{
                  pixelSize: isSelected ? 5 : 2,
                  color: isSelected ? Color.RED : Color.YELLOW,
                  outlineColor: Color.WHITE,
                  outlineWidth: 1
                }}
              />
              {isSelected && selectedSatellitePath.length > 0 && (
                <Entity
                  name={`${satellite.name}_path`}
                  polyline={{
                    positions: selectedSatellitePath,
                    width: 2,
                    material: Color.YELLOW.withAlpha(0.8),
                    clampToGround: false
                  }}
                />
              )}
            </React.Fragment>
          );
        })}
      </Viewer>
    </div>
  );
};

export default SatelliteVisualizer;