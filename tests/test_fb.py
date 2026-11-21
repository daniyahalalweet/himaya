import asyncio, json
from playwright.async_api import async_playwright
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import serve, copy_with_config, launch_args, OUT

store={}
async def main():
    URL, _ = serve(copy_with_config())
    async with async_playwright() as p:
        b = await p.chromium.launch(**launch_args())
        ctx = await b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2)
        errs=[]
        async def fs(route, req):
            if req.method=='POST':
                body=json.loads(req.post_data); did=req.url.split('documentId=')[1].split('&')[0]
                if did in store: return await route.fulfill(status=409, body='{}')
                store[did]=body['fields']; return await route.fulfill(status=200, content_type='application/json', body='{}')
            assert 'Bearer tok123' in (req.headers.get('authorization') or '')
            docs=[{'name':f'projects/x/databases/(default)/documents/events/{k}','fields':v} for k,v in store.items()]
            await route.fulfill(status=200, content_type='application/json', body=json.dumps({'documents':docs}))
        await ctx.route('https://firestore.googleapis.com/**', fs)
        await ctx.route('https://identitytoolkit.googleapis.com/**', lambda r: r.fulfill(status=200, content_type='application/json', body=json.dumps({'idToken':'tok123'})))
        pg = await ctx.new_page()
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.click('text=تحميل بيانات تجريبية')
        await pg.click('[data-v=setup]'); await pg.fill('#s-base','6'); await pg.press('#s-base','Tab')
        await pg.screenshot(path=OUT+'/20_setup_share.png', full_page=True)
        await pg.click('#homeBtn'); await pg.click('.tile >> text=مسؤولة الحصر'); await pg.click('[data-a=startEv]')
        n = await pg.locator('.grid .cls').count()
        for i in range(n):
            await pg.click(f'.grid .cls >> nth={i}'); await pg.click('[data-a=manualAll]')
        await pg.click('[data-a=evac]')
        await ctx.set_offline(True)
        await pg.click('.bar [data-a=endEv]'); await pg.click('[data-a=confirmYes]'); await pg.wait_for_timeout(500)
        print('offline sync label:', await pg.inner_text('[data-sync]'), '| outbox', await pg.evaluate("JSON.parse(localStorage.getItem('himaya-field-v1')).outbox.length"))
        await ctx.set_offline(False); await pg.wait_for_timeout(1500)
        print('online sync label:', await pg.inner_text('[data-sync]'), '| stored docs', len(store))
        doc=list(store.values())[0]; print('fields:', sorted(doc.keys()))
        print('any student names in doc?', any('stringValue' in v and any(w in v['stringValue'] for w in ['نورة','سارة','ريم']) for v in doc.values()))
        await pg.screenshot(path=OUT+'/21_report_sync.png', full_page=True)
        # admin
        await pg.click('#homeBtn'); await pg.click('[data-v=setup]'); await pg.click('[data-v=admin]')
        await pg.fill('#ad-mail','me@example.com'); await pg.fill('#ad-pass','x'); await pg.click('[data-a=adminIn]'); await pg.wait_for_timeout(800)
        await pg.screenshot(path=OUT+'/22_admin.png', full_page=True)
        print('admin lead:', await pg.inner_text('p.lead'))
        print('errors:', errs or 'none')
        await b.close()
asyncio.run(main())
