"""Run the synchronous endpoints end to end.

    export IOTYPE_TOKEN="..."
    python examples/quickstart.py
"""
from iotype import Iotype, IotypeError

def main() -> None:
    io = Iotype()

    print("translate:", io.translate("سلام! امروز هوا بسیار عالی است.", "fa", "en"))

    url = io.synthesize("سلام دنیا", speaker="tanaz", tone="general")
    print("synthesize:", url)
    if url:
        io.download(url, "narration.mp3")
        print("saved -> narration.mp3")

    files = io.files()
    print(f"files: {len(files)} submitted")
    for f in files[:5]:
        print(f"  {f.uuid}  {f.filename}  done={f.done}")

if __name__ == "__main__":
    try:
        main()
    except IotypeError as exc:
        raise SystemExit(f"iotype error: {exc}")
