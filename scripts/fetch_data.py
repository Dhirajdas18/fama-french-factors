"""Download the latest IIMA factor release into data/iima/ (not committed)."""

from ff.data import fetch

if __name__ == "__main__":
    print(f"IIMA release {fetch()} -> data/iima/")
