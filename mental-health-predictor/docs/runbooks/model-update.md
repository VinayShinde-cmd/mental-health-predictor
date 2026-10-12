# Runbook: update or replace the model

The model is a pickled scikit-learn pipeline. Unpickling runs code, so only ever load a file you made.

1. **Export** in the notebook: `joblib.dump(random_search.best_estimator_, "Mental_Health_Model2.pkl")`.
   Note the version: `import sklearn; print(sklearn.__version__)`.
2. **Match versions.** Set `scikit-learn` (and `pandas`, `numpy`) in `backend/requirements.txt` to those
   used for training. The backend refuses to start on a mismatch, naming both versions.
3. **Check the columns.** The pipeline must expect exactly these 12 columns: Age, Gender, Grouped_country,
   Academic_Level, Most_Used_Platform, Purpose_Of_Use, Avg_Daily_Usage_Hours, Daily_Unlocks, Study_Hours,
   Physical_Activity_Hours, Sleep_Hours_Per_Night, Stress_Level, and keep the step names `preprocessor` and
   the one-hot transformer `Normal` (as in the notebook). If you rename anything, update
   `backend/app/domain/features.py` and `services/model_service.py`.
4. **Hash it:** `sha256sum Mental_Health_Model2.pkl` (Windows: `certutil -hashfile Mental_Health_Model2.pkl SHA256`).
5. **Test locally:** put the file at `backend/models/`, set `MODEL_PATH` and `MODEL_SHA256` in `backend/.env`,
   start the backend, open the form, run an estimate, check `/api/health`.
6. **Get it to the host.** The file is deliberately not in git. Pick one (open decision for the owner):
   a persistent disk or secret file on the host, a private storage bucket downloaded at build time, or Git LFS
   in a private repo. Whatever you pick, the file must come only from a place you control.
7. **Deploy** with the new `MODEL_SHA256` and `MODEL_PATH`. The app will not start if the hash differs.
8. **Verify:** `/api/health` is 200, a test estimate looks sensible, and `model_id` in the response (first 12
   characters of the hash) matches what you expect.

**Roll back** by redeploying the previous file and its previous `MODEL_SHA256`; keep the last good file.
