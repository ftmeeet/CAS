from sklearn.ensemble import RandomForestClassifier
import pandas as pd
import joblib

X = pd.read_csv("X_features.csv")
y = pd.read_csv("y_labels.csv")

model = RandomForestClassifier(n_estimators=100)
model.fit(X, y.values.ravel())

joblib.dump(model, "conjunction_predictor.pkl")

print("Model training complete ✅")