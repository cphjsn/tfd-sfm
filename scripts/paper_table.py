#!/usr/bin/env python3
"""Print the HTML rows of the page's results table from the paper's main table
(tab:aggregated_results_all_horizontal in sec/experiments.tex).

The page shows RRA@5, RTA@5 and AUC@10 per dataset; the paper has, per dataset, RRA at three
thresholds, RTA at three thresholds and AUC@10 (IMC2021: @3/@5/@10 instead of @1/@5/@10).

    python scripts/paper_table.py <overleaf>/sec/experiments.tex > table_rows.html
"""
import re
import sys

COLS = (1, 4, 6)  # RRA@5, RTA@5, AUC@10 within each dataset's 7 columns
DATASETS = 4


def strip_macros(cell):
    """The number of a cell such as \\rev{\\hcb{97.9}}, with whether it is bold (best) or
    underlined (second best)."""
    best = bool(re.search(r"\\hcb\w*\{", cell))
    second = bool(re.search(r"\\hcu\w*\{", cell))
    value = re.findall(r"\d+\.\d+|\d+", re.sub(r"\\[a-zA-Z]+", "", cell))
    return (value[0] if value else ""), best, second


def main():
    tex = open(sys.argv[1]).read()
    body = tex.split(r"\label{tab:aggregated_results_all_horizontal}")[1].split(r"\bottomrule")[0]
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("%") or "&" not in line or line.startswith("&") or "multicolumn" in line:
            continue
        cells = [c.strip() for c in line.rstrip("\\").split("&")]
        name = re.sub(r"\\cite\{[^}]*\}", "", cells[0])
        name = name.replace(r"\rev{\textbf{\ours{}}}", "TFD-SfM (ours)").replace(r"\ours{}", "TFD-SfM")
        name = re.sub(r"\\[a-zA-Z]+\{|\}", "", name).strip()
        values = cells[1:]
        if len(values) != 7 * DATASETS:
            continue
        tds = []
        for d in range(DATASETS):
            for c in COLS:
                v, best, second = strip_macros(values[7 * d + c])
                cls = ' class="best"' if best else ' class="second"' if second else ""
                tds.append(f"<td{cls}>{v}</td>")
        ours = ' class="ours"' if "ours" in name else ""
        print(f"<tr{ours}><th>{name}</th>{''.join(tds)}</tr>")


if __name__ == "__main__":
    main()
