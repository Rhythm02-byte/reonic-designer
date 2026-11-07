"""Check the isolated pitch, without running evaluation or touching application code.

Requires the already-installed playwright package and Chromium headless shell.
Writes only QA screenshots and qa-report.json beside this script.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CHROMIUM = Path.home() / "AppData/Local/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-win64/chrome-headless-shell.exe"


def main() -> None:
    html = (HERE / "index.html").read_text(encoding="utf-8")
    evidence = json.loads((HERE / "evidence-pinned.json").read_text(encoding="utf-8"))
    assert evidence["chosen"] == {"model": "M1", "pvGate": 0.6}, "Review changed selection"
    assert evidence["nTestProjects"] == 325
    assert evidence["nValidation"] == 232
    for model in ["B0", "B0c", "B1", "M1", "H1"]:
        for key, digits in [("ems", 1), ("wholeDesign", 1), ("pv", 1), ("battery", 1)]:
            v = evidence["test"][model][key]
            expected = f"{v if key == 'ems' else 100*v:.{digits}f}"
            assert expected in html, (model, key, expected)
    assert sum(map(int, re.findall(r'data-seconds="(\d+)"', html))) == 300
    current = ROOT / "eval/results/latest.json"
    current_matches = current.is_file() and hashlib.sha256(current.read_bytes()).hexdigest() == evidence["sourceSha256"]
    screenshots = HERE / "qa"
    screenshots.mkdir(exist_ok=True)
    errors: list[str] = []
    network: list[str] = []
    layout: list[dict] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=str(CHROMIUM))
        page = browser.new_page(viewport={"width": 1440, "height": 920}, device_scale_factor=1)
        page.on("pageerror", lambda e: errors.append(str(e)))

        def route_request(route):
            url = route.request.url
            if url.startswith(("file:", "data:", "blob:")):
                route.continue_()
            else:
                network.append(url)
                route.abort()

        page.route("**/*", route_request)
        page.goto((HERE / "index.html").as_uri())
        assert page.locator(".slide").count() == 11
        for i in range(11):
            page.evaluate("n => {location.hash = String(n)}", i + 1)
            page.wait_for_function("n => document.querySelectorAll('.slide')[n-1].classList.contains('active')", arg=i+1)
            check = page.locator(".slide.active").evaluate("""s => {
                const content=s.querySelector('.content');
                const bad=[...s.querySelectorAll('.content, h1, h2, h3, p, .footer, td, th')]
                  .filter(e => e.getClientRects().length && !e.closest('.notes'))
                  .filter(e=>e.scrollWidth>e.clientWidth+2 || e.scrollHeight>e.clientHeight+2)
                  .map(e=>({tag:e.tagName,cls:e.className,text:e.textContent.slice(0,100),w:e.scrollWidth-e.clientWidth,h:e.scrollHeight-e.clientHeight}));
                return {title:s.dataset.title,overflow:bad,activeCount:document.querySelectorAll('.slide.active').length,
                        contentHeight:content.clientHeight,contentScroll:content.scrollHeight};
            }""")
            assert check["activeCount"] == 1
            layout.append(check)
            page.screenshot(path=str(screenshots / f"slide-{i+1:02}.png"))
        page.keyboard.press("Home")
        assert page.locator("#counter").inner_text() == "1 / 11"
        page.keyboard.press("ArrowRight")
        assert page.locator("#counter").inner_text() == "2 / 11"
        page.keyboard.press("n")
        assert page.locator("#notes-panel").is_visible()
        page.keyboard.press("Escape")
        assert not page.locator("#notes-panel").is_visible()
        page.keyboard.press("o")
        assert page.locator("body").get_attribute("class") == "overview"
        page.keyboard.press("o")
        assert page.locator("#counter").inner_text() == "2 / 11"
        page.emulate_media(media="print")
        assert page.locator(".slide:visible").count() == 11
        assert not page.locator(".nav").is_visible()
        page.emulate_media(media="screen", reduced_motion="reduce")
        page.set_viewport_size({"width": 390, "height": 844})
        page.keyboard.press("Home")
        assert page.locator("#next").is_visible()
        for selector in ["#next", "#notes-toggle", "#fullscreen"]:
            box=page.locator(selector).bounding_box()
            assert box and box["height"] >= 44
        page.screenshot(path=str(screenshots / "mobile-controls.png"))
        browser.close()
    report = {"kind":"presentation QA, not engine evaluation", "sourceSnapshotCurrent":bool(current_matches),
              "sourceSha256":evidence["sourceSha256"],"slides":len(layout), "mainPitchSeconds":300,
              "pageErrors":errors,"unexpectedNetworkRequests":network,"layout":layout,
              "navigationNotesOverviewPrintAndMobileControls":"checked",
              "limitations":["System font fallback; Geist not bundled", "No live application or model test run", "Visual QA is not full accessibility certification"]}
    (HERE / "qa-report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    assert not errors, errors
    assert not network, network
    assert not any(x["overflow"] for x in layout), "Inspect overflow in qa-report.json"


if __name__ == "__main__":
    main()
