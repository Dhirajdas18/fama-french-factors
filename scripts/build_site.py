"""Build site/index.html from the fetched IIMA factors (run scripts/fetch_data.py first)."""

from pathlib import Path

from ff import data
from ff.site import build_html


def main() -> None:
    f = data.factors()
    out = Path("site/index.html")
    out.parent.mkdir(exist_ok=True)
    out.write_text(build_html(f, data.release()), encoding="utf-8")
    print(f"{out} ({out.stat().st_size / 1e3:.0f} kB), release {data.release()}, {len(f)} months")


if __name__ == "__main__":
    main()
