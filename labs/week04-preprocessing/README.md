# Week 04 Lab

Build a reusable preprocessing pipeline (sklearn Pipeline/ColumnTransformer); PCA as a worked stateful-transform example.

Starter files for this week's lab will be added here before the lab session
(pulled into your repo via `git fetch upstream && git merge upstream/main`,
as introduced in the Week 1 lab).

## Reflection

**Why close accuracy does not mean the leak was harmless.** The original script printed 0.6375 and the fixed Pipeline also printed 0.6375. The leak changes what the evaluation means, not necessarily the number: once test rows have shaped the imputer and scaler, the test set is no longer unseen data, so the score cannot be trusted. On smaller data, skewed columns or stronger transforms, the same mistake can inflate results a lot, and the metric gives no warning.

**Which lines caused the leak, and how I proved it.** `imputer.fit_transform(X[NUMERIC_FEATURES])`, `scaler.fit_transform(X[NUMERIC_FEATURES])` and `pd.get_dummies(X, ...)` all ran on the full dataset before `train_test_split`. I proved it by comparing fitted state, not accuracy: the scaler fit on all 400 rows learned an annual_income mean of 43761.45, while a scaler fit only on the 320 training rows learned 43213.02 (all five means differed).

**Serving code that recomputes its own scaler from the last hour of requests.** That is training-serving skew: the model was trained on features scaled with training statistics, but production would scale the same input differently depending on recent traffic. Leakage makes the offline evaluation optimistic; skew makes production predictions wrong even when the evaluation was clean. The fix is to save the fitted Pipeline and load it unchanged at serving time.

**PCA's state.** Fitting PCA learns the centering mean and the component directions (`components_`) from the training data; the classifier's weights are tied to those exact axes. A fresh `PCA().fit_transform()` on incoming requests would find different directions (or flipped signs, or a different order), so the classifier would receive numbers on axes it never saw; with a single request PCA cannot even be fit. Serving must reuse the fitted pca inside the saved Pipeline.

**Results.** Leaky starter: 0.6375. Fixed Pipeline: 0.6375. With PCA(5): 0.6375, explained variance 0.350 / 0.169 / 0.157 / 0.096 / 0.066. GridSearchCV best params {C: 10, n_components: 8}, best CV accuracy 0.7062, final test accuracy 0.65.
