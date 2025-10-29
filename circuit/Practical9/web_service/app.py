from flask import Flask, render_template, request, redirect, jsonify
import requests
import pickle
import numpy as np
import os
from circuit_breaker import handle_db_failure, db_circuit_breaker
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
model_path = os.path.join('model.pkl')
with open(model_path, 'rb') as f:
    model = pickle.load(f)

DB_SERVICE_URL = "http://dbapp_container:5001/record"

iris_classes = {
    0: 'Setosa',
    1: 'Versicolor',
    2: 'Virginica'
}

prediction_cache = []


@handle_db_failure
def save_to_database(data):
    response = requests.post(DB_SERVICE_URL, data=data, timeout=5)
    response.raise_for_status()
    return response.json()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def get_from_database():
    response = requests.get(DB_SERVICE_URL, timeout=5)
    response.raise_for_status()
    return response.json()


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        sepal_length = float(request.form['sepal_length'])
        sepal_width = float(request.form['sepal_width'])
        petal_length = float(request.form['petal_length'])
        petal_width = float(request.form['petal_width'])

        features = np.array(
            [sepal_length, sepal_width, petal_length, petal_width])
        features = features.reshape(1, -1)
        pred = model.predict(features)
        flower_name = iris_classes[pred[0]]

        prediction_data = {
            "sepal_length": sepal_length,
            "sepal_width": sepal_width,
            "petal_length": petal_length,
            "petal_width": petal_width,
            "predicted_class": flower_name
        }

        result = save_to_database(prediction_data)

        if result.get("cached"):
            prediction_cache.append(prediction_data)
            logger.warning("Prediction saved to local cache")

        return render_template('index.html', prediction=flower_name, db_status=result.get("status"))
    else:
        return redirect(location='/')


@app.route('/show-result')
def show_result():
    try:
        records = get_from_database()
        return render_template('show-result.html', records=records, degraded=False)
    except Exception as e:
        logger.error(f"Failed to fetch records: {str(e)}")
        return render_template('show-result.html', records=prediction_cache, degraded=True)


@app.route('/health')
def health():
    db_status = "healthy" if db_circuit_breaker.current_state == "closed" else "degraded"
    return jsonify({
        "status": "up",
        "circuit_breaker": {
            "state": db_circuit_breaker.current_state,
            "fail_count": db_circuit_breaker.fail_counter,
            "db_service": db_status
        }
    })


@app.route('/metrics')
def metrics():
    return jsonify({
        "circuit_breaker_state": db_circuit_breaker.current_state,
        "failure_count": db_circuit_breaker.fail_counter,
        "success_count": db_circuit_breaker.success_counter,
        "cache_size": len(prediction_cache)
    })


if __name__ == '__main__':
    logger.info("Starting web service with circuit breaker protection")
    app.run(host="0.0.0.0", port=5000, debug=True)
