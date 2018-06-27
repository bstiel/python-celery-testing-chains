import unittest
import responses
import app
import tasks

from unittest import TestCase, mock
from freezegun import freeze_time
from celery import chain


class Tests(TestCase):

    def setUp(self):
        app.app.config['TESTING'] = True
        self.client = app.app.test_client()
    
    @responses.activate
    def test_chain(self):
        responses.add(responses.GET, 'https://api.coindesk.com/v1/bpi/historical/close.json?start=2018-05-01&end=2018-05-08', body='{"bpi":{"2018-05-01":9067.715,"2018-05-02":9219.8638,"2018-05-03":9734.675,"2018-05-04":9692.7175,"2018-05-05":9826.5975,"2018-05-06":9619.1438,"2018-05-07":9362.5338,"2018-05-08":9180.1588},"disclaimer":"This data was produced from the CoinDesk Bitcoin Price Index. BPI value data returned as USD.","time":{"updated":"May 9, 2018 00:03:00 UTC","updatedISO":"2018-05-09T00:03:00+00:00"}}', status=200)
        task = chain(
            tasks.fetch_bitcoin_price_index.s(start_date='2018-05-01', end_date='2018-05-08'),
            tasks.calculate_moving_average.s(window=2)).apply()
        self.assertEqual(task.status, 'SUCCESS')
        self.assertEqual(task.result, [
            {'date': '2018-05-01', 'ma': '', 'value': 9067.715},
            {'date': '2018-05-02', 'ma': 9143.7894, 'value': 9219.8638},
            {'date': '2018-05-03', 'ma': 9477.2694, 'value': 9734.675},
            {'date': '2018-05-04', 'ma': 9713.69625, 'value': 9692.7175},
            {'date': '2018-05-05', 'ma': 9759.657500000001, 'value': 9826.5975},
            {'date': '2018-05-06', 'ma': 9722.87065, 'value': 9619.1438},
            {'date': '2018-05-07', 'ma': 9490.8388, 'value': 9362.5338},
            {'date': '2018-05-08', 'ma': 9271.346300000001, 'value': 9180.1588}
        ])

    @mock.patch('app.chain')
    @mock.patch('app.fetch_bitcoin_price_index')
    @mock.patch('app.calculate_moving_average')
    def test_mocked_chain(self, mock_calculate_moving_average, mock_fetch_bitcoin_price_index, mock_chain):
        response = self.client.post('/', json={'start_date': '2018-05-01', 'end_date': '2018-05-08', 'window': 3})
        self.assertEqual(response.status_code, 201)
        mock_chain.assert_called_once_with(
            mock_fetch_bitcoin_price_index.s(start_date='2018-05-01', end_date='2018-05-08'),
            mock_calculate_moving_average.s(window=3))
