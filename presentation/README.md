# Presentation

Install dependencies and generate the deck plus architecture PNG:

```powershell
python -m pip install -r requirements.txt
python presentation/build_presentation.py
```

The script creates `eventhouse-schema-drift-reference.pptx` locally and refreshes the public architecture PNG. Generated `.pptx` files are intentionally excluded from Git. Edit the slide definitions in `build_presentation.py`, then regenerate when a local deck is needed.
