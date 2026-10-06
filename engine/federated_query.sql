INSTALL iceberg;
LOAD iceberg;
INSTALL spatial;
LOAD spatial;

CREATE VIEW fiware_lake AS 
  SELECT * FROM iceberg_scan('/data/lakehouse_a_fiware/metadata/v1.metadata.json');

CREATE VIEW segittur_lake AS 
  SELECT * FROM iceberg_scan('/data/lakehouse_b_segittur/metadata/v1.metadata.json');

-- The "Query Over Everything" cross-ontology federation
SELECT 
    f.municipality_code,
    f.category AS fiware_category,
    s.tipo_espacio AS segittur_category,
    COUNT(DISTINCT f.id) AS accommodation_count,
    SUM(f.capacity_beds) AS total_bed_capacity,
    ROUND(SUM(f.capacity_beds * f.occupancy_rate), 1) AS estimated_active_guests,
    SUM(s.visitantes_mensuales) AS monthly_visitor_footfall,
    ROUND(SUM(s.visitantes_mensuales * s.gasto_medio_diario_eur), 2) AS estimated_monthly_spend_eur,
    ROUND(CAST(SUM(s.visitantes_mensuales) AS DOUBLE) / NULLIF(SUM(f.capacity_beds) * 30.0, 0), 2) AS tourism_pressure_index
FROM fiware_lake f
JOIN segittur_lake s 
  ON f.municipality_code = s.codigo_ine_municipio
 AND (
     (f.category = 'Hotel' AND s.tipo_espacio = 'AlojamientoHotelero') OR
     (f.category = 'Camping' AND s.tipo_espacio = 'ZonaAcampada') OR
     (s.tipo_espacio IN ('RecursoCultural', 'EspacioNatural'))
 )
GROUP BY f.municipality_code, f.category, s.tipo_espacio
ORDER BY tourism_pressure_index DESC;
