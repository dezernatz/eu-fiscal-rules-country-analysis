# EU fiscal rules country analysis

This repository collects the country-level model code, input data, notebooks, paper files, and final result workbooks used for the EU fiscal rules reform paper.

## What to look at first

- `paper/` contains the final paper handover files.
- `results/final/` contains the final country result workbooks used for the paper.
- `results/figures/` contains the SPB and debt-ratio figures used for the paper.
- `FS-DSA_Final_AT.ipynb`, `FS-DSA_Final_DE.ipynb`, `FS-DSA_Final_FI.ipynb`, `FS-DSA_Final_FR.ipynb`, and `FS-DSA_Final_IT.ipynb` are the country notebooks.
- `model/fs/` contains the fiscal sustainability model code used by the country notebooks.
- `model/dsa/` contains the debt sustainability analysis model code and reference outputs.
- `data/` contains the input workbooks used by the fiscal sustainability model.

## Final result files

The latest paper result files are in `results/final/`:

- `Austria_Results_v3.xlsx`
- `Finland_Results_v3.xlsx`
- `France_Results_v3.xlsx`
- `Germany_Results_v3.xlsx`
- `Italy_Results_v4.xlsx`

Older or superseded result files are kept in `results/archive/`.

## Result provenance

The public notebooks are copies of the verified `FS-DSA_*_ExactWorkflow.ipynb` notebooks from the project working folder. They are the provenance files for the final result workbooks:

| Country | Notebook | Final workbook | SPB target baseline -> scenario | Potential growth baseline -> scenario |
| --- | --- | --- | --- | --- |
| Austria | `FS-DSA_Final_AT.ipynb` | `Austria_Results_v3.xlsx` | 1.06% -> 1.04% | 1.10% -> 1.12% |
| Finland | `FS-DSA_Final_FI.ipynb` | `Finland_Results_v3.xlsx` | 2.27% -> 2.15% | 0.93% -> 1.00% |
| France | `FS-DSA_Final_FR.ipynb` | `France_Results_v3.xlsx` | 2.236% -> 2.239% | 1.20% -> 1.16% until 2028; about 1.00% thereafter |
| Germany | `FS-DSA_Final_DE.ipynb` | `Germany_Results_v3.xlsx` | 0.99% -> 0.84% | 0.90% -> 1.15% |
| Italy | `FS-DSA_Final_IT.ipynb` | `Italy_Results_v4.xlsx` | 2.95% -> 2.84% | 0.78% -> 0.85% |

Note: the final Finland workbook and notebook use 0.93% -> 1.00% potential growth. The paper text/table reports the older rounded growth comparison 0.90% -> 0.97%, while its SPB target values match the final v3 workbook.

## Paper files

The paper handover files are in `paper/`:

- `EU_Fiscal_Rules_Reform_Final_Version.docx`
- `Annex_1_vz_fz.docx`

## Reproducing results

1. Create and activate a Python environment.
2. Install the dependencies:

   ```powershell
   pip install -r requirements.txt
   pip install -r model/dsa/requirements.txt
   ```

3. Open the country notebooks from the repository root so relative imports resolve correctly.
4. Run the relevant country notebook.
5. Compare regenerated outputs with the files in `results/final/`.

The notebooks expect the repository layout to remain stable, especially `data/`, `model/fs/`, and `model/dsa/`.

## Notes for maintainers

- Do not commit Python cache folders, notebook checkpoints, local environments, or Office lock files.
- Keep public-repo copies limited to files that are safe to publish.
- If a result workbook is superseded, move the older version to `results/archive/` and document the new final file above.
