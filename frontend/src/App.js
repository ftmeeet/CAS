import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { Viewer, Entity } from 'resium';
import { Cartesian3, Color, Ion, buildModuleUrl, JulianDate, TimeInterval, TimeIntervalCollection, SampledPositionProperty, SampledProperty, ReferenceFrame } from 'cesium';
import axios from 'axios';
import * as satellite from 'satellite.js';
import { 
  Box, 
  Button, 
  TextField, 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions,
  LinearProgress,
  Typography,
  Paper,
  Alert,
  Snackbar
} from '@mui/material';

// Import Cesium CSS
import "cesium/Source/Widgets/widgets.css";

// Set Cesium ion token
Ion.defaultAccessToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiIyMmMyYTBkNS0yMGZkLTQ3YzEtYjY3Yy1hY2M1MWQ5ZTQ0ZDkiLCJpZCI6MzAxMjQ2LCJpYXQiOjE3NDcwNDk1MjZ9.M13g4K52JwC9-AsoKIcMBBpJN0Bxy8PZpkOLD-hZwyI";

// Configure Cesium base URL and assets
window.CESIUM_BASE_URL = '/cesium';
buildModuleUrl.setBaseUrl('/cesium');

// Configure axios with better error handling
const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  validateStatus: function (status) {
    return status >= 200 && status < 500;
  }
});

// Add response interceptor for better error handling
api.interceptors.response.use(
  response => {
    if (response.status === 404) {
      console.warn('API endpoint not found:', response.config.url);
      return Promise.reject(new Error(`Endpoint not found: ${response.config.url}`));
    }
    return response;
  },
  error => {
    if (error.response) {
      console.error('API Error:', {
        status: error.response.status,
        url: error.config.url,
        data: error.response.data
      });
    } else if (error.request) {
      console.error('No response received:', error.request);
    } else {
      console.error('Error setting up request:', error.message);
    }
    return Promise.reject(error);
  }
);

// Helper function to validate TLE format
const validateTLE = (tle1, tle2) => {
  if (!tle1 || !tle2) return false;
  if (!tle1.trim().startsWith('1') || !tle2.trim().startsWith('2')) return false;
  if (tle1.trim().length !== 69 || tle2.trim().length !== 69) return false;
  return true;
};

// Helper function to convert ECI coordinates to Cartesian3
const eciToCartesian3 = (x, y, z) => {
  const xMeters = x * 1000;
  const yMeters = y * 1000;
  const zMeters = z * 1000;
  return new Cartesian3(xMeters, yMeters, zMeters);
};

// Helper function to generate CZML data for a satellite
const generateCZMLData = (satellite, startTime, endTime, timeStep = 60) => {
  try {
    const tle = satellite.twoline2satrec(satellite.TLE1, satellite.TLE2);
    if (!tle) {
      throw new Error('Failed to parse TLE data');
    }

    const positionProperty = new SampledPositionProperty(ReferenceFrame.INERTIAL);
    const velocityProperty = new SampledProperty(Cartesian3);

    let currentTime = JulianDate.clone(startTime);
    const scratchDate = new JulianDate();

    while (JulianDate.lessThanOrEquals(currentTime, endTime)) {
      const date = JulianDate.toDate(currentTime);
      const julianDate = satellite.jday(
        date.getUTCFullYear(),
        date.getUTCMonth() + 1,
        date.getUTCDate(),
        date.getUTCHours(),
        date.getUTCMinutes(),
        date.getUTCSeconds()
      );

      const positionAndVelocity = satellite.propagate(tle, julianDate);
      
      if (positionAndVelocity.position) {
        const { x, y, z } = positionAndVelocity.position;
        const position = eciToCartesian3(x, y, z);
        positionProperty.addSample(currentTime, position);

        if (positionAndVelocity.velocity) {
          const { x: vx, y: vy, z: vz } = positionAndVelocity.velocity;
          const velocity = eciToCartesian3(vx, vy, vz);
          velocityProperty.addSample(currentTime, velocity);
        }
      }

      JulianDate.addSeconds(currentTime, timeStep, scratchDate);
      JulianDate.clone(scratchDate, currentTime);
    }

    return {
      id: satellite.Name,
      name: satellite.Name,
      position: positionProperty,
      velocity: velocityProperty,
      point: {
        pixelSize: 10,
        color: Color.YELLOW
      }
    };
  } catch (error) {
    console.error(`Error generating CZML data for ${satellite.Name}:`, error);
    return null;
  }
};

