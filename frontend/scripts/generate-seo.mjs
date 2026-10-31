// Generates public/sitemap.xml and public/robots.txt at build time from the project data.
// SITE_URL (or Vercel's VERCEL_PROJECT_PRODUCTION_URL) supplies the origin; without it the
// sitemap is skipped rather than shipping a made-up domain.
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const projects = JSON.parse(readFileSync(join(root, "src/data/generated/projects.json"), "utf8"));
const raw = process.env.SITE_URL || process.env.VERCEL_PROJECT_PRODUCTION_URL || "";
const origin = raw ? (raw.startsWith("http") ? raw : `https://${raw}`).replace(/\/$/, "") : "";

let robots = "User-agent: *\nAllow: /\n";
if (origin) {
  const paths = ["/", "/about", "/experience", "/projects", "/skills", "/resume", "/contact",
    ...projects.map((p) => `/projects/${p.id}`)];
  const urls = paths.map((p) => `  <url><loc>${origin}${p}</loc></url>`).join("\n");
  writeFileSync(join(root, "public/sitemap.xml"),
    `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`);
  robots += `Sitemap: ${origin}/sitemap.xml\n`;
  console.log(`SEO: wrote sitemap for ${origin}`);
} else {
  console.warn("SEO: SITE_URL not set; sitemap.xml skipped (robots.txt written without a Sitemap line).");
}
writeFileSync(join(root, "public/robots.txt"), robots);
