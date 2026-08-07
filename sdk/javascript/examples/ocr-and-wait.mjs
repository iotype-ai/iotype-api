// IOTYPE_TOKEN=... node examples/ocr-and-wait.mjs contract.pdf
import { Iotype, ProcessingTimeout, fileResult } from "@iotype-ai/sdk";

const path = process.argv[2];
if (!path) { console.error("usage: ocr-and-wait.mjs <file.pdf|file.jpg>"); process.exit(1); }

const io = new Iotype();

const file = await io.ocr(path, { summarize: true });
console.log("uuid:", file.uuid, "(store this — you can resume after a restart)");

try {
  console.log("\n--- extracted text ---");
  console.log(await io.waitFor(file.uuid, { processType: "ocr" }));

  const summary = fileResult(await io.track(file.uuid), "summarize");
  if (summary) console.log("\n--- summary ---\n" + summary);
} catch (e) {
  if (e instanceof ProcessingTimeout) console.log(`still processing; resume with waitFor("${e.uuid}")`);
  else throw e;
}
