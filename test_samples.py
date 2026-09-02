import asyncio
import sys
import io
import json
import os

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))
sys.path.insert(0, os.getcwd())
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

samples = [
    'acme_robotics_sample.md',
    'greenenergy_series_a.md',
    'meridian_health_10k.md',
    'quickship_logistics_dd.md',
    'novatech_ai_seed.md',
]

async def test_all():
    from app.main import app
    from app.database import init_db
    await init_db()
    import httpx
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    
    async with httpx.AsyncClient(transport=transport, base_url='http://test') as client:
        for fname in samples:
            print()
            print('=====' , fname, '=====')
            path = 'C:/Users/ahmed/OneDrive/Desktop/My Projects/Vision/ai-dd-copilot/sample_data/' + fname
            try:
                with open(path, 'rb') as f:
                    r = await client.post('/upload', files={'file': (fname, f, 'text/markdown')}, timeout=30)
                doc_id = r.json()['id']
                chunks = r.json().get('chunks', 0)
                print('Upload:', r.status_code, chunks, 'chunks')
                
                r = await client.post('/analyze/' + doc_id, timeout=180)
                print('Analyze:', r.status_code)
                if r.status_code == 200:
                    data = r.json()
                    s = data.get('executive_summary', {})
                    print('  company_name:', s.get('company_name'))
                    print('  strengths:', len(s.get('key_strengths', [])), 'items')
                    print('  risks:', len(s.get('key_risks', [])), 'items')
                    print('  opportunities:', len(s.get('growth_opportunities', [])), 'items')
                    print('  confidence:', s.get('confidence_score'))
                    fm = data.get('financial_metrics', {})
                    filled = sum(1 for k, v in fm.items() if v and k != 'custom')
                    print('  metrics filled:', filled, '/12')
                    print('  risks found:', len(data.get('risks', [])))
                    for risk in data.get('risks', [])[:3]:
                        print('    - [' + risk.get('severity', '') + '] ' + risk.get('title', ''))
                else:
                    err = r.json().get('detail', 'unknown')
                    print('  Error:', err[:200])
            except Exception as e:
                print('  EXCEPTION:', str(e)[:200])

asyncio.run(test_all())
