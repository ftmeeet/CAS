import React, { useState, useEffect } from 'react';
import styles from './styles.module.css';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlay, faStop, faSpinner, faChartBar } from '@fortawesome/free-solid-svg-icons';
import AnalysisResults from '../AnalysisResults';

const AnalysisControls = ({ onAnalysisComplete }) => {
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('');
  const [error, setError] = useState(null);
  const [processedPairs, setProcessedPairs] = useState(0);
  const [totalPairs, setTotalPairs] = useState(0);
  const [showResults, setShowResults] = useState(false);
  const [analysisResults, setAnalysisResults] = useState(null);

  const checkServerStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/analysis-status');
      if (!response.ok) {
        throw new Error('Failed to fetch status');
      }
      const data = await response.json();
      console.log('Analysis status:', data);
      
      setIsRunning(data.is_running);
      setProgress(data.progress);
      setMessage(data.message);
      
      // Extract processed pairs from status message
      const pairsMatch = data.message.match(/(\d+)\/(\d+) pairs/);
      if (pairsMatch) {
        setProcessedPairs(parseInt(pairsMatch[1]));
        setTotalPairs(parseInt(pairsMatch[2]));
      }
      
      // Check if analysis is complete
      if (!data.is_running && data.progress === 100) {
        console.log('Analysis completed, fetching results...');
        await fetchResults();
        onAnalysisComplete && onAnalysisComplete();
        return true; // Indicate successful check
      }
      return true; // Indicate successful check
    } catch (error) {
      console.error('Error checking server status:', error);
      return false; // Indicate failed check
    }
  };

  useEffect(() => {
    let intervalId;
    let retryCount = 0;
    const maxRetries = 30;
    const retryDelay = 2000; // 2 seconds

    const checkStatusWithRetry = async () => {
      const success = await checkServerStatus();
      if (!success && retryCount < maxRetries) {
        retryCount++;
        console.log(`Retrying... (${retryCount}/${maxRetries})`);
        setTimeout(checkStatusWithRetry, retryDelay);
      } else if (!success) {
        setError('Failed to connect to server');
        clearInterval(intervalId);
      }
    };

    if (isRunning) {
      // Check status immediately and then every 5 seconds
      checkStatusWithRetry();
      intervalId = setInterval(checkStatusWithRetry, 5000);
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [isRunning, onAnalysisComplete]);

  const startAnalysis = async () => {
    try {
      setError(null);
      setProcessedPairs(0);
      setTotalPairs(0);
      setAnalysisResults(null);
      setShowResults(false);
      const response = await fetch('http://localhost:8000/api/start-analysis', {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error('Failed to start analysis');
      }
      
      setIsRunning(true);
      setProgress(0);
      setMessage('Starting analysis...');
    } catch (err) {
      setError(err.message);
    }
  };

  const stopAnalysis = async () => {
    try {
      setError(null);
      const response = await fetch('http://localhost:8000/api/stop-analysis', {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error('Failed to stop analysis');
      }
      
      setIsRunning(false);
      setProgress(0);
      setMessage('Server restarting...');

      // Wait for server to restart and reconnect
      let retries = 0;
      const maxRetries = 30;
      const checkServer = async () => {
        try {
          const statusResponse = await fetch('http://localhost:8000/api/analysis-status');
          if (statusResponse.ok) {
            const data = await statusResponse.json();
            setMessage('Server restarted successfully');
            setError(null);
            return true;
          }
        } catch (err) {
          if (retries < maxRetries) {
            retries++;
            setTimeout(checkServer, 1000);
          } else {
            setError('Failed to reconnect to server after restart');
            return false;
          }
        }
      };

      // Start checking for server restart
      setTimeout(checkServer, 2000);
    } catch (err) {
      // Don't show error if the server is restarting
      if (!err.message.includes('Failed to fetch')) {
        setError(err.message);
      }
      setIsRunning(false);
      setProgress(0);
      setMessage('Server restarting...');
      
      // Still try to reconnect even if the initial request failed
      let retries = 0;
      const maxRetries = 30;
      const checkServer = async () => {
        try {
          const statusResponse = await fetch('http://localhost:8000/api/analysis-status');
          if (statusResponse.ok) {
            const data = await statusResponse.json();
            setMessage('Server restarted successfully');
            setError(null);
            return true;
          }
        } catch (err) {
          if (retries < maxRetries) {
            retries++;
            setTimeout(checkServer, 1000);
          } else {
            setError('Failed to reconnect to server after restart');
            return false;
          }
        }
      };

      // Start checking for server restart
      setTimeout(checkServer, 2000);
    }
  };

  const fetchResults = async () => {
    try {
      console.log('Fetching analysis results...');
      const response = await fetch('http://localhost:8000/api/analysis-results');
      if (!response.ok) {
        const errorData = await response.json();
        console.error('Error fetching results:', errorData);
        throw new Error(errorData.detail || 'Failed to fetch results');
      }
      const data = await response.json();
      console.log('Analysis results received:', data);
      setAnalysisResults(data);
      setShowResults(true);
    } catch (error) {
      console.error('Error in fetchResults:', error);
      setError(error.message);
    }
  };

  const handleViewResults = async () => {
    await fetchResults();
  };

  return (
    <>
      <div className={styles.container}>
        <div className={styles.controls}>
          {!isRunning ? (
            <div className={styles.buttonGroup}>
              <button 
                className={styles.startButton}
                onClick={startAnalysis}
                disabled={isRunning}
              >
                <FontAwesomeIcon icon={faPlay} /> Start Analysis
              </button>
              <button 
                className={styles.viewButton}
                onClick={handleViewResults}
                disabled={isRunning}
              >
                <FontAwesomeIcon icon={faChartBar} /> View Results
              </button>
            </div>
          ) : (
            <button 
              className={styles.stopButton}
              onClick={stopAnalysis}
            >
              <FontAwesomeIcon icon={faStop} /> Stop Analysis
            </button>
          )}
        </div>

        {isRunning && (
          <div className={styles.progressContainer}>
            <div className={styles.progressBar}>
              <div 
                className={styles.progressFill}
                style={{ width: `${progress}%` }}
              />
            </div>
            <div className={styles.progressInfo}>
              <span className={styles.progressText}>
                {progress}%
              </span>
              {isRunning && (
                <FontAwesomeIcon 
                  icon={faSpinner} 
                  spin 
                  className={styles.spinner}
                />
              )}
            </div>
            {totalPairs > 0 && (
              <div className={styles.pairsInfo}>
                Processing pairs: {processedPairs} / {totalPairs}
              </div>
            )}
          </div>
        )}

        {message && (
          <div className={styles.message}>
            {message}
          </div>
        )}

        {error && (
          <div className={styles.error}>
            Error: {error}
          </div>
        )}
      </div>

      {showResults && (
        <AnalysisResults 
          results={analysisResults} 
          onClose={() => setShowResults(false)} 
        />
      )}
    </>
  );
};

export default AnalysisControls; 