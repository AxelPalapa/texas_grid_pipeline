WITH temp_capacity_table AS (
    SELECT 
        plant_id_eia,
        report_date,
        SUM(capacity_mw) AS total_capacity_mw
    FROM out_eia__monthly_generators
    GROUP BY 
        plant_id_eia,
        report_date
)
SELECT 
    p.county,
    p.city,
    p.plant_id_eia,
    p.plant_name_eia,
    g.report_date,
    g.fuel_type_code_pudl,
    c.total_capacity_mw, 
    SUM(g.net_generation_mwh) AS total_generation_mwh 
FROM core_eia__entity_plants p 
INNER JOIN out_eia923__generation_fuel_combined g
    ON p.plant_id_eia = g.plant_id_eia
LEFT JOIN temp_capacity_table c 
    ON p.plant_id_eia = c.plant_id_eia 
    AND g.report_date = c.report_date
WHERE 
    p.state = 'TX' 
    AND p.county IN ('Harris', 'Fort Bend', 'Montgomery', 'Brazoria', 'Galveston')
    AND g.report_date BETWEEN '2021-01-01' AND '2026-01-01'
GROUP BY 
    p.county,
    p.city,
    p.plant_id_eia,
    p.plant_name_eia,
    g.report_date,
    g.fuel_type_code_pudl,
    c.total_capacity_mw 
ORDER BY 
    g.report_date ASC,
    total_generation_mwh DESC;