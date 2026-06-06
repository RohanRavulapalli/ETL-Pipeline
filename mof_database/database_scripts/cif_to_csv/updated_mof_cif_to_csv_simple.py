#!/usr/bin/env python3

import argparse
import csv
import shlex
from io import StringIO
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from frac_cart import get_fractional_to_cartesian_matrix
import numpy as np

MISSING_TOKENS = {"?", ".", "NA", "na", "N/A", "n/a"}

def clean(val: Optional[str]) -> Optional[str]:
    if val is None:
        return None
    s = str(val).strip().strip("'\"").strip()
    if s in MISSING_TOKENS or s == "":
        return None
    return s

def norm_symbol(s: Optional[str]) -> Optional[str]:
    s = clean(s)
    return s.upper() if s else None

def first_nonempty(row: Dict[str, Any], keys: List[str]) -> Optional[str]:
    for k in keys:
        if k in row:
            v = clean(row.get(k))
            if v is not None:
                return v
    return None

def parse_cif(text: str) -> List[Tuple[List[str], List[List[str]]]]:

    lines = text.splitlines()
    i = 0
    n = len(lines)
    loops = []
    single_values = []

    while i < n:
        line = lines[i].strip()

         # Handle single values (key-value pairs)
        if line.startswith("_") and not line.lower() == "loop_":
            parts = line.split(None, 1)  # Split on first whitespace
            if len(parts) == 2:
                key, value = parts
                single_values.append((key, value))
            i += 1

        elif line.lower() == "loop_":
            i += 1
            tags = []
            while i < n and lines[i].strip().startswith("_"):
                tags.append(lines[i].strip())
                i += 1
            rows: List[List[str]] = []
            while i < n:
                s = lines[i].strip()
                if not s:
                    i += 1
                    break
                if s.lower() == "loop_" or s.startswith("_") or s.lower().startswith("data_"):
                    break
                try:
                    vals = shlex.split(s)
                except ValueError:
                    vals = s.split()
                if vals:
                    rows.append(vals)
                i += 1
            loops.append((tags, rows))

        else:
            i += 1

    return {
        "loops": loops,
        "single_values": single_values
    }

def loop_to_dicts(tags: List[str], rows: List[List[str]]) -> List[Dict[str, Any]]:
    lt = [t.lower() for t in tags]
    out: List[Dict[str, Any]] = []
    for r in rows:
        if len(r) < len(lt):
            r = r + [None] * (len(lt) - len(r))
        elif len(r) > len(lt):
            r = r[:len(lt)]
        out.append({k: clean(v) for k, v in zip(lt, r)})
    return out

def extract_from_cif(path: Path, charge_stats: Dict[str, int]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    try:
        text = path.read_text(errors="ignore")
    except Exception as e:
        print(f"[WARN] Could not read {path}: {e}")
        return [], []

    parsed = parse_cif(text)

    loops = parsed['loops']

    single_values = parsed['single_values']

    atom_type_by_symbol: Dict[str, Dict[str, Any]] = {}
    for tags, rows in loops:
        lower_tags = [t.lower() for t in tags]
        if any(t.startswith("_atom_type_") for t in lower_tags):
            table = loop_to_dicts(tags, rows)
            symbol_key = None
            for cand in ("_atom_type_symbol", "_atom_type_label", "_atom_type_type"):
                if table and cand in table[0]:
                    symbol_key = cand
                    break
                if not symbol_key and any(cand in row for row in table):
                    symbol_key = cand
                    break
            charge_keys = ["_atom_type_partial_charge", "_atom_type_charge"]
            for row in table:
                sym = norm_symbol(row.get(symbol_key)) if symbol_key else None
                if not sym:
                    continue
                charge_val = first_nonempty(row, charge_keys)
                if charge_val is None:
                    for k, v in row.items():
                        if "charge" in k and clean(v) is not None:
                            charge_val = clean(v)
                            break
                atom_type_by_symbol[sym] = {
                    "description": row.get("_atom_type_description"),
                    "partial_charge": charge_val,
                }

        # Extract cell parameters from single_values
    cell_params = {}
    for key, value in single_values:
        key_lower = key.lower()
        if key_lower == "_cell_length_a":
            cell_params["length_a"] = value
        elif key_lower == "_cell_length_b":
            cell_params["length_b"] = value
        elif key_lower == "_cell_length_c":
            cell_params["length_c"] = value
        elif key_lower == "_cell_angle_alpha":
            cell_params["alpha"] = value
        elif key_lower == "_cell_angle_beta":
            cell_params["beta"] = value
        elif key_lower == "_cell_angle_gamma":
            cell_params["gamma"] = value

    atoms_out: List[Dict[str, Any]] = []
    bonds_out: List[Dict[str, Any]] = []

    for tags, rows in loops:
        lower_tags = [t.lower() for t in tags]
        if any(t.startswith("_atom_site_") for t in lower_tags):
            table = loop_to_dicts(tags, rows)
            for row in table:
                label = row.get("_atom_site_label")
                element = row.get("_atom_site_type_symbol")
                fx = row.get("_atom_site_fract_x")
                fy = row.get("_atom_site_fract_y")
                fz = row.get("_atom_site_fract_z")
                site_charge = first_nonempty(row, ["_atom_site_charge", "_atom_site_partial_charge"])
                if site_charge is None:
                    for k, v in row.items():
                        if "charge" in k and clean(v) is not None:
                            site_charge = clean(v)
                            break

                desc = None
                charge = None
                key = norm_symbol(element)
                if key and key in atom_type_by_symbol:
                    desc = atom_type_by_symbol[key].get("description")
                    charge = atom_type_by_symbol[key].get("partial_charge")

                chosen = None
                if site_charge is not None:
                    chosen = site_charge
                    charge_stats["from_site"] += 1
                elif charge is not None:
                    chosen = charge
                    charge_stats["from_type"] += 1
                else:
                    charge_stats["missing"] += 1

                # converting fractal to cartesian coordinates:

                V_frac = np.array([fx, fy, fz])

                r = get_fractional_to_cartesian_matrix(
                            a=cell_params["length_a"],
                            b=cell_params["length_b"],
                            c=cell_params["length_c"],
                            alpha=cell_params["alpha"],
                            beta=cell_params["beta"],
                            gamma=cell_params["gamma"]
                        )
                
                V_cart = np.dot(r, V_frac)
                
                x_cart, y_cart, z_cart = V_cart

                if any([label, fx, fy, fz]):
                    atoms_out.append({
                        "file": path.name,
                        "atom_label": label,
                        "element": element,
                        "description": desc,
                        "fract_x": fx,
                        "fract_y": fy,
                        "fract_z": fz,
                        "partial_charge": chosen,
                        **cell_params,  # Include cell parameters in each atom
                        "cart_x": x_cart,
                        "cart_y": y_cart,
                        "cart_z": z_cart
                    })

    for tags, rows in loops:
        lower_tags = [t.lower() for t in tags]
        if any(t.startswith("_geom_bond_") or t.startswith("_ccdc_geom_bond_") for t in lower_tags):
            table = loop_to_dicts(tags, rows)
            for row in table:
                a1 = row.get("_geom_bond_atom_site_label_1")
                a2 = row.get("_geom_bond_atom_site_label_2")
                btype = row.get("_ccdc_geom_bond_type") or row.get("_geom_bond_type")
                if a1 or a2 or btype:
                    bonds_out.append({
                        "file": path.name,
                        "atom1_label": a1,
                        "atom2_label": a2,
                        "bond_type": btype
                    })

    return atoms_out, bonds_out

def find_cif_paths(paths: List[str], recursive: bool) -> List[Path]:
    out: List[Path] = []
    for p in paths:
        pth = Path(p)
        if pth.is_file() and pth.suffix.lower() == ".cif":
            out.append(pth)
        elif pth.is_dir():
            it = pth.rglob("*.cif") if recursive else pth.glob("*.cif")
            out.extend([q for q in it if q.is_file()])
    seen = set()
    unique = []
    for p in out:
        rp = p.resolve()
        if rp not in seen:
            unique.append(p)
            seen.add(rp)
    return unique

def write_csv_readable(out_path: Path, rows: List[Dict[str, Any]], field_order: List[str]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    buf = StringIO()
    writer = csv.DictWriter(buf, fieldnames=field_order)
    writer.writeheader()
    for r in rows:
        writer.writerow({k: r.get(k) for k in field_order})
    text = buf.getvalue().replace(",", ", ")
    with out_path.open("w", encoding="utf-8", newline="") as f:
        f.write(text)

def process_file_list(file_paths):
    """Process a list of file paths directly (bypasses command line interface)"""
    # Convert string paths to Path objects  
    cif_paths = [Path(p) for p in file_paths]
    
    all_atoms: List[Dict[str, Any]] = []
    all_bonds: List[Dict[str, Any]] = []
    charge_stats = {"from_site": 0, "from_type": 0, "missing": 0}

    # Process each file (same logic as main())
    for p in cif_paths:
        atoms, bonds = extract_from_cif(p, charge_stats)
        all_atoms.extend(atoms)
        all_bonds.extend(bonds)

    # Write output CSVs (same as main())
    atoms_fields = ["file", "atom_label", "element", "description", "fract_x", "fract_y", "fract_z", "partial_charge"]
    bonds_fields = ["file", "atom1_label", "atom2_label", "bond_type"]

    write_csv_readable(Path("atom_sites.csv"), all_atoms, atoms_fields)
    write_csv_readable(Path("bonds.csv"), all_bonds, bonds_fields)

    print(f"Wrote {len(all_atoms)} atom rows to atom_sites.csv")
    print(f"Wrote {len(all_bonds)} bond rows to bonds.csv")
    
    return len(all_atoms), len(all_bonds)

def main():
    ap = argparse.ArgumentParser(description="Extract MOF atom sites and bonds from CIF into CSV")
    ap.add_argument("paths", nargs="+", help="CIF files or directories to process")
    ap.add_argument("-r", "--recursive", action="store_true", help="Recurse into subdirectories")
    args = ap.parse_args()

    cif_paths = find_cif_paths(args.paths, args.recursive)
    if not cif_paths:
        print("No CIF files found. Provide one or more CIF files or directories.")
        return

    all_atoms: List[Dict[str, Any]] = []
    all_bonds: List[Dict[str, Any]] = []
    charge_stats = {"from_site": 0, "from_type": 0, "missing": 0}

    for p in cif_paths:
        atoms, bonds = extract_from_cif(p, charge_stats)
        all_atoms.extend(atoms)
        all_bonds.extend(bonds)

    atoms_fields = ["file", "atom_label", "element", "description", "fract_x", "fract_y", "fract_z", "partial_charge"]
    bonds_fields = ["file", "atom1_label", "atom2_label", "bond_type"]

    write_csv_readable(Path("atom_sites.csv"), all_atoms, atoms_fields)
    write_csv_readable(Path("bonds.csv"), all_bonds, bonds_fields)

    print(f"Wrote {len(all_atoms)} atom rows to atom_sites.csv")
    print(f"Wrote {len(all_bonds)} bond rows to bonds.csv")

if __name__ == "__main__":
    main()