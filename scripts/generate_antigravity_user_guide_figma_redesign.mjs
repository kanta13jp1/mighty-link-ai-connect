import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const [sourcePath, outputPath, qaDir] = process.argv.slice(2);
if (!sourcePath || !outputPath || !qaDir) {
  throw new Error(
    "Usage: generate_antigravity_user_guide_figma_redesign.mjs <source.pptx> <output.pptx> <qa-dir>",
  );
}

const FIGMA_FILE_URL = "https://www.figma.com/slides/t1LgWfEHQKTAkCxsxUFkgD";
const FIGMA_EXPORT_DOC =
  "https://help.figma.com/hc/en-us/articles/24848334599447-Export-from-Figma-Slides";

const fillMap = new Map([
  ["F7FAFC", "#F7F9FC"],
  ["00A5E3", "#00A7C7"],
  ["EF7E00", "#FF8A00"],
  ["2F9E63", "#16A56A"],
  ["7B61A8", "#6F5BD3"],
  ["D9485F", "#DB3241"],
  ["071A2B", "#101820"],
  ["102B3B", "#082532"],
  ["C9D8E1", "#D1DBE2"],
  ["E8F6FC", "#E6F7FA"],
  ["FFFFFF", "#FFFFFF"],
]);

const textColorMap = new Map([
  ["17242B", "#101820"],
  ["536978", "#52616B"],
  ["EDF6FA", "#FFFFFF"],
  ["00A5E3", "#00A7C7"],
  ["FFFFFF", "#FFFFFF"],
  ["E8F4F7", "#ECF5F7"],
  ["9FC2D4", "#74C8D8"],
  ["EF7E00", "#FF8A00"],
  ["2F9E63", "#16A56A"],
  ["7B61A8", "#6F5BD3"],
  ["D9485F", "#DB3241"],
  ["D8EAF1", "#D9EEF2"],
  ["B9D6E4", "#B9DDE4"],
  ["526571", "#52616B"],
  ["4A5F68", "#52616B"],
]);

function firstRunColor(proto) {
  for (const paragraph of proto?.paragraphs ?? []) {
    for (const run of paragraph.runs ?? []) {
      const value = run?.textStyle?.fill?.color?.value;
      if (value) return value;
    }
  }
  return null;
}

function isLargeCard(record) {
  const [, , width = 0, height = 0] = record.bbox ?? [];
  return width >= 180 && height >= 70;
}

async function writeBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

await fs.mkdir(path.dirname(outputPath), { recursive: true });
await fs.mkdir(qaDir, { recursive: true });

const presentation = await PresentationFile.importPptx(
  await FileBlob.load(sourcePath),
);
const before = await presentation.inspect({
  kind: "slide,textbox,shape,image,table,chart,notes,layout",
  maxChars: 300000,
});
const records = before.ndjson
  .split(/\r?\n/)
  .filter(Boolean)
  .map((line) => JSON.parse(line));

const editLog = [];
for (const record of records) {
  if (!record.id?.startsWith("sh/")) continue;

  const shape = presentation.resolve(record.id);
  const proto = shape.toProto?.();
  const sourceFill = proto?.shape?.fill?.color?.value ?? null;
  const targetFill = sourceFill ? fillMap.get(sourceFill) : null;
  const sourceTextColor = firstRunColor(proto);
  const targetTextColor = sourceTextColor
    ? textColorMap.get(sourceTextColor)
    : null;

  if (targetFill) {
    shape.fill = targetFill;
  }
  if (targetTextColor && String(shape.text ?? "").length > 0) {
    shape.text.color = targetTextColor;
  }

  if (sourceFill === "FFFFFF" && isLargeCard(record)) {
    shape.line = { style: "solid", fill: "#D5DFE5", width: 1 };
    shape.borderRadius = 12;
    shape.shadow = "shadow-sm";
  } else if (sourceFill === "102B3B") {
    shape.line = { style: "solid", fill: "#082532", width: 0 };
    shape.borderRadius = 14;
    shape.shadow = "shadow-sm";
    if (String(shape.text ?? "").length > 450) {
      shape.text.autoFit = "shrinkText";
    }
  } else if (sourceFill === "071A2B" && isLargeCard(record)) {
    shape.borderRadius = 10;
  }

  if (targetFill || targetTextColor) {
    editLog.push({
      slide: record.slide,
      id: record.id,
      name: record.name ?? "",
      sourceFill,
      targetFill,
      sourceTextColor,
      targetTextColor,
    });
  }
}

for (const slide of presentation.slides.items) {
  slide.speakerNotes.append(
    `\n- Figma Slides visual system: ${FIGMA_FILE_URL}` +
      `\n- Figma Slides PPTX export guidance: ${FIGMA_EXPORT_DOC}`,
  );
  slide.speakerNotes.setVisible(true);
}

for (let index = 0; index < presentation.slides.items.length; index += 1) {
  const slide = presentation.slides.items[index];
  const slideNumber = String(index + 1).padStart(2, "0");
  await writeBlob(
    path.join(qaDir, `slide-${slideNumber}.png`),
    await presentation.export({ slide, format: "png", scale: 1 }),
  );
  await fs.writeFile(
    path.join(qaDir, `slide-${slideNumber}.layout.json`),
    await (await slide.export({ format: "layout" })).text(),
  );
}

const after = await presentation.inspect({
  kind: "slide,textbox,shape,image,table,chart,notes",
  maxChars: 300000,
});
await fs.writeFile(path.join(qaDir, "final-inspect.ndjson"), after.ndjson);
await fs.writeFile(
  path.join(qaDir, "restyle-audit.json"),
  JSON.stringify(
    {
      source: sourcePath,
      output: outputPath,
      figmaFileUrl: FIGMA_FILE_URL,
      slideCount: presentation.slides.items.length,
      editedObjects: editLog.length,
      palette: Object.fromEntries(fillMap),
      textPalette: Object.fromEntries(textColorMap),
      edits: editLog,
    },
    null,
    2,
  ),
);

const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(outputPath);

console.log(
  JSON.stringify(
    {
      outputPath,
      qaDir,
      slideCount: presentation.slides.items.length,
      editedObjects: editLog.length,
      figmaFileUrl: FIGMA_FILE_URL,
    },
    null,
    2,
  ),
);
