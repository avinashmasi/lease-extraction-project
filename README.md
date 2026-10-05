# lease-extraction-project

Team Members:
- Avinash
- Samith
- Kareena

Workflow:

1. git pull
2. Make changes
3. git add .
4. git commit -m "message"
5. git push

Run the YAML combiner on Windows (PowerShell):

```powershell
py -3.14 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe '.\yaml_combine_new_ontology_format 3 1 2.py'
```

Use the `.venv` Python for subsequent runs; the system Python may not have PyYAML installed.