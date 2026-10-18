// Render the scene frame-by-frame through headless Chromium.
//   node scripts/render.mjs stills A 0,1.2,4.6 [--guides]   -> build/stills/A_<t>.png
//   node scripts/render.mjs video A                          -> out/mastrix_reel_A.mp4
import { chromium } from "playwright-core";
import { spawn } from "node:child_process";
import { createServer } from "node:http";
import { readFile, mkdir } from "node:fs/promises";
import { cpus } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const [mode, variant = "A", timesArg = ""] = process.argv.slice(2);
const guides = process.argv.includes("--guides");
const jpeg = process.argv.includes("--jpeg");
const TYPES = { ".html": "text/html", ".css": "text/css", ".json": "application/json", ".woff2": "font/woff2", ".woff": "font/woff", ".js": "text/javascript" };

const server = createServer(async (req, res) => {
  try {
    const file = path.join(ROOT, decodeURIComponent(new URL(req.url, "http://x").pathname));
    if (!file.startsWith(ROOT)) throw new Error("outside root");
    res.writeHead(200, { "content-type": TYPES[path.extname(file)] || "application/octet-stream" });
    res.end(await readFile(file));
  } catch { res.writeHead(404); res.end(); }
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const base = `http://127.0.0.1:${server.address().port}/scene/index.html?v=${variant}${guides ? "&guides" : ""}`;

const browser = await chromium.launch({ args: ["--force-color-profile=srgb", "--font-render-hinting=none"] });
async function openPage() {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on("pageerror", (e) => console.error("pageerror:", e.message));
  await page.goto(base);
  await page.evaluate(() => window.ready);
  return page;
}
const frameAt = async (page, t) => {
  await page.evaluate((tt) => window.renderAt(tt), t);
  return page.screenshot(jpeg ? { type: "jpeg", quality: 95 } : { type: "png" });
};

if (mode === "stills") {
  await mkdir(path.join(ROOT, "build/stills"), { recursive: true });
  const page = await openPage();
  for (const t of timesArg.split(",").map(Number)) {
    await page.evaluate((tt) => window.renderAt(tt), t);
    const out = path.join(ROOT, `build/stills/${variant}_${t.toFixed(2)}${guides ? "_guides" : ""}.png`);
    await page.screenshot({ path: out });
    console.log(out);
  }
} else if (mode === "video") {
  await mkdir(path.join(ROOT, "out"), { recursive: true });
  const tl = JSON.parse(await readFile(path.join(ROOT, `build/timeline_${variant}.json`), "utf8"));
  const total = Math.round(tl.duration * tl.fps);
  const audio = path.join(ROOT, `build/mix_${variant}_norm.wav`);
  const out = path.join(ROOT, `out/mastrix_reel_${variant}.mp4`);
  const ff = spawn("ffmpeg", [
    "-v", "error", "-y", "-f", "image2pipe", "-framerate", String(tl.fps), "-c:v", jpeg ? "mjpeg" : "png", "-i", "-",
    "-i", audio, "-map", "0:v", "-map", "1:a",
    "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", "-profile:v", "high",
    "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", out,
  ], { stdio: ["pipe", "inherit", "inherit"] });
  const ffDone = new Promise((r, j) => ff.on("close", (c) => (c ? j(new Error(`ffmpeg ${c}`)) : r())));

  const workers = Math.max(1, Math.min(4, cpus().length));
  const pages = await Promise.all(Array.from({ length: workers }, openPage));
  const done = new Map();
  let next = 0, written = 0;
  const flush = async () => {
    while (done.has(written)) {
      const buf = done.get(written); done.delete(written); written++;
      if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once("drain", r));
    }
  };
  const t0 = Date.now();
  await Promise.all(pages.map(async (page) => {
    while (next < total) {
      const f = next++;
      done.set(f, await frameAt(page, f / tl.fps));
      await flush();
      if (f % 150 === 0) console.log(`${variant}: frame ${f}/${total} (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
    }
  }));
  await flush();
  ff.stdin.end();
  await ffDone;
  console.log(out);
}
await browser.close();
server.close();
