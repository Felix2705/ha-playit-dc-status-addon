import sys
import requests
import json
from datetime import datetime


def poll(url: str):
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        content_type = r.headers.get('Content-Type','')
        data = None
        if 'application/json' in content_type:
            data = r.json()
        else:
            data = {'text_preview': r.text[:800]}

        out = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'url': url,
            'status_code': r.status_code,
            'data_preview': data,
        }
        print(json.dumps(out))
    except Exception as e:
        print(json.dumps({'timestamp': datetime.utcnow().isoformat() + 'Z', 'error': str(e)}))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: poll.py <url>')
        sys.exit(2)
    poll(sys.argv[1])
