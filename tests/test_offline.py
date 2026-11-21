import asyncio
from playwright.async_api import async_playwright
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import serve, copy_with_config, launch_args, OUT

async def main():
    URL, _ = serve()
    async with async_playwright() as p:
        b = await p.chromium.launch(**launch_args())
        ctx = await b.new_context()
        pg = await ctx.new_page()
        await pg.goto(URL)
        await pg.evaluate("navigator.serviceWorker.ready.then(()=>true)")
        await pg.wait_for_timeout(1500)
        await pg.reload(); await pg.wait_for_timeout(800)
        await ctx.set_offline(True)
        await pg.reload(); await pg.wait_for_timeout(800)
        print('offline title:', await pg.title(), '| qrcode lib:', await pg.evaluate("typeof qrcode"), '| jsQR:', await pg.evaluate("typeof jsQR"))
        print('home text ok:', 'جاهزية الإخلاء' in await pg.inner_text('#pTitle'))
        print('font offline:', await pg.evaluate("document.fonts.ready.then(()=>document.fonts.check('500 16px Tajawal','حماية'))"))
        await b.close()
asyncio.run(main())
