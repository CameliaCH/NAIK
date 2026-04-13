import requests, os, time

DID_API_URL = 'https://api.d-id.com'

# A free professional presenter image hosted by D-ID
# You can replace this with any publicly accessible image URL
PRESENTER_IMAGE = 'https://d-id-public-bucket.s3.amazonaws.com/alice.jpg'

def create_avatar_video(text: str) -> str:
    """
    Send text to D-ID, poll until video is ready, return the video URL.
    """
    api_key = os.getenv('DID_API_KEY')
    headers = {
        'Authorization': f'Basic {api_key}',
        'Content-Type': 'application/json'
    }

    # Step 1: Create the talk
    payload = {
        'source_url': PRESENTER_IMAGE,
        'script': {
            'type': 'text',
            'input': text,
            'provider': {
                'type': 'microsoft',
                'voice_id': 'en-US-JennyNeural'
            }
        }
    }
    res = requests.post(f'{DID_API_URL}/talks', json=payload, headers=headers)
    res.raise_for_status()
    talk_id = res.json()['id']

    # Step 2: Poll until the video is ready (max 30 seconds)
    for _ in range(30):
        time.sleep(1)
        status_res = requests.get(f'{DID_API_URL}/talks/{talk_id}', headers=headers)
        data = status_res.json()
        if data.get('status') == 'done':
            return data['result_url']
        if data.get('status') == 'error':
            raise RuntimeError(f"D-ID error: {data.get('error')}")

    raise RuntimeError('D-ID video timed out after 30 seconds')
