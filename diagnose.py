#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
診斷腳本：登入後截圖並列出頁面所有按鈕/連結/選單文字
執行: python diagnose.py
"""
import asyncio
from playwright.async_api import async_playwright

USERNAME = "001343"
PASSWORD = "2xguoglu"
BASE_URL  = "https://parking.shl-external.com/"

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        page = await browser.new_page(viewport={"width": 1366, "height": 768})

        print("前往首頁...")
        await page.goto(BASE_URL)
        await page.wait_for_load_state("domcontentloaded")

        # 點選員工登入 Tab
        await page.click("text=員工登入")
        await asyncio.sleep(0.5)

        # 填入帳密
        await page.fill("input[name='username']", USERNAME)
        await page.fill("input[name='password']", PASSWORD)
        await page.click("button:has-text('員工登入')")
        await page.wait_for_load_state("networkidle", timeout=15000)

        print("\n✅ 登入完成，等待 2 秒讓頁面穩定...")
        await asyncio.sleep(2)

        # ── 截圖 ──
        screenshot_path = "after_login.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"📸 截圖已存：{screenshot_path}")

        # ── 列出所有 button 文字 ──
        print("\n── 頁面上所有 <button> 文字 ──")
        buttons = await page.locator("button").all()
        for i, btn in enumerate(buttons):
            try:
                txt = (await btn.inner_text()).strip()
                print(f"  [{i}] {txt!r}")
            except Exception:
                pass

        # ── 列出所有 <a> 連結文字 ──
        print("\n── 頁面上所有 <a> 連結文字 ──")
        links = await page.locator("a").all()
        for i, link in enumerate(links):
            try:
                txt = (await link.inner_text()).strip()
                href = await link.get_attribute("href") or ""
                print(f"  [{i}] {txt!r}  href={href!r}")
            except Exception:
                pass

        # ── 列出所有 <div>/<li> 含文字（可能是選單項目）──
        print("\n── .link_buttons 內所有子元素文字（選單區）──")
        menu_items = await page.locator(".link_buttons *").all()
        for i, el in enumerate(menu_items):
            try:
                txt = (await el.inner_text()).strip()
                if txt:
                    tag = await el.evaluate("el => el.tagName")
                    print(f"  [{i}] <{tag.lower()}> {txt!r}")
            except Exception:
                pass

        # ── 進入員工專區 → 車位申請作業 → 臨時車位申請 ──
        print("\n── 導覽至臨時車位申請表單 ──")
        await page.click("button:has-text('員工專區')")
        await page.wait_for_load_state("networkidle", timeout=10000)
        await asyncio.sleep(0.5)

        print("\n── 員工專區展開後可見元素──")
        await asyncio.sleep(2)  # 額外等待確保菜單完全渲染
        
        items = await page.locator("button, a, div, span").all()
        for i, el in enumerate(items):
            try:
                txt = (await el.inner_text()).strip()
                if txt:
                    visible = await el.is_visible()
                    print(f"  [{i}] {txt!r} visible={visible}")
            except Exception:
                pass

        # 更精確診斷「車位申請作業」與「臨時車位申請」
        for keyword in ['車位申請作業', '臨時車位申請']:
            for selector_pattern in [f"text={keyword}", f"button:has-text('{keyword}')"]:
                locator = page.locator(selector_pattern)
                count = await locator.count()
                print(f"\n── {selector_pattern} count={count} ──")
                for j in range(count):
                    el = locator.nth(j)
                    try:
                        tag = await el.evaluate('el => el.tagName')
                        visible = await el.is_visible()
                        outer = await el.evaluate('el => el.outerHTML')
                        print(f"  [{j}] <{tag}> visible={visible} outerHTML={outer[:300]!r}")
                    except Exception as e:
                        print(f"  [{j}] error: {e}")

        await page.click("text=車位申請作業")
        await asyncio.sleep(0.6)
        await page.click("text=臨時車位申請")
        await page.wait_for_load_state("networkidle", timeout=10000)
        await asyncio.sleep(1)

        # ── 點擊「選擇時段」開啟 Modal ──
        print("\n── 點擊「選擇時段」，列出 Modal 內容 ──")
        await page.click("button:has-text('選擇時段')")
        await asyncio.sleep(1)

        screenshot_path2 = "after_modal.png"
        await page.screenshot(path=screenshot_path2, full_page=True)
        print(f"📸 Modal 截圖已存：{screenshot_path2}")

        # Modal 內所有 select
        print("\n── Modal 內所有 <select> 元素 ──")
        selects = await page.locator("select").all()
        for i, el in enumerate(selects):
            try:
                info = await el.evaluate("""e => ({
                    name: e.name, id: e.id, f: e.getAttribute('f'),
                    visible: e.offsetParent !== null,
                    options: Array.from(e.options).map(o => ({value: o.value, text: o.text}))
                })""")
                print(f"  [{i}] {info}")
            except Exception as ex:
                print(f"  [{i}] error: {ex}")

        # Modal 內所有 button
        print("\n── Modal 內所有 <button> 文字 ──")
        buttons = await page.locator("button").all()
        for i, btn in enumerate(buttons):
            try:
                txt = (await btn.inner_text()).strip()
                visible = await btn.is_visible()
                print(f"  [{i}] {txt!r}  visible={visible}")
            except Exception:
                pass

        # Modal 內所有 input
        print("\n── Modal 內所有 <input> 元素 ──")
        inputs = await page.locator("input").all()
        for i, el in enumerate(inputs):
            try:
                attrs = await el.evaluate("""e => ({
                    type: e.type, name: e.name, id: e.id,
                    placeholder: e.placeholder, value: e.value,
                    visible: e.offsetParent !== null
                })""")
                print(f"  [{i}] {attrs}")
            except Exception as ex:
                print(f"  [{i}] error: {ex}")

        # Modal 可見文字
        print("\n── Modal 可見文字 ──")
        modal_text = await page.inner_text("#schedule_modal")
        print(modal_text[:2000])

        input("\n按 Enter 關閉瀏覽器...")
        await browser.close()

asyncio.run(main())
