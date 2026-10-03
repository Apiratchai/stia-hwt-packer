// pack.js — build a Stia .hwt face with the bundled ClaudeFit sample.
// Needs schema files from the user's own Theme Studio install (see
// resolveStudioFile below). This repo ships NO Huawei files.
// Packs with protobufjs + RLE image blob + 16-byte framing + zip.
// Run: node pack.js
// Verifies: proto round-trip, image-stream re-decode + pixel compare, zip layout.
const fs = require("fs");
const path = require("path");
const protobuf = require("protobufjs");
const { Jimp } = require("jimp");
const AdmZip = require("adm-zip");

const ROOT = __dirname;
const RES = path.join(ROOT, "res");

// Schema files come from the user's own licensed Theme Studio install —
// never vendored here. Set STIA_STUDIO_DIR to the Studio resources dir, e.g.
// macOS: .../ThemeStudio.app/Contents/Resources/resources
function studioTemplateDir() {
  let fileDir = null;
  try { fileDir = fs.readFileSync(path.join(ROOT, ".studio-dir"), "utf8").trim(); } catch {}
  const cands = [
    process.env.STIA_STUDIO_DIR,
    fileDir,
    "/Applications/ThemeStudio.app/Contents/Resources/resources",
    path.join(process.env.HOME || "", "Applications/ThemeStudio.app/Contents/Resources/resources"),
  ].filter(Boolean);
  for (const d of cands) {
    if (d && fs.existsSync(path.join(d, "watchface-template", "template_watch2.proto"))) return d;
  }
  return null;
}
function resolveStudioFile(rel) {
  const dir = studioTemplateDir();
  if (!dir) {
    throw new Error(
      "Schema files not found. Install Huawei Theme Studio (Windows/macOS) from " +
      "https://developer.huawei.com/consumer/en/doc/content/themes-design-tools-0000001054531194 " +
      "and set STIA_STUDIO_DIR to its resources dir, e.g. STIA_STUDIO_DIR=/Applications/ThemeStudio.app/Contents/Resources/resources"
    );
  }
  return path.join(dir, rel);
}
const PROTO = resolveStudioFile("watchface-template/template_watch2.proto");
const SPEC_PATH = resolveStudioFile("watchface-template/smart-watch-spec-1.0.json");
const H = (f) => path.join(RES, f);

const SIG = [85, 85, 85, 85], VER = [1, 0, 0, 1], IMG_HDR = [69, 35, 136, 136];
const MAGIC = [137, 103, 69, 35];
const le16 = (v) => [v & 255, (v >> 8) & 255];
const le32 = (v) => [v & 255, (v >> 8) & 255, (v >> 16) & 255, (v >> 24) & 255];

function rleBGRA(w, h, rgba) {
  // replicate Theme Studio bitMapRLE (PNG path); assert: no magic-valued pixel
  const px = [];
  for (let i = 0; i < rgba.length; i += 4) {
    const b = [rgba[i + 2], rgba[i + 1], rgba[i], rgba[i + 3]];
    if (b[0] === 137 && b[1] === 103 && b[2] === 69 && b[3] === 35)
      throw new Error("magic-valued pixel present, abort");
    px.push(b);
  }
  const out = [...IMG_HDR, ...le16(w), ...le16(h)];
  let runColor = px[0], runLen = 1;
  const flush = () => {
    if (runLen > 3) out.push(...MAGIC, ...runColor, ...le32(runLen));
    else for (let k = 0; k < runLen; k++) out.push(...runColor);
  };
  for (let i = 1; i < px.length; i++) {
    const same = px[i].every((v, j) => v === runColor[j]);
    if (same) runLen++;
    else { flush(); runColor = px[i]; runLen = 1; }
  }
  flush();
  return out;
}

