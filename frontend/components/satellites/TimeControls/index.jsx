import { useState, useEffect } from "react";
import styles from "./index.module.scss";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlay, faPause, faStop } from '@fortawesome/free-solid-svg-icons';

const TimeControls = ({
  handleMultiplierChange,
  isNavOpen,
  isAboutOpen
}) => {
  const [inputMultiplier, setInputMultiplier] = useState(2); // Default to 2x
  const [exponentialMultiplier, setExponentialMultiplier] = useState(2); // Default to 2x
  const [currentTime, setCurrentTime] = useState(new Date());
  const range = 50; // Maximum speed of 50x

  // Initialize with default speed only after component is mounted
  useEffect(() => {
    if (handleMultiplierChange) {
      handleMultiplierChange(2);
    }
  }, [handleMultiplierChange]);

  useEffect(() => {
    let intervalId;
    if (exponentialMultiplier !== 0) {
      // Update time more frequently for faster speeds
      const updateInterval = Math.max(100, 1000 / Math.abs(exponentialMultiplier));
      intervalId = setInterval(() => {
        setCurrentTime(prevTime => {
          const newTime = new Date(prevTime);
          // Add seconds based on the multiplier
          newTime.setSeconds(newTime.getSeconds() + exponentialMultiplier);
          return newTime;
        });
      }, updateInterval);
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [exponentialMultiplier]);

  const handleTimeChange = (e) => {
    setInputMultiplier(e.target.value);

    let expMultiplier = 0;
    if (Math.abs(e.target.value) < 2) {
      // set time as stopped
      expMultiplier = 0;
    } else {
      // calculate exponentially rising multiplier, capped at 50x
      expMultiplier = Math.round(Math.exp((Math.log(range*100)/range) * Math.abs(e.target.value)));
      expMultiplier = Math.min(expMultiplier, 50); // Cap at 50x
      if (e.target.value < 0) {
        expMultiplier = expMultiplier * -1;
      }
    }

    setExponentialMultiplier(expMultiplier);
    if (handleMultiplierChange) {
      handleMultiplierChange(expMultiplier);
    }
  };

  const stopTime = () => {
    setInputMultiplier(0);
    setExponentialMultiplier(0);
    if (handleMultiplierChange) {
      handleMultiplierChange(0);
    }
  };

  const formatTime = (date) => {
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const formatDate = (date) => {
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div
      className={`
        ${styles["time-controls"]}
        ${isNavOpen ? styles["nav-open"] : ""}
        ${isAboutOpen ? styles["about-open"] : ""}
      `}
    >
      <div className={styles["time-display"]}>
        <div className={styles["date"]}>{formatDate(currentTime)}</div>
        <div className={styles["time"]}>{formatTime(currentTime)}</div>
      </div>
      <div className={styles["time-text"]}>
        <div>
          <FontAwesomeIcon icon={exponentialMultiplier === 0 ? faPause : faPlay} />
          <span className={styles["bold"]}>
            {exponentialMultiplier === 0 ? "Paused" : `${exponentialMultiplier}x`}
          </span>
        </div>
        {exponentialMultiplier !== 0 && (
          <button
            className={styles["stop-time"]}
            onClick={stopTime}
            title="Stop time"
          >
            <FontAwesomeIcon icon={faStop} />
          </button>
        )}
      </div>
      <input
        type="range"
        className={styles["time-range"]}
        min={-range}
        max={range}
        value={inputMultiplier}
        onChange={handleTimeChange}
        title="Adjust time flow"
      />
    </div>
  );
};

export default TimeControls;
