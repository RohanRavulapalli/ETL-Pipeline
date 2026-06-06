/*
WARNING: running this file generates an error, specifically the following error:

    Catgalog Error:
        Table with name atom_sites_comprehensive does not exist!
        Did you mean "carbon_db.atom_sites_comprehensive"?
    
I tried using different prefixes, such as carbon_db.atom_sites_comprehensive, main.atom_sites_comprehensive,
and just atom_sites_comprehensive, but none of these worked.

When I checked the catalog, I could see that the table atom_sites_comprehensive did exist in the carbon_db schema.

When I went to the MotherDuck web IDE and ran this script, I ran into similar errors, but prefixing
the tables with main seemed to work. Still doesnt work when using duckdb CLI however.
*/

CREATE OR REPLACE TABLE carbon_db.bonds_comprehensive (
	file VARCHAR,
	atom1_label VARCHAR,
	atom2_label VARCHAR,
	bond_type VARCHAR,
	PRIMARY KEY (file, atom1_label, atom2_label, bond_type)
);