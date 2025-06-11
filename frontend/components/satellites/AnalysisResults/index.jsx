import React from 'react';
import styles from './styles.module.css';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTimes } from '@fortawesome/free-solid-svg-icons';

const AnalysisResults = ({ results, onClose }) => {
  if (!results) return null;

  // Check if we have any actual results
  const hasResults = results.total_pairs > 0;

  return (
    <div className={styles.overlay}>
      <div className={styles.modal}>
        <button className={styles.closeButton} onClick={onClose}>
          <FontAwesomeIcon icon={faTimes} />
        </button>
        
        <h2 className={styles.title}>Analysis Results</h2>
        
        {hasResults ? (
          <>
            <div className={styles.section}>
              <h3>Summary</h3>
              <p>Total pairs processed: {results.total_pairs}</p>
              <p>Successful predictions: {results.successful_predictions}</p>
            </div>

            <div className={styles.section}>
              <h3>Distance Summary</h3>
              <p>Potential conjunctions (distance &lt; {results.threshold_km}km): {results.potential_conjunctions}</p>
              <p>Average actual distance: {results.avg_distance.toFixed(2)} km</p>
              <p>Minimum actual distance: {results.min_distance.toFixed(2)} km</p>
              <p>Maximum actual distance: {results.max_distance.toFixed(2)} km</p>
            </div>

            <div className={styles.section}>
              <h3>Velocity Summary</h3>
              <p>Average relative velocity: {results.avg_velocity.toFixed(2)} km/s</p>
              <p>Maximum relative velocity: {results.max_velocity.toFixed(2)} km/s</p>
            </div>

            <div className={styles.section}>
              <h3>Risk Summary</h3>
              <p>Average risk value: {results.avg_risk.toFixed(4)}</p>
              <p>Average collision probability: {(results.avg_probability * 100).toFixed(2)}%</p>
              <p>High risk pairs: {results.high_risk_pairs}</p>
              <p>Medium risk pairs: {results.medium_risk_pairs}</p>
              <p>Low risk pairs: {results.low_risk_pairs}</p>
            </div>

            {results.conjunctions && results.conjunctions.length > 0 && (
              <div className={styles.section}>
                <h3>Potential Conjunctions</h3>
                <div className={styles.conjunctionsList}>
                  {results.conjunctions.map((conj, index) => (
                    <div key={index} className={styles.conjunction}>
                      <p><strong>{conj.User_Satellite} - {conj.Database_Satellite}</strong></p>
                      <p>Actual Distance: {conj.Actual_Distance_km.toFixed(2)} km</p>
                      {conj.Relative_Velocity_km_s && (
                        <p>Relative Velocity: {conj.Relative_Velocity_km_s.toFixed(2)} km/s</p>
                      )}
                      <p>Risk Value: {conj.Risk_Value.toFixed(4)}</p>
                      <p>Collision Probability: {(conj.Collision_Probability * 100).toFixed(2)}%</p>
                      <p>Risk Level: {conj.Risk_Level}</p>
                      {conj.Conjunction_Time && (
                        <p>Conjunction Time: {conj.Conjunction_Time}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : (
          <div className={styles.section}>
            <p>No analysis results available yet. Please run an analysis to see results.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalysisResults; 