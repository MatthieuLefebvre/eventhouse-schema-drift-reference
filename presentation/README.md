# Presentation

Install dependencies and generate the deck plus architecture PNG:

```powershell
python -m pip install -r requirements.txt
python presentation/build_presentation.py
```

The generated `eventhouse-schema-drift-reference.pptx` is committed so the architecture overview can be read without running Python. Edit the slide definitions in `build_presentation.py`, then regenerate.
