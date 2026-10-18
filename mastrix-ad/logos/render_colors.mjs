// Render logos/colors.html: one image per palette row plus two halves for quick viewing.
import { chromium } from "playwright-core";
import { createServer } from "node:http";
import { readFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const OUT = path.join(ROOT, "logos/out/colors");
const TYPES = { ".html": "text/html", ".css": "text/css", ".js": "text/javascript", ".woff2": "font/woff2", ".woff": "font/woff" };
const server = createServer(async (req, res) => {
  const file = path.join(ROOT, decodeURIComponent(new URL(req.url, "http://x").pathname));
  let body;
  try { if (!file.startsWith(ROOT)) throw 0; body = await readFile(file); } catch { res.writeHead(404); return res.end(); }
  res.writeHead(200, { "content-type": TYPES[path.extname(file)] || "application/octet-stream" });
  res.end(body);
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
await mkdir(OUT, { recursive: true });
const browser = await chromium.launch({ args: ["--force-color-profile=srgb"] });
const page = await browser.newPage({ viewport: { width: 1640, height: 1200 } });
page.on("pageerror", (e) => console.error("pageerror:", e.message));
await page.goto(`http://127.0.0.1:${server.address().port}/logos/colors.html`);
await page.evaluate(() => window.ready);
for (let i = 1; i <= 6; i++) await page.locator(`#p${i}`).screenshot({ path: path.join(OUT, `palette_${i}.png`) });
await page.screenshot({ path: path.join(OUT, "all.png"), fullPage: true });
console.log(OUT);
await browser.close();
server.close();
