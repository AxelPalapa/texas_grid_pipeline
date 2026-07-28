SELECT 
    p.county,
    p.city,
    p.plant_id_eia,
    p.plant_name_eia,
    g.report_date,
    g.fuel_type_code_pudl,
    c.total_capacity_mw
FROM core_eia__entity_plants p 
INNER JOIN out_eia923__generation_fuel_combined g
    ON p.plant_id_eia = g.plant_id_eia
WHERE 
    p.state = 'TX' 
    AND g.report_date BETWEEN '2021-01-01' AND '2026-01-01'
GROUP BY 
    p.county,
    p.city,
    p.plant_id_eia,
    p.plant_name_eia,
    g.report_date,
    g.fuel_type_code_pudl
ORDER BY 
    g.report_date ASC,
    total_generation_mwh DESC;