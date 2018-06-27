import os
from flask import Flask, Response, request, jsonify
from tasks import fetch_bitcoin_price_index, calculate_moving_average
from celery import chain


PATH = './data'
app = Flask(__name__)
app.config['DEBUG'] = True


@app.route('/', methods=['POST'])
def index():
    if request.method == 'POST':
        start_date = request.json['start_date']
        end_date = request.json['end_date']
        window = request.json['window']
        chain(
            fetch_bitcoin_price_index.s(start_date=start_date, end_date=end_date),
            calculate_moving_average.s(window=window)
        ).delay()
        return '', 201


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)