import requests
from config import TAVILY_API_KEY

def search_web(query: str, max_results: int = 5):
    if not TAVILY_API_KEY:
        return {'enabled': False, 'results': [], 'message': 'TAVILY_API_KEY is not configured.'}
    r = requests.post('https://api.tavily.com/search', json={
        'api_key': TAVILY_API_KEY, 'query': query, 'search_depth': 'basic',
        'max_results': max_results, 'include_answer': True
    }, timeout=20)
    r.raise_for_status()
    data=r.json()
    return {'enabled': True, 'answer': data.get('answer'), 'results': [
        {'title':x.get('title'),'url':x.get('url'),'content':x.get('content','')[:1200]}
        for x in data.get('results',[])
    ]}
