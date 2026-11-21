import asyncio, json
from playwright.async_api import async_playwright
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import serve, copy_with_config, launch_args, OUT

async def main():
    URL, _ = serve()
    async with async_playwright() as p:
        b = await p.chromium.launch(**launch_args())
        errs=[]
        def ctx_page(ctx, tag):
            async def mk():
                pg = await ctx.new_page()
                pg.on('console', lambda m: errs.append(f'{tag} console {m.type}: {m.text}') if m.type in ('error','warning') else None)
                pg.on('pageerror', lambda e: errs.append(f'{tag} pageerror: {e}'))
                return pg
            return mk()
        off_ctx = await b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2)
        off = await ctx_page(off_ctx,'OFF'); await off.goto(URL)
        await off.screenshot(path=OUT+'/01_home_empty.png', full_page=True)
        await off.click('text=تحميل بيانات تجريبية'); await off.wait_for_timeout(200)
        # package text
        await off.click('[data-v=setup]'); await off.click('[data-a=copyPkg]')
        pkg = await off.input_value('#cp'); await off.click('.sheet [data-a=close]')
        print('pkg len', len(pkg))
        await off.screenshot(path=OUT+'/02_setup.png', full_page=True)
        # QR pages
        await off.click('[data-a=showPkg]'); await off.wait_for_timeout(200)
        await off.click('[data-a=pkgQR][data-id=""]'); await off.wait_for_timeout(300)
        await off.screenshot(path=OUT+'/03_pkg_qr.png')
        pages=[]; i=0
        while True:
            await off.locator('.qr').screenshot(path=OUT+f'/pkg{i}.png'); pages.append(OUT+f'/pkg{i}.png'); i+=1
            nxt=off.locator('[data-a=qrNext]')
            if await nxt.count()==0 or await nxt.is_disabled(): break
            await nxt.click(); await off.wait_for_timeout(150)
        print('pkg qr pages', len(pages))
        await off.click('.sheet [data-a=close]')
        # start event
        await off.click('#homeBtn'); await off.click('.tile >> text=مسؤولة الحصر')
        await off.screenshot(path=OUT+'/04_officer_new.png', full_page=True)
        await off.click('[data-a=startEv]'); await off.wait_for_timeout(300)
        # teacher device
        t_ctx = await b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2)
        t = await ctx_page(t_ctx,'TCH'); await t.goto(URL)
        await t.click('.tile >> text=المعلمة')
        await t.click('[data-a=scan][data-for=cls]'); await t.wait_for_timeout(300)
        for pg in pages:
            await t.set_input_files('#fImg', pg); await t.wait_for_timeout(1200)
            print('t scan', await t.locator('#scanMsg').inner_text() if await t.locator('#scanMsg').count() else 'sheet closed')
        await t.wait_for_timeout(300)
        print('teacher classes', await t.evaluate("JSON.parse(localStorage.getItem('himaya-field-v1')).classes.length"))
        await t.fill('#t-name','أ. سارة'); await t.press('#t-name','Tab')
        await t.screenshot(path=OUT+'/05_teacher_pick.png', full_page=True)
        # class 1
        await t.click('.grid .cls >> nth=0'); await t.wait_for_timeout(150)
        await t.screenshot(path=OUT+'/06_loc.png')
        await t.click('[data-a=setLoc][data-k=room]')
        await t.click('[data-a=pick][data-n="3"]'); await t.click('[data-a=setSt][data-k=m]')
        await t.screenshot(path=OUT+'/07_last.png')
        await t.click('[data-a=setLast][data-k=w]')
        await t.click('[data-a=pick][data-n="5"]'); await t.click('[data-a=setSt][data-k=a]')
        await t.click('[data-a=pick][data-n="7"]'); await t.click('[data-a=setSt][data-k=o]')
        await t.screenshot(path=OUT+'/08_list.png', full_page=True)
        await t.click('[data-a=tFinish]'); await t.wait_for_timeout(200)
        await t.click('[data-a=rate][data-v="5"]')
        await t.screenshot(path=OUT+'/09_done.png', full_page=True)
        await t.locator('.qr').screenshot(path=OUT+'/qr1.png')
        n7 = await t.evaluate("JSON.parse(localStorage.getItem('himaya-field-v1')).classes[0].st[6].name")
        # class 2 with extra = student 7 of class 1
        await t.click('[data-a=tNew]'); await t.click('.grid .cls >> nth=1'); await t.click('[data-a=setLoc][data-k=yard]')
        await t.click('[data-a=extraDlg]'); await t.click('[data-a=extraCls] >> nth=0')
        await t.fill('#exQ', n7.split()[0]); await t.wait_for_timeout(100)
        await t.click(f'[data-a=extraAdd][data-n="7"]')
        await t.click('[data-a=tFinish]'); await t.wait_for_timeout(200)
        await t.locator('.qr').screenshot(path=OUT+'/qr2.png')
        # officer scans both via image
        for q in ('qr1.png','qr2.png'):
            await off.click('.bar [data-a=scan]'); await off.wait_for_timeout(300)
            await off.set_input_files('#fImg', OUT+'/'+q); await off.wait_for_timeout(1500)
            print('scanMsg', await off.inner_text('#scanMsg'))
            await off.click('.sheet [data-a=close]')
        await off.screenshot(path=OUT+'/10_officer_live.png', full_page=True)
        # manual for class 3, and all for the rest
        cnt = await off.locator('.grid .cls').count()
        await off.click('.grid .cls >> nth=2'); await off.click('[data-a=manualList]')
        await off.click('[data-a=pick][data-n="1"]'); await off.click('[data-a=setSt][data-k=i]')
        await off.click('[data-a=oSave]'); await off.wait_for_timeout(100)
        for i in range(3, cnt):
            await off.click(f'.grid .cls >> nth={i}'); await off.click('[data-a=manualAll]')
        await off.click('[data-a=evac]')
        await off.screenshot(path=OUT+'/11_officer_full.png', full_page=True)
        await off.click('.bar [data-a=endEv]'); await off.click('[data-a=confirmYes]'); await off.wait_for_timeout(300)
        await off.screenshot(path=OUT+'/12_report.png', full_page=True)
        print('impact:\n', await off.input_value('#tx-impact'))
        print('chalet:\n', await off.input_value('#tx-chalet'))
        await off.set_viewport_size({'width':1100,'height':900}); await off.click('[data-v=history]')
        await off.screenshot(path=OUT+'/13_history_wide.png', full_page=True)
        print('\n'.join(errs) or 'no console errors')
        await b.close()
asyncio.run(main())
