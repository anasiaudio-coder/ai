// Render film/overlay.html to a transparent PNG sequence at the film's frame rate.
//   node film/render_overlay.mjs            -> build/film/overlay/0000.png ...
//   node film/render_overlay.mjs stills 0,4.5,26.5   -> build/film/overlay_stills/<t>.png
import { chromium } from "playwright-core";
import { createServer } from "node:http";
import { readFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const plan = JSON.parse(await readFile(path.join(ROOT, "film/plan.json"), "utf8"));
const [mode = "frames", times = ""] = process.argv.slice(2);
const TYPES = { ".html": "text/html", ".css": "text/css", ".js": "text/javascript", ".json": "application/json", ".woff2": "font/woff2", ".woff": "font/woff" };
const server = createServer(async (req, res) => {
  const file = path.join(ROOT, decodeURIComponent(new URL(req.url, "http://x").pathname));
  let body;
  try { if (!file.startsWith(ROOT)) throw 0; body = await readFile(file); } catch { res.writeHead(404); return res.end(); }
  res.writeHead(200, { "content-type": TYPES[path.extname(file)] || "application/octet-stream" });
  res.end(body);
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const url = `http://127.0.0.1:${server.address().port}/film/overlay.html`;
const browser = await chromium.launch();
const open = async () => {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on("pageerror", (e) => console.error("pageerror:", e.message));
  await page.goto(url);
  await page.evaluate(() => window.ready);
  return page;
};

if (mode === "stills") {
  const dir = path.join(ROOT, "build/film/overlay_stills");
  await mkdir(dir, { recursive: true });
  const page = await open();
  for (const t of times.split(",").map(Number)) {
    await page.evaluate((tt) => window.renderAt(tt), t);
    await page.screenshot({ path: path.join(dir, `${t.toFixed(2)}.png`), omitBackground: true });
  }
} else {
  const dir = path.join(ROOT, "build/film/overlay");
  await mkdir(dir, { recursive: true });
  const total = Math.round(plan.duration * plan.fps);
  const pages = await Promise.all([0, 1, 2, 3].map(open));
  let next = 0;
  await Promise.all(pages.map(async (page) => {
    while (next < total) {
      const f = next++;
      await page.evaluate((tt) => window.renderAt(tt), f / plan.fps);
      await page.screenshot({ path: path.join(dir, `${String(f).padStart(4, "0")}.png`), omitBackground: true });
    }
  }));
  console.log(dir, total, "frames");
}
await browser.close();
server.close();
