/*
This file defines various SQL functions that will be used 
for converting fractional coordinates to cartesian coordinates
natively within duckdb.

The functions are based on the logic outlined by the functions listed in fract_cart.py.

It is currently quite difficult to register table-valued and array-valued functions defined in python
to a duckdb database, thus, these functions were made as an attempt to bridge the gap and
transform coordinates natively within duckdb. Furthermore, defining macros directly within duckdb
can make future calculation updates easier.

Note: we use WITH MATERIALIZED for every CTE in each macro due to the CTE scope rules of duckdb
(not explicitly specifying that the CTE should be materialized results in a catalog error
 saying that a given CTE could not be found when you try to query it)

*/

CREATE OR REPLACE MACRO carbon_db.degree_to_radians(angle, angle_in_degrees := True) AS (
    -- this macro will convert an angle from degrees to radians if it is not already in radians
       CASE WHEN angle_in_degrees IS TRUE 
                 THEN radians(angle)
                      ELSE angle 
                            END);

CREATE OR REPLACE MACRO carbon_db.fractional_to_cartesian_matrix(a, b, c, alpha, beta, gamma, angle_in_degrees := True) AS TABLE(
    -- this macro builds the transformation matrix that converts fractional coordinates to cartesian coordinates.
    WITH angle_conversions AS MATERIALIZED (
        SELECT carbon_db.degree_to_radians(alpha, angle_in_degrees) AS alpha_rad,
               carbon_db.degree_to_radians(beta, angle_in_degrees) AS beta_rad,
               carbon_db.degree_to_radians(gamma, angle_in_degrees) AS gamma_rad,
               a AS length_a,
               b AS length_b,
               c AS length_c
    ),
    trig_values AS MATERIALIZED (
        SELECT 
               COS(alpha_rad) AS cosa,
               SIN(alpha_rad) AS sina,
               COS(beta_rad) AS cosb,
               SIN(beta_rad) AS sinb,
               COS(gamma_rad) AS cosg,
               SIN(gamma_rad) AS sing,
               length_a,
               length_b,
               length_c
        FROM angle_conversions
    ),
    volume_calc AS MATERIALIZED (
        SELECT 
               cosa,
               cosb,
               cosg,
               sing,
               length_a,
               length_b,
               length_c,
               SQRT(GREATEST(
                   1.0 - (cosa * cosa) - (cosb * cosb) - (cosg * cosg) + (2.0 * cosa * cosb * cosg),
                   0.0
               )) AS volume
        FROM trig_values
    ) 
    SELECT 
        CASE 
            WHEN r.row_num = 1 THEN length_a
            ELSE 0.0
        END AS col1,
        CASE 
            WHEN r.row_num = 1 THEN length_b * cosg
            WHEN r.row_num = 2 THEN length_b * sing
            ELSE 0.0
        END AS col2,
        CASE 
            WHEN r.row_num = 1 THEN length_c * cosb
            WHEN r.row_num = 2 THEN length_c * (cosa - cosb * cosg) / sing
            WHEN r.row_num = 3 THEN length_c * volume / sing
            ELSE 0.0
        END AS col3,
        r.corresponding_coordinate
    FROM volume_calc v
    CROSS JOIN (
        VALUES 
            (1, 'cart_x'),
            (2, 'cart_y'),
            (3, 'cart_z')
    ) AS r(row_num, corresponding_coordinate)
);

CREATE OR REPLACE MACRO carbon_db.fract_to_cart(a, b, c, alpha, beta, gamma, fract_x, fract_y, fract_z, angle_in_degrees := True) AS TABLE(
    -- this macro will convert fractional to cartesian coordinates,
    -- making use of the previous two macros defined in this file
    
    WITH fractional_vector(fract_x, fract_y, fract_z) AS MATERIALIZED (
        SELECT fract_x, fract_y, fract_z
    ),
    fract_to_cart_matrix AS MATERIALIZED (
        SELECT m.col1, m.col2, m.col3, m.corresponding_coordinate
        FROM carbon_db.fractional_to_cartesian_matrix(
            a, b, c, alpha, beta, gamma, angle_in_degrees) AS m
    ),
    cartesian_coords AS MATERIALIZED (
        SELECT m.col1 * f.fract_x + m.col2 * f.fract_y + m.col3 * f.fract_z AS coord, m.corresponding_coordinate 
            -- should return a scalar for each row
        FROM fract_to_cart_matrix m 
            CROSS JOIN fractional_vector AS f
    )
    SELECT cart_x, cart_y, cart_z
    FROM (PIVOT cartesian_coords
            ON corresponding_coordinate IN ('cart_x', 'cart_y', 'cart_z')
            USING MAX(coord)) p 
);
