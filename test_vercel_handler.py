import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.index import handler


def test_vercel_handler_returns_safe_body_contract():
    response = handler(
        {
            'httpMethod': 'GET',
            'path': '/',
            'headers': {'host': 'localhost:3000'},
            'queryStringParameters': {},
            'body': '',
        },
        None,
    )

    assert response['statusCode'] in {200, 404, 500}
    assert isinstance(response.get('body'), str)
    assert 'isBase64Encoded' in response
    assert isinstance(response['isBase64Encoded'], bool)
