import asyncio, time
from playwright.async_api import async_playwright
OUT='/tmp/claude-0/-home-claude/03ec61e5-df55-51b4-9bc8-0d29cb23cb3d/scratchpad/reel/'
frames=[]  # (file, hold_seconds, caption)
async def snap(pg,name,hold,cap):
    await pg.screenshot(path=OUT+f'fr_{name}.png'); frames.append((f'fr_{name}.png',hold,cap))
async def burst(pg,name,n,dt,hold,cap):
    for i in range(n):
        await pg.screenshot(path=OUT+f'fr_{name}{i:02d}.png'); frames.append((f'fr_{name}{i:02d}.png',dt if i<n-1 else hold,cap)); await pg.wait_for_timeout(int(dt*1000))
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=3,is_mobile=True,has_touch=True,locale='ja-JP')
        await ctx.add_init_script("localStorage.setItem('crate.welcomed','1')")
        pg=await ctx.new_page()
        await pg.goto('http://localhost:8765/index.html'); await pg.wait_for_timeout(1500)
        await pg.evaluate("[...document.querySelectorAll('[data-view=\"scores\"]')].find(e=>e.offsetParent).click()"); await pg.wait_for_timeout(800)
        await snap(pg,'a_scores',1.2,'楽譜タブで「サンプル楽譜で試す」')
        await pg.locator('[data-act="scoreSample"]').first.click(); await pg.wait_for_timeout(8000)
        if await pg.locator('[data-act="tipsClose"]').count(): await pg.locator('[data-act="tipsClose"]').first.click(); await pg.wait_for_timeout(500)
        await snap(pg,'b_score',1.8,'読み込んだ楽譜（イ長調）')
        await pg.locator('button:has-text("移調")').first.click(); await pg.wait_for_timeout(900)
        await snap(pg,'c_tp',1.2,'「移調」を押して')
        sharp=pg.locator('[data-act="tpStep"][data-d="1"]').first
        await sharp.click(); await burst(pg,'d_s1',4,0.25,1.0,'♯を押すと…')
        await sharp.click(); await burst(pg,'e_s2',4,0.25,1.6,'音符も調号も、新しいキーで書き直し')
        await pg.locator('[data-act="tpDone"]').first.click(); await pg.wait_for_timeout(1500)
        await snap(pg,'f_done',1.8,'ロ長調に移調できました')
        if await pg.locator('[data-act="svExport"]').count():
            await pg.evaluate("document.querySelector('[data-act=\"svExport\"]').click()"); await pg.wait_for_timeout(3000)
            await snap(pg,'g_pdf',2.0,'PDFで保存して、LINEで送れる')
        await b.close()
    import json; json.dump(frames,open(OUT+'frames.json','w'),ensure_ascii=False)
    print(len(frames),'frames')
asyncio.run(main())
