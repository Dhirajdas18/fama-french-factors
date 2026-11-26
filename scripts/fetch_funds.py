"""Download (once) the NAV histories of Indian diversified equity direct-growth funds."""

from ff.funds import fetch

if __name__ == "__main__":
    print(f"{fetch()} funds cached in data/funds/")
