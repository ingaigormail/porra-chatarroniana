-- =============================================================================
-- APUESTAS QUINIELA / PORRA / FINALISTAS — Porra Chatarroniana
-- Pegar en Supabase → SQL Editor → Run
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1) VISTA UNIFICADA (recomendada): todas las apuestas en una sola tabla
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_apuestas_todas AS

-- Quiniela y porra (por partido)
SELECT
    u.nombre AS usuario,
    q.tipo AS tipo_apuesta,          -- 'quiniela' o 'porra'
    p.id AS partido_id,
    p.fase,
    el.nombre AS equipo_local,
    ev.nombre AS equipo_visitante,
    CASE
        WHEN q.tipo = 'quiniela' THEN '1/X/2 → ' || COALESCE(q.eleccion_quiniela, '?')
        WHEN q.tipo = 'porra' THEN
            'Marcador → '
            || COALESCE(q.goles_local_apostados::text, '0')
            || '-'
            || COALESCE(q.goles_visitante_apostados::text, '0')
        ELSE '—'
    END AS apuesta,
    q.puntos_provisionales,
    q.puntos_finales,
    q.validado,
    q.fecha_apuesta
FROM quinielas q
JOIN usuarios u ON u.id = q.usuario_id
JOIN partidos p ON p.id = q.partido_id
LEFT JOIN equipos el ON el.id = p.equipo_local_id
LEFT JOIN equipos ev ON ev.id = p.equipo_visitante_id

UNION ALL

-- Finalistas (una fila por usuario)
SELECT
    u.nombre AS usuario,
    'finalistas' AS tipo_apuesta,
    NULL::integer AS partido_id,
    'Final' AS fase,
    f1.nombre AS equipo_local,       -- finalista 1
    f2.nombre AS equipo_visitante,   -- finalista 2
  'Finalistas → ' || f1.nombre || ' + ' || f2.nombre AS apuesta,
    NULL::integer AS puntos_provisionales,
    fa.puntos AS puntos_finales,
    (fa.puntos IS NOT NULL AND fa.puntos > 0) AS validado,
    fa.fecha_apuesta
FROM finalistas_apostados fa
JOIN usuarios u ON u.id = fa.usuario_id
LEFT JOIN equipos f1 ON f1.id = fa.finalista_1_id
LEFT JOIN equipos f2 ON f2.id = fa.finalista_2_id;

-- Consultar la vista:
-- SELECT * FROM v_apuestas_todas ORDER BY usuario, tipo_apuesta, partido_id;


-- -----------------------------------------------------------------------------
-- 2) SOLO QUINIELA / PORRA (detalle por partido)
-- -----------------------------------------------------------------------------
/*
SELECT
    u.nombre AS usuario,
    q.tipo,
    p.id AS partido,
    p.fase,
    el.nombre || ' vs ' || ev.nombre AS partido_nombre,
    p.tipo_apuesta AS tipo_partido_configurado,
    CASE
        WHEN q.tipo = 'quiniela' THEN q.eleccion_quiniela
        ELSE q.goles_local_apostados::text || '-' || q.goles_visitante_apostados::text
    END AS eleccion,
    q.puntos_provisionales,
    q.puntos_finales,
    q.validado,
    q.fecha_apuesta
FROM quinielas q
JOIN usuarios u ON u.id = q.usuario_id
JOIN partidos p ON p.id = q.partido_id
LEFT JOIN equipos el ON el.id = p.equipo_local_id
LEFT JOIN equipos ev ON ev.id = p.equipo_visitante_id
WHERE q.tipo IN ('quiniela', 'porra')
ORDER BY p.fase, p.id, u.nombre;
*/


-- -----------------------------------------------------------------------------
-- 3) SOLO FINALISTAS
-- -----------------------------------------------------------------------------
/*
SELECT
    u.nombre AS usuario,
    f1.nombre AS finalista_1,
    f2.nombre AS finalista_2,
    fa.puntos,
    fa.fecha_apuesta
FROM finalistas_apostados fa
JOIN usuarios u ON u.id = fa.usuario_id
LEFT JOIN equipos f1 ON f1.id = fa.finalista_1_id
LEFT JOIN equipos f2 ON f2.id = fa.finalista_2_id
ORDER BY u.nombre;
*/


-- -----------------------------------------------------------------------------
-- 4) QUIÉN NO HA APOSTADO (quiniela/porra en partidos abiertos o ya configurados)
-- -----------------------------------------------------------------------------
/*
WITH usuarios_todos AS (
    SELECT id, nombre FROM usuarios
),
partidos_apuesta AS (
    SELECT id, fase, tipo_apuesta
    FROM partidos
    WHERE tipo_apuesta IN ('quiniela', 'porra')
)
SELECT
    ut.nombre AS usuario,
    pa.id AS partido_id,
    pa.fase,
    pa.tipo_apuesta AS tipo_requerido,
    'FALTA' AS estado
FROM usuarios_todos ut
CROSS JOIN partidos_apuesta pa
LEFT JOIN quinielas q
    ON q.usuario_id = ut.id AND q.partido_id = pa.id
WHERE q.id IS NULL
ORDER BY pa.fase, pa.id, ut.nombre;
*/


-- -----------------------------------------------------------------------------
-- 5) QUIÉN NO HA APOSTADO FINALISTAS
-- -----------------------------------------------------------------------------
/*
SELECT u.nombre AS usuario, 'FALTA finalistas' AS estado
FROM usuarios u
LEFT JOIN finalistas_apostados fa ON fa.usuario_id = u.id
WHERE fa.id IS NULL
ORDER BY u.nombre;
*/
