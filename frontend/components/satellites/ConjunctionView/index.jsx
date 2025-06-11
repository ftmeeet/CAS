import React, { useEffect, useState } from 'react';
import { useDispatch } from 'react-redux';
import styles from './styles.module.css';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faExclamationTriangle, faTimes } from '@fortawesome/free-solid-svg-icons';

const ConjunctionView = ({ viewer }) => {
  const [conjunctions, setConjunctions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showDialog, setShowDialog] = useState(false);
  const [analysisComplete, setAnalysisComplete] = useState(false);
  const dispatch = useDispatch();

  useEffect(() => {
    const fetchConjunctions = async () => {
      try {
        setLoading(true);
        const response = await fetch('http://localhost:8000/api/conjunctions');
        if (!response.ok) {
          throw new Error('Failed to fetch conjunction data');
        }
        const data = await response.json();
        setConjunctions(data);
        setLoading(false);
        setAnalysisComplete(true);
        
        // Show dialog when data is loaded and there are high-risk conjunctions
        if (data.length > 0 && data.some(c => c.collision_probability > 0.7)) {
          setShowDialog(true);
        }
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };

    // Only fetch conjunctions if analysis is complete
    if (analysisComplete) {
      fetchConjunctions();
    }
  }, [analysisComplete]);

  useEffect(() => {
    if (!viewer || !conjunctions.length) return;

    // Clear existing conjunction entities
    const existingEntities = viewer.entities.values.filter(
      entity => entity.conjunction
    );
    existingEntities.forEach(entity => viewer.entities.remove(entity));

    // Add new conjunction entities
    conjunctions.forEach(conjunction => {
      // Determine color based on collision probability
      let color;
      if (conjunction.collision_probability > 0.7) {
        color = Cesium.Color.RED;
      } else if (conjunction.collision_probability > 0.3) {
        color = Cesium.Color.ORANGE;
      } else {
        color = Cesium.Color.GREEN;
      }

      // Create a line entity to show the conjunction
      viewer.entities.add({
        name: `Conjunction: ${conjunction.satellite1} - ${conjunction.satellite2}`,
        polyline: {
          positions: new Cesium.CallbackProperty(() => {
            const sat1 = viewer.entities.values.find(
              e => e.name === conjunction.satellite1
            );
            const sat2 = viewer.entities.values.find(
              e => e.name === conjunction.satellite2
            );
            if (sat1 && sat2) {
              return [sat1.position.getValue(), sat2.position.getValue()];
            }
            return [];
          }, false),
          width: 2,
          material: new Cesium.ColorMaterialProperty(
            color.withAlpha(0.5)
          ),
        },
        conjunction: true,
        properties: {
          distance: conjunction.distance_km,
          probability: conjunction.collision_probability,
          time: conjunction.conjunction_time,
          velocity: conjunction.relative_velocity_km_s,
        },
      });
    });
  }, [viewer, conjunctions]);

  const getRiskLevel = (probability) => {
    if (probability > 0.7) return 'highRisk';
    if (probability > 0.3) return 'mediumRisk';
    return 'lowRisk';
  };

  const getRiskLabel = (probability) => {
    if (probability > 0.7) return 'HIGH RISK';
    if (probability > 0.3) return 'MEDIUM RISK';
    return 'LOW RISK';
  };

  if (loading) {
    return <div className={styles.loading}>Loading conjunction data...</div>;
  }

  if (error) {
    return <div className={styles.error}>Error: {error}</div>;
  }

  if (!analysisComplete) {
    return null;
  }

  const highRiskCount = conjunctions.filter(c => c.collision_probability > 0.7).length;
  const mediumRiskCount = conjunctions.filter(c => c.collision_probability > 0.3 && c.collision_probability <= 0.7).length;
  const lowRiskCount = conjunctions.filter(c => c.collision_probability <= 0.3).length;

  return (
    <>
      {showDialog && (
        <div className={styles.dialogOverlay}>
          <div className={styles.dialog}>
            <div className={styles.dialogHeader}>
              <h3>
                <FontAwesomeIcon icon={faExclamationTriangle} /> Analysis Complete
              </h3>
              <button 
                className={styles.closeButton}
                onClick={() => setShowDialog(false)}
              >
                <FontAwesomeIcon icon={faTimes} />
              </button>
            </div>
            <div className={styles.dialogContent}>
              <h4>Conjunction Analysis Results</h4>
              <div className={styles.summary}>
                <p>Total Conjunctions Found: {conjunctions.length}</p>
                <p className={styles.highRisk}>
                  High Risk Conjunctions: {highRiskCount}
                  {highRiskCount > 0 && ' ⚠️'}
                </p>
                <p className={styles.mediumRisk}>
                  Medium Risk Conjunctions: {mediumRiskCount}
                </p>
                <p className={styles.lowRisk}>
                  Low Risk Conjunctions: {lowRiskCount}
                </p>
              </div>
              <div className={styles.dialogActions}>
                <button 
                  className={styles.viewDetailsButton}
                  onClick={() => setShowDialog(false)}
                >
                  View Details
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className={styles.container}>
        <h3>
          <FontAwesomeIcon icon={faExclamationTriangle} /> Conjunctions
          {highRiskCount > 0 && <span className={styles.riskIndicator}>⚠️ {highRiskCount} High Risk</span>}
        </h3>
        <div className={styles.conjunctionList}>
          {conjunctions.map((conjunction, index) => {
            const riskLevel = getRiskLevel(conjunction.collision_probability);
            return (
              <div key={index} className={`${styles.conjunctionItem} ${styles[riskLevel]}`}>
                <div className={styles.satellites}>
                  {conjunction.satellite1} - {conjunction.satellite2}
                  <span className={styles.riskIndicator}>
                    {getRiskLabel(conjunction.collision_probability)}
                  </span>
                </div>
                <div className={styles.details}>
                  <div>Distance: {conjunction.distance_km.toFixed(2)} km</div>
                  <div>
                    Probability: {(conjunction.collision_probability * 100).toFixed(2)}%
                  </div>
                  <div>Time: {new Date(conjunction.conjunction_time).toLocaleString()}</div>
                  <div>
                    Relative Velocity: {conjunction.relative_velocity_km_s.toFixed(2)} km/s
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
};

export default ConjunctionView; 