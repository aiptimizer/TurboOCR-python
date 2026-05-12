# Non-Latin PDFs

Nothing to do. The bundled glyphless font covers every BMP codepoint
(Latin, CJK, Arabic, Cyrillic, …), so a non-Latin scan goes through the
same single call as anything else:

```python
from pathlib import Path
from turboocr import Client

client = Client()
overlay = client.make_searchable_pdf("scan.pdf", dpi=200)
Path("/tmp/out.pdf").write_bytes(overlay)
```

## Override the bundled font

Only useful if you specifically want a **visible** text overlay (e.g. an
accessibility pipeline). For the standard "make this scan searchable"
case, the default is correct.

```python
overlay = client.make_searchable_pdf(
    "scan.pdf",
    dpi=200,
    font_path="/path/to/your-font.ttf",
)
```
