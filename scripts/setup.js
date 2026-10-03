// npm run setup [-- /path/to/ThemeStudio[.app][/Contents/Resources/resources]
//                  | /path/to/official-package.(zip|tar.gz|tgz)]
// Locates the resources dir of the user's own Theme Studio install (or extracts
// it from the official package archive) and saves it to .studio-dir
// (gitignored). pack.js reads env STIA_STUDIO_DIR first, then this file,
// then conventional install paths.
const fs = require("fs");
const path = require("path");
const os = require("os");
const { execFileSync } = require("child_process");

const PROBE = path.join("watchface-template", "template_watch2.proto");
const CONVENTIONAL = [
  "/Applications/ThemeStudio.app/Contents/Resources/resources",
  ...(process.env.HOME ? [path.join(process.env.HOME, "Applications/ThemeStudio.app/Contents/Resources/resources")] : []),
  "C:\\Program Files\\Huawei\\Theme Studio\\resources",
  "C:\\Program Files (x86)\\Huawei\\Theme Studio\\resources",
];
const OFFICIAL_URL = "https://developer.huawei.com/consumer/en/doc/content/themes-design-tools-0000001054531194";

function norm(p) {
  let d = path.resolve(p);
  if (d.endsWith("ThemeStudio.app")) d = path.join(d, "Contents/Resources/resources");
  else if (d.endsWith("resources") === false && fs.existsSync(path.join(d, "Contents/Resources/resources")))
    d = path.join(d, "Contents/Resources/resources");
  return d;
}

// Find a dir holding watchface-template/template_watch2.proto, at root or
// nested a few levels (handles app roots and raw extracted trees).
function findResourcesDir(start) {
  if (fs.existsSync(path.join(start, PROBE))) return start;
  const queue = [[start, 0]];
  while (queue.length) {
    const [dir, depth] = queue.shift();
    if (depth > 4) continue;
    let entries = [];
    try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch { continue; }
    for (const e of entries) {
      if (!e.isDirectory() || e.name === "node_modules" || e.name.startsWith(".")) continue;
      const sub = path.join(dir, e.name);
      if (fs.existsSync(path.join(sub, PROBE))) return sub;
      queue.push([sub, depth + 1]);
    }
  }
  return null;
}

function extractArchive(archive) {
  const cache = path.join(os.homedir(), ".cache", "stia-hwt-packer");
  fs.mkdirSync(cache, { recursive: true });
  const dest = path.join(cache, path.basename(archive).replace(/\.(zip|tar\.gz|tgz)$/, ""));
  if (fs.existsSync(path.join(dest, PROBE)) || findResourcesDir(dest)) {
    console.log("Reusing cached extraction:", dest);
    return findResourcesDir(dest);
  }
  console.log("Extracting", archive, "->", dest);
  fs.mkdirSync(dest, { recursive: true });
  if (/\.zip$/.test(archive)) {
    execFileSync("unzip", ["-q", "-o", archive, "-d", dest], { stdio: "inherit" });
  } else {
    execFileSync("tar", ["-xzf", archive, "-C", dest], { stdio: "inherit" });
  }
  const found = findResourcesDir(dest);
  if (!found) throw new Error("No Theme Studio resources inside " + archive);
  return found;
}

function main() {
  const arg = process.argv.slice(2).find((a) => a !== "--");
  let dir = null;
  if (arg && /\.(zip|tar\.gz|tgz)$/.test(arg)) {
    dir = extractArchive(path.resolve(arg));
  } else {
    const cands = arg ? [norm(arg)] : CONVENTIONAL.map(norm);
    for (const d of cands) {
      const hit = findResourcesDir(d);
      if (hit) { dir = hit; break; }
    }
  }
  if (!dir) {
    console.error("Theme Studio resources not found" + (arg ? ` at ${arg}` : " in conventional locations") + ".");
    console.error("Download the official package (accept Huawei's license) from");
    console.error("  " + OFFICIAL_URL);
    console.error("then run either:");
    console.error("  npm run setup -- /path/to/ThemeStudio.app");
    console.error("  npm run setup -- /path/to/downloaded-package.(zip|tar.gz)");
    process.exit(1);
  }
  fs.writeFileSync(path.join(__dirname, "..", ".studio-dir"), dir + "\n");
  console.log("Studio resources:", dir);
  console.log("Saved to .studio-dir — no export needed.");
}
try { main(); } catch (e) { console.error("setup failed:", e.message); process.exit(1); }
