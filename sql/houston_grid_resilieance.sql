CREATE OR REPLACE VIEW v_houston_grid_resilience AS
SELECT 
    h.county,
    h.city,
    h.plant_id_eia,
    h.plant_name_eia,
    h.report_date,
    (DAY(LAST_DAY(h.report_date))*24) AS hours_in_month,
    h.fuel_type_code_pudl,
    h.total_capacity_mw, 
    h.total_generation_mwh,
    ROUND((h.total_generation_mwh/(h.total_capacity_mw * (DAY(LAST_DAY(h.report_date))*24))*100), 2) AS utilization_pct,
    w.TMAX,
    w.TMIN,
    w.PRCP
FROM houston_grid_history AS h
INNER JOIN houston_monthly_weather AS w
  ON h.report_date = w.report_date
WHERE h.total_capacity_mw > 0;