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

Effective rent abstraction:

- `Effective_Rent_Monthly` and `Effective_Rent_Yearly` share a monthly-first
  stated-effective-rent source priority. Stated effective values override
  derived incentive calculations; only period conversion is applied.
- Without a stated effective value, spread eligible landlord-funded,
  non-repayable incentives (including fit-out contributions and TI allowances)
  across the initial lease term. Never deduct repayable contributions or
  occupancy/vacancy allocations, or use invoice/payment/VAT totals as rent.
- Reject non-lease engagement/service agreements. Missing required evidence
  returns `i dont know`; the currency UOM fields retain `EUR`, `USD`, or an
  empty string when the amount/currency is not determinable.
- Keep full precision until the final output, then round half up to two
  decimals. For example, annual effective rent `212639.94` converts to monthly
  `17720.00` because the unrounded result is `17719.995`.
- The amount templates include worked examples for free rent, no incentives,
  contributions, direct values, rejected payment schedules, deferred rent,
  service agreements, occupancy allocations, source priority and stepped rent.
- Both model paths for all four effective-rent fields use a dedicated
  `Effective-Rent-Context`, rather than the broad `Terms-Context`. Separate
  searches retrieve stated effective values, annual base rent, initial term,
  incentives/repayment clauses, document identity and currency evidence.
- For derived values, the prompts require an evidence register and a
  term-total calculation: gross contractual base rent minus each eligible
  incentive once. Divide net term rent by initial months for the monthly
  field or initial years for the yearly field, retaining full precision.
- These YAML files configure model retrieval and instructions; they do not
  implement a deterministic arithmetic runner. Validate live extraction
  against source lease clauses as well as manual comparison values.