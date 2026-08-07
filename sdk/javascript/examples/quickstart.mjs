// IOTYPE_TOKEN=... node examples/quickstart.mjs
import { Iotype } from "@iotype-ai/sdk";

const io = new Iotype();

console.log("translate:", await io.translate("سلام! امروز هوا بسیار عالی است.", "fa", "en"));
console.log("synthesize:", await io.synthesize("سلام دنیا", { speaker: "tanaz" }));

const files = await io.files();
console.log(`files: ${files.length} submitted`);
for (const f of files.slice(0, 5)) console.log(` ${f.uuid}  ${f.filename}`);
