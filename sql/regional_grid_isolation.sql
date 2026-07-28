SELECT 
    p.county,
    p.city,
    g.report_date,
    g.fuel_type_code_pudl,
    SUM(g.net_generation_mwh) AS total_generation_mwh 
FROM core_eia__entity_plants p 
INNER JOIN out_eia923__generation_fuel_combined g
    ON p.plant_id_eia = g.plant_id_eia
WHERE 
    p.state = 'TX' 
    AND p.county IN ('Harris', 'Fort Bend', 'Montgomery', 'Brazoria', 'Galveston')
    AND g.report_date IN ('2021-02-01', '2023-08-01', '2024-01-01', '2025-05-01')
GROUP BY 
    p.county,
    p.city,
    g.report_date,
    g.fuel_type_code_pudl
ORDER BY 
    g.report_date ASC,
    total_generation_mwh DESC;