function App() {
  const [satellites, setSatellites] = useState([]);
  const [czmlData, setCzmlData] = useState([]);
  const [analysisStatus, setAnalysisStatus] = useState({
    is_running: false,
    progress: 0,
    results: null,
    error: null
  });
  const [openDialog, setOpenDialog] = useState(false);
  const [tleData, setTleData] = useState({
    name: '',
    tle1: '',
    tle2: ''
  });
  const [error, setError] = useState(null);
  const viewerRef = useRef(null);

  const generateCZMLForAllSatellites = useCallback(() => {
    const startTime = JulianDate.fromDate(new Date());
    const endTime = JulianDate.addSeconds(startTime, 3600, new JulianDate()); // 1 hour of propagation

    const newCzmlData = satellites
      .map(sat => generateCZMLData(sat, startTime, endTime))
      .filter(data => data !== null);

    setCzmlData(newCzmlData);
  }, [satellites]);

  const fetchSatellites = useCallback(async () => {
    try {
      const response = await api.get('/api/satellites');
      
      if (!response.data || !Array.isArray(response.data.satellites)) {
        console.warn('Invalid satellites data format:', response.data);
        return;
      }

      const formattedSatellites = response.data.satellites
        .map(sat => ({
          ...sat,
          TLE1: sat.TLE1?.trim(),
          TLE2: sat.TLE2?.trim()
        }))
        .filter(sat => validateTLE(sat.TLE1, sat.TLE2));

      console.log('Fetched satellites:', formattedSatellites.length);
      setSatellites(formattedSatellites);
    } catch (error) {
      console.error('Error fetching satellites:', error);
      setError(`Failed to fetch satellites: ${error.message}`);
    }
  }, []);

  // Fetch satellites data
  useEffect(() => {
    fetchSatellites();
  }, [fetchSatellites]);

  // Generate CZML data when satellites change
  useEffect(() => {
    if (satellites.length > 0) {
      generateCZMLForAllSatellites();
    }
  }, [satellites, generateCZMLForAllSatellites]);

  // Poll analysis status
  useEffect(() => {
    let interval;
    if (analysisStatus.is_running) {
      interval = setInterval(async () => {
        try {
          const response = await api.get('/api/analysis-status');
          
          if (!response.data) {
            console.warn('Invalid analysis status data format:', response.data);
            return;
          }

          setAnalysisStatus(response.data);
          if (!response.data.is_running) {
            clearInterval(interval);
          }
        } catch (error) {
          console.error('Error fetching analysis status:', error);
          setError(`Failed to fetch analysis status: ${error.message}`);
          clearInterval(interval);
        }
      }, 1000);
    }
    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [analysisStatus.is_running]);

  const handleStartAnalysis = useCallback(async () => {
    try {
      const response = await api.post('/api/start-analysis');
      
      if (!response.data) {
        console.warn('Invalid start analysis response:', response.data);
        return;
      }

      setAnalysisStatus(prev => ({ ...prev, is_running: true }));
    } catch (error) {
      console.error('Error starting analysis:', error);
      setError(`Failed to start analysis: ${error.message}`);
    }
  }, []);

  const handleUploadTLE = useCallback(async () => {
    try {
      if (!tleData.name || !tleData.tle1 || !tleData.tle2) {
        setError('Please fill in all TLE fields');
        return;
      }

      const formattedTLE = {
        name: tleData.name.trim(),
        tle1: tleData.tle1.trim(),
        tle2: tleData.tle2.trim()
      };

      if (!validateTLE(formattedTLE.tle1, formattedTLE.tle2)) {
        setError('Invalid TLE format. Please check the TLE lines.');
        return;
      }

      const response = await api.post('/api/upload-tle', formattedTLE);
      
      if (!response.data) {
        console.warn('Invalid upload TLE response:', response.data);
        return;
      }

      setOpenDialog(false);
      fetchSatellites();
    } catch (error) {
      console.error('Error uploading TLE:', error);
      setError(`Failed to upload TLE data: ${error.message}`);
    }
  }, [tleData, fetchSatellites]);

  const handleTLEChange = useCallback((field) => (e) => {
    setTleData(prev => ({ ...prev, [field]: e.target.value }));
  }, []);

  const handleCloseError = () => {
    setError(null);
  };

  const handleViewerReady = useCallback((viewer) => {
    if (viewerRef.current !== viewer) {
      viewerRef.current = viewer;
      viewer.infoBox = undefined;
      
      // Set up the clock for animation
      const startTime = JulianDate.fromDate(new Date());
      const stopTime = JulianDate.addSeconds(startTime, 3600, new JulianDate());
      
      viewer.clock.startTime = startTime;
      viewer.clock.stopTime = stopTime;
      viewer.clock.currentTime = startTime;
      viewer.clock.clockRange = 1; // CLAMP_LOOP
      viewer.clock.clockStep = 1; // SYSTEM_CLOCK_MULTIPLIER
      viewer.clock.multiplier = 1;
      viewer.timeline.zoomTo(startTime, stopTime);

      // Configure Cesium assets
      viewer.scene.globe.enableLighting = false;
      viewer.scene.globe.baseColor = Color.BLACK;
      viewer.scene.globe.showGroundAtmosphere = false;
      viewer.scene.globe.showWaterEffect = false;
      viewer.scene.globe.showSkirts = false;
      viewer.scene.globe.showAtmosphere = false;
    }
  }, []);

  // Memoize viewer options
  const viewerOptions = useMemo(() => ({
    full: true,
    infoBox: false,
    baseLayerPicker: false,
    navigationHelpButton: false,
    homeButton: false,
    sceneModePicker: false,
    animation: true,
    timeline: true,
    fullscreenButton: false,
    contextOptions: {
      webgl: {
        alpha: true,
        depth: true,
        stencil: true,
        antialias: true,
        premultipliedAlpha: true,
        preserveDrawingBuffer: true,
        failIfMajorPerformanceCaveat: false
      }
    }
  }), []);

  // Memoize satellite entities
  const satelliteEntities = useMemo(() => 
    czmlData.map((data) => (
      <Entity
        key={`satellite-${data.id}`}
        name={data.name}
        position={data.position}
        point={data.point}
      />
    )), [czmlData]);

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ p: 2, display: 'flex', gap: 2 }}>
        <Button 
          variant="contained" 
          onClick={() => setOpenDialog(true)}
        >
          Upload TLE
        </Button>
        <Button 
          variant="contained" 
          onClick={handleStartAnalysis}
          disabled={analysisStatus.is_running}
        >
          Start Analysis
        </Button>
      </Box>

      {analysisStatus.is_running && (
        <Box sx={{ p: 2 }}>
          <Typography variant="body2" gutterBottom>
            Analysis in progress...
          </Typography>
          <LinearProgress variant="determinate" value={analysisStatus.progress} />
        </Box>
      )}

      {analysisStatus.results && (
        <Paper sx={{ p: 2, m: 2 }}>
          <Typography variant="h6">Analysis Results</Typography>
          <pre>{JSON.stringify(analysisStatus.results, null, 2)}</pre>
        </Paper>
      )}

      <Box sx={{ flex: 1 }}>
        <Viewer 
          {...viewerOptions}
          ref={viewerRef}
          onReady={handleViewerReady}
        >
          {satelliteEntities}
        </Viewer>
      </Box>

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)}>
        <DialogTitle>Upload TLE Data</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Satellite Name"
            fullWidth
            value={tleData.name}
            onChange={handleTLEChange('name')}
          />
          <TextField
            margin="dense"
            label="TLE Line 1"
            fullWidth
            value={tleData.tle1}
            onChange={handleTLEChange('tle1')}
            multiline
            rows={2}
            placeholder="1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927"
          />
          <TextField
            margin="dense"
            label="TLE Line 2"
            fullWidth
            value={tleData.tle2}
            onChange={handleTLEChange('tle2')}
            multiline
            rows={2}
            placeholder="2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button onClick={handleUploadTLE}>Upload</Button>
        </DialogActions>
      </Dialog>

      <Snackbar 
        open={!!error} 
        autoHideDuration={6000} 
        onClose={handleCloseError}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseError} severity="error" sx={{ width: '100%' }}>
          {error}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default App; 