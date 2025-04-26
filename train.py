import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
import joblib # Added for saving the model


train_data = pd.read_csv('train_data.csv')
test_data = pd.read_csv('test_data.csv')

# Removed interpolate calls on the raw train_data

df_copy = train_data[['event_id','time_to_tca','risk','max_risk_estimate', 'max_risk_scaling', 'miss_distance', 'relative_speed', 'relative_position_r', 'relative_position_t', 'relative_position_n', 'relative_velocity_r', 'relative_velocity_t', 'relative_velocity_n','t_time_lastob_start', 't_time_lastob_end', 't_recommended_od_span', 't_actual_od_span', 't_obs_available', 't_obs_used', 't_residuals_accepted', 't_weighted_rms', 't_rcs_estimate', 't_cd_area_over_mass', 't_cr_area_over_mass','t_sedr', 't_j2k_sma', 't_j2k_ecc', 't_j2k_inc', 't_ct_r', 't_cn_r', 't_cn_t', 't_crdot_r', 't_crdot_t', 't_crdot_n', 't_ctdot_r', 't_ctdot_t', 't_ctdot_n', 't_ctdot_rdot', 't_cndot_r','t_cndot_t', 't_cndot_n', 't_cndot_rdot','t_cndot_tdot', 'c_time_lastob_start', 'c_time_lastob_end','c_recommended_od_span', 'c_actual_od_span', 'c_obs_available', 'c_obs_used', 'c_residuals_accepted', 'c_weighted_rms', 'c_cd_area_over_mass','c_cr_area_over_mass', 'c_sedr', 'c_j2k_sma', 'c_j2k_ecc', 'c_j2k_inc', 'c_ct_r', 'c_cn_r', 'c_cn_t', 'c_crdot_r', 'c_crdot_t', 'c_crdot_n', 'c_ctdot_r', 'c_ctdot_t', 'c_ctdot_n', 'c_ctdot_rdot', 'c_cndot_r', 'c_cndot_t', 'c_cndot_n','c_ctdot_rdot', 'c_cndot_r', 'c_cndot_t', 'c_cndot_n', 'c_cndot_rdot', 'c_cndot_tdot', 't_span', 'c_span', 't_h_apo', 't_h_per', 'c_h_apo', 'c_h_per', 'geocentric_latitude', 'azimuth', 'mahalanobis_distance','t_sigma_r', 'c_sigma_r', 't_sigma_t', 'c_sigma_t', 't_sigma_n', 'c_sigma_n', 't_sigma_rdot', 'c_sigma_rdot', 't_sigma_tdot', 'c_sigma_tdot', 't_sigma_ndot', 'c_sigma_ndot', 'F10', 'F3M', 'SSN', 'AP']]

# Select only numeric columns to remove any object types
df_copy = df_copy.select_dtypes(include=np.number)

# Interpolate *after* selecting numeric columns
df_copy = df_copy.interpolate()

x = df_copy.drop(['risk'], axis=1)
y = df_copy.risk

# REMOVED saving feature list here

x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.4, random_state=100)
print(f"DEBUG: Shape of x_train after split: {x_train.shape}") # DEBUG
print(f"DEBUG: Shape of x_test after split: {x_test.shape}")   # DEBUG

# create regressor object
regressor = RandomForestRegressor(n_estimators = 100, random_state = 0)

print("Starting model training...")
regressor.fit(x_train,y_train)
print("Model training finished.")
print(f"DEBUG: Model n_features_in_ after fitting: {regressor.n_features_in_}") # DEBUG

# --- Save the exact feature list the model ACTUALLY used ---
feature_list_filename = 'training_features.joblib'
actual_training_features = list(regressor.feature_names_in_)
print(f"DEBUG: Features being saved (Count: {len(actual_training_features)}): {actual_training_features[:5]}...{actual_training_features[-5:]}") # DEBUG ++ 
joblib.dump(actual_training_features, feature_list_filename)
print(f"List of {len(actual_training_features)} actual training features saved to {feature_list_filename}")
# ---

# Save the trained model to a file
model_filename = 'random_forest_risk_model.joblib'
joblib.dump(regressor, model_filename)
print(f"Trained model saved to {model_filename}")

print("Calculating performance metrics...")
predR = regressor.predict(x_test)
rmseR = np.sqrt(mean_squared_error(y_test, predR))
mseR=mean_squared_error(y_test,predR)
maeR=mean_absolute_error(y_test,predR)
r2R=r2_score(y_test,predR)
result1=[rmseR,mseR,maeR,r2R]
df_R = pd.DataFrame({'RandomForestRegressor':result1},index=['RMSE:','MSE:','MAE:','R2-score:'])

print("Training Results:")
print(df_R)