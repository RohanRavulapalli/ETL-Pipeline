CREATE TABLE IF NOT EXISTS carbon_db.atom_sites_comprehensive
 (
    file VARCHAR NOT NULL, 
    atom_label VARCHAR NOT NULL,        
    element            VARCHAR,        
    description        VARCHAR,        
    fract_x            DOUBLE,         
    fract_y            DOUBLE,         
    fract_z            DOUBLE,         
    partial_charge     DOUBLE,         
    length_a           DOUBLE,         
    length_b           DOUBLE,         
    length_c           DOUBLE,      
    alpha              DOUBLE,         
    beta               DOUBLE,         
    gamma              DOUBLE,         
    cart_x             DOUBLE,         
    cart_y             DOUBLE,         
    cart_z             DOUBLE,    
    PRIMARY KEY(file, atom_label)
);