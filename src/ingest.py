"""Baixa o dataset bruto e valida o checksum, para garantir reprodutibilidade."""
import hashlib
import urllib.request

from config import RAW, SOURCE_SHA256, SOURCE_URL


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    RAW.parent.mkdir(parents=True, exist_ok=True)
    if not RAW.exists():
        print(f"Baixando {SOURCE_URL}")
        urllib.request.urlretrieve(SOURCE_URL, RAW)
    digest = sha256(RAW)
    if digest != SOURCE_SHA256:
        raise SystemExit(f"Checksum inesperado: {digest}. A fonte mudou; revise antes de seguir.")
    print(f"OK: {RAW.name} ({RAW.stat().st_size/1e6:.1f} MB), sha256 conferido")


if __name__ == "__main__":
    main()