(async () => {
  const face = JSON.parse(fs.readFileSync(path.join(ROOT, "face.json"), "utf8"));
  const root = await protobuf.load(PROTO);
  const T = root.lookupType("TemplateWatch2");

  // Firmware image table is one-based (002 rendered the first time glyph).
  // Source asset
  // filenames are editable labels, not offsets into the binary image table.
  const seen = [];
  for (const el of face.elements) for (const l of [...el.layers, ...(el.containers || []).flatMap(c => c.layers)]) {
    const names = l.singleRes ? [l.singleRes.resName] : l.selectedRes ? l.selectedRes.res : l.combinedRes ? l.combinedRes.res : [];
    for (const n of names) if (!seen.includes(n)) seen.push(n);
  }
  const resourceIds = new Map(seen.map((name, i) => [name, String(i + 1).padStart(3, "0")]));
  const short = (name) => {
    if (!resourceIds.has(name)) throw new Error("unpacked resource " + name);
    return resourceIds.get(name);
  };
  const encodeLayer = (l) => {
      const base = { index: l.index, drawType: l.drawType };
      if (l.singleRes) base.singleRes = { resName: short(l.singleRes.resName), resPosition: { x: l.singleRes.pos[0], y: l.singleRes.pos[1] } };
      if (l.selectedRes) base.selectedRes = { resName: l.selectedRes.res.map(short), resPosition: { x: l.selectedRes.pos[0], y: l.selectedRes.pos[1] }, valueType: l.selectedRes.value };
      if (l.combinedRes) base.combinedRes = { resName: l.combinedRes.res, resDefault: [l.combinedRes.res[0], l.combinedRes.res[0]], resPosition: { x: l.combinedRes.pos[0], y: l.combinedRes.pos[1] }, alignType: 0, valueType: l.combinedRes.value, resSign: "" };
      if (l.text) base.text = { textRect: { x: l.text.rect[0], y: l.text.rect[1], width: l.text.rect[2], height: l.text.rect[3] }, textColor: { red: l.text.color[0], green: l.text.color[1], blue: l.text.color[2], alpha: l.text.color[3] }, fontType: l.text.font, alignType: l.text.align, valueType: l.text.value };
      return base;
  };
  const elements = face.elements.map((el) => ({
    label: el.label,
    isSupportOption: false,
    layers: el.layers.map(encodeLayer),
    containers: (el.containers || []).map((c) => ({
      index: c.index, isSupportOption: false, dataType: c.dataType,
      rect: { x: c.rect[0], y: c.rect[1], width: c.rect[2], height: c.rect[3] },
      layers: c.layers.map(encodeLayer),
    })),
  }));
  if (elements.some(e => e.label === 3 && e.layers.length))
    throw new Error("Stia widget values must be in containers");
  if (!elements.find(e => e.label === 1).layers.some(l => l.selectedRes?.valueType === 64))
    throw new Error("missing time-driven mascot frames");
  const msg = { titleEn: face.titleEn, titleCn: face.titleCn, elements };
  const err = T.verify(msg);
  if (err) throw new Error("proto verify: " + err);
  const protoBytes = T.encode(T.create(msg)).finish();
  // round-trip check
  const back = T.decode(protoBytes);
  if (back.elements.length !== msg.elements.length) throw new Error("proto round-trip mismatch");

  // Reject unsupported tap targets (jump-app ids or widget values from the
  // Stia profile) and verify every hit region survives encoding.
  const spec = JSON.parse(fs.readFileSync(SPEC_PATH, "utf8"));
  const allowed = new Set([
    ...(spec.constraint.jumpapp || []),
    ...(spec.constraint.dataTypes || []).flatMap((t) => t.valueTypes || []),
  ]);
  const expectedButtons = elements.flatMap(e => e.containers);
  const decodedButtons = back.elements.flatMap(e => e.containers);
  if (decodedButtons.length !== expectedButtons.length) throw new Error("button count mismatch");
  expectedButtons.forEach((button, i) => {
    const rect = button.rect;
    if (!allowed.has(button.dataType) ||
        rect.x + rect.width > 280 || rect.y + rect.height > 456 ||
        rect.width < 44 || rect.height < 44)
      throw new Error("invalid button target/region " + i);
    if (decodedButtons[i].dataType !== button.dataType ||
        JSON.stringify(decodedButtons[i].rect) !== JSON.stringify(rect))
      throw new Error("button round-trip mismatch " + i);
  });
  console.log(`OK containers: ${expectedButtons.length}, 4 jump regions + battery`);

  // Check references against the actual image table, including nested buttons.
  for (let e = 0; e < face.elements.length; e++) {
    const source = face.elements[e];
    const encoded = back.elements[e];
    const srcLayers = [...source.layers, ...(source.containers || []).flatMap(c => c.layers)];
    const dstLayers = [...encoded.layers, ...encoded.containers.flatMap(c => c.layers)];
    srcLayers.forEach((layer, i) => {
      const names = layer.singleRes ? [layer.singleRes.resName] : layer.selectedRes ? layer.selectedRes.res : [];
      const refs = dstLayers[i].singleRes ? [dstLayers[i].singleRes.resName] : dstLayers[i].selectedRes ? dstLayers[i].selectedRes.resName : [];
      if (names.some((name, j) => seen[Number(refs[j]) - 1] !== name))
        throw new Error("image reference resolves to wrong asset");
    });
  }
  console.log(`OK references: ${seen.length} dense resource IDs`);

  const blobs = [], table = [];
  let offset = 8;
  for (const n of seen) {
    const img = await Jimp.read(H(n));
    const { width: w, height: h, data } = img.bitmap;
    const enc = rleBGRA(w, h, data);
    blobs.push(enc);
    table.push([enc.length, offset]);
    offset += enc.length;
  }
  const imgBlob = [...SIG, ...VER, ...blobs.flat()];
  const indexBuf = table.flatMap(([len, off]) => [...le32(off), ...le32(len)]);
  const head = [2, 0, ...le16(protoBytes.length), ...le16(indexBuf.length), 0, 0, ...le32(imgBlob.length), ...le32(0)];
  const bin = Buffer.concat([Buffer.from(head), Buffer.from(protoBytes), Buffer.from(indexBuf), Buffer.from(imgBlob)]);

  // verify: re-decode image stream (extractor logic) + pixel compare
  const U = (b, i) => b[i] + (b[i + 1] << 8);
  let pos = 16 + protoBytes.length + indexBuf.length;
  if (!SIG.every((v, i) => bin[pos + i] === v)) throw new Error("SIG missing");
  pos += 8; // SIG + VER
  for (const n of seen) {
    const hdr = [...bin.slice(pos, pos + 4)]; pos += 4;
    if (JSON.stringify(hdr) !== JSON.stringify(IMG_HDR)) throw new Error("img hdr mismatch " + n);
    const w = U(bin, pos), h = U(bin, pos + 2); pos += 4;
    const src = (await Jimp.read(H(n))).bitmap;
    if (src.width !== w || src.height !== h) throw new Error("size mismatch " + n);
    const got = [];
    while (got.length < w * h) {
      const B = bin[pos++], G = bin[pos++], R = bin[pos++], A = bin[pos++];
      if (B === 137 && G === 103 && R === 69 && A === 35) {
        const bw = bin[pos++], gw = bin[pos++], rw = bin[pos++], aw = bin[pos++];
        const cnt = bin[pos] + (bin[pos + 1] << 8) + (bin[pos + 2] << 16) + (bin[pos + 3] << 24); pos += 4;
        for (let k = 0; k < cnt; k++) got.push([rw, gw, bw, aw]);
      } else got.push([R, G, B, A]);
    }
    if (got.length !== w * h) throw new Error("pixel count mismatch " + n);
    for (let i = 0; i < got.length; i++) {
      const [r, g, b, a] = got[i];
      if (src.data[i * 4] !== r || src.data[i * 4 + 1] !== g || src.data[i * 4 + 2] !== b || src.data[i * 4 + 3] !== a)
        throw new Error("pixel mismatch " + n + " px " + i);
    }
  }
  console.log(`OK bin: proto=${protoBytes.length} index=${indexBuf.length} img=${imgBlob.length} total=${bin.length}, ${seen.length} images verified`);

  const desc = `<?xml version="1.0" encoding="UTF-8"?>\n<HwTheme>\n    <title>ClaudeFit</title>\n    <title-cn>ClaudeFit</title-cn>\n    <author>opencode</author>\n    <designer>opencode</designer>\n    <screen>HWHD06</screen>\n    <version>1.0</version>\n    <font>Default</font>\n    <font-cn>\u9ed8\u8ba4</font-cn>\n    <briefinfo>{"en_US":"Pixel terminal style face for Watch Fit (280x456)."}</briefinfo>\n</HwTheme>\n`;
  fs.writeFileSync(path.join(ROOT, "description.xml"), desc);
  const zip = new AdmZip();
  zip.addFile("com.huawei.watchface", bin);
  zip.addFile("description.xml", Buffer.from(desc, "utf8"));
  zip.addFile("preview/cover.jpg", fs.readFileSync(path.join(ROOT, "preview/cover.jpg")));
  zip.addFile("preview/icon_small.jpg", fs.readFileSync(path.join(ROOT, "preview/icon_small.jpg")));
  // fixed entry timestamps => reproducible .hwt bytes across builds/machines
  const epoch = new Date("2020-01-01T00:00:00Z");
  for (const e of zip.getEntries()) e.header.time = epoch;
  zip.writeZip(path.join(ROOT, "claude-fit-pixel.hwt"));
  console.log("OK hwt:", zip.getEntries().map((e) => e.entryName).join(", "));
})().catch((e) => { console.error("FAIL:", e.message); process.exit(1); });
