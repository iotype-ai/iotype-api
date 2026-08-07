"""Upload a PDF for OCR and poll until the text is ready.

    python examples/ocr_and_wait.py contract.pdf
"""
import sys
from iotype import Iotype, ProcessingTimeout

def main(path: str) -> None:
    io = Iotype()

    file = io.ocr(path, summarize=True)
    print(f"uuid: {file.uuid}  (store this — you can resume tracking after a restart)")

    try:
        text = io.wait_for(file.uuid, process_type="ocr", timeout=1800)
    except ProcessingTimeout as exc:
        print(f"still processing; resume later with wait_for({exc.uuid!r})")
        return

    print("\n--- extracted text ---")
    print(text)

    summary = io.track(file.uuid).result("summarize")
    if summary:
        print("\n--- summary ---")
        print(summary)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: ocr_and_wait.py <file.pdf|file.jpg>")
    main(sys.argv[1])
