SELECT 
  plant_id_eia,
  report_date,
  SUM(capacity_mw) AS total_capacity_mw
FROM out_eia__monthly_generators
GROUP BY 
  plant_id_eia,
  report_date
LIMIT 10;


