# Presentation

Install dependencies and generate the deck plus architecture PNG:

```powershell
python -m pip install -r requirements.txt
python presentation/build_presentation.py
```

The generated `eventhouse-schema-drift-reference.pptx` is committed for customer workshops. Edit the slide definitions in `build_presentation.py` and narrative guidance in `slide-notes.md`, then regenerate.
