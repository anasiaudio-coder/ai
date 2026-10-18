// Render the logo gallery: one sheet per direction, an overview of all 20, and an SVG per mark.
//   node logos/render.mjs
import { chromium } from "playwright-core";
import { createServer } from "node:http";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const OUT = path.join(ROOT, "logos/out");
const TYPES = { ".html": "text/html", ".css": "text/css", ".js": "text/javascript", ".woff2": "font/woff2", ".woff": "font/woff" };

const server = createServer(async (req, res) => {
  try {
    const file = path.join(ROOT, decodeURIComponent(new URL(req.url, "http://x").pathname));
    if (!file.startsWith(ROOT)) throw new Error("outside root");
    res.writeHead(200, { "content-type": TYPES[path.extname(file)] || "application/octet-stream" });
    res.end(await readFile(file));
  } catch { res.writeHead(404); res.end(); }
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const base = `http://127.0.0.1:${server.address().port}/logos/index.html`;

await mkdir(path.join(OUT, "svg"), { recursive: true });
const browser = await chromium.launch({ args: ["--force-color-profile=srgb"] });
const open = async (view, width) => {
  const page = await browser.newPage({ viewport: { width, height: 1200 }, deviceScaleFactor: 1 });
  page.on("pageerror", (e) => console.error("pageerror:", e.message));
  await page.goto(`${base}?view=${view}`);
  await page.evaluate(() => window.ready);
  return page;
};

const sections = await open("sections", 1196);
for (let i = 1; i <= 5; i++) {
  const file = path.join(OUT, `sheet_${i}.png`);
  await sections.locator(`#t${i}`).screenshot({ path: file });
  console.log(file);
}
const svgs = await sections.evaluate(() => MARKS.map((m) => {
  const vb = m.wide ? IJAM.viewBox : "0 0 200 200";
  const [x, y, w, h] = vb.split(" ");
  return { n: m.n, svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${vb}"><rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${PALETTES.dark.bg}"/>${m.svg(PALETTES.dark)}</svg>` };
}));
for (const { n, svg } of svgs) await writeFile(path.join(OUT, "svg", `${String(n).padStart(2, "0")}.svg`), svg);

const overview = await open("overview", 1760);
const file = path.join(OUT, "overview.png");
await overview.screenshot({ path: file, fullPage: true });
console.log(file);

await browser.close();
server.close();
