-- Tennis Intelligence 360 — all 20 analysis queries (MySQL; for PostgreSQL replace `rank` with "rank")

-- ===== A. COMPETITIONS =====
-- A1 competitions with category name
SELECT c.competition_id, c.competition_name, k.category_name FROM competitions c LEFT JOIN categories k ON k.category_id = c.category_id;
-- A2 competitions per category
SELECT k.category_name, COUNT(*) AS competitions FROM competitions c JOIN categories k ON k.category_id = c.category_id GROUP BY k.category_name ORDER BY competitions DESC;
-- A3 doubles competitions
SELECT competition_id, competition_name, gender FROM competitions WHERE type = 'doubles';
-- A4 competitions in a category (ITF Men)
SELECT c.competition_name, c.type FROM competitions c JOIN categories k ON k.category_id = c.category_id WHERE k.category_name = 'ITF Men';
-- A5 parents and sub-competitions
SELECT p.competition_name AS parent, s.competition_name AS sub_competition FROM competitions s JOIN competitions p ON p.competition_id = s.parent_id ORDER BY parent;
-- A6 type distribution by category
SELECT k.category_name, c.type, COUNT(*) AS n FROM competitions c JOIN categories k ON k.category_id = c.category_id GROUP BY k.category_name, c.type ORDER BY k.category_name, n DESC;
-- A7 top-level competitions
SELECT competition_id, competition_name, type, gender FROM competitions WHERE parent_id IS NULL;

-- ===== B. COMPLEXES & VENUES =====
-- B1 venues with complex
SELECT v.venue_name, v.city_name, x.complex_name FROM venues v LEFT JOIN complexes x ON x.complex_id = v.complex_id;
-- B2 venues per complex
SELECT x.complex_name, COUNT(v.venue_id) AS venues FROM complexes x LEFT JOIN venues v ON v.complex_id = x.complex_id GROUP BY x.complex_id, x.complex_name ORDER BY venues DESC;
-- B3 venues in Chile
SELECT venue_name, city_name, timezone FROM venues WHERE country_name = 'Chile';
-- B4 venues and timezones
SELECT venue_name, timezone FROM venues ORDER BY timezone;
-- B5 complexes with more than one venue
SELECT x.complex_name, COUNT(v.venue_id) AS venues FROM complexes x JOIN venues v ON v.complex_id = x.complex_id GROUP BY x.complex_id, x.complex_name HAVING COUNT(v.venue_id) > 1 ORDER BY venues DESC;
-- B6 venues grouped by country
SELECT country_name, COUNT(*) AS venues, GROUP_CONCAT(venue_name SEPARATOR '; ') AS venue_list FROM venues GROUP BY country_name ORDER BY venues DESC;
-- B7 venues of complex 'Nacional'
SELECT v.venue_name, v.city_name, v.country_name FROM venues v JOIN complexes x ON x.complex_id = v.complex_id WHERE x.complex_name = 'Nacional';

-- ===== C. DOUBLES RANKINGS =====
-- C1 competitors with rank and points
SELECT c.name, r.`rank`, r.points FROM competitor_rankings r JOIN competitors c ON c.competitor_id = r.competitor_id ORDER BY r.`rank`;
-- C2 top 5
SELECT c.name, r.`rank`, r.points FROM competitor_rankings r JOIN competitors c ON c.competitor_id = r.competitor_id WHERE r.`rank` <= 5 ORDER BY r.`rank`;
-- C3 stable rank (movement = 0)
SELECT c.name, r.`rank` FROM competitor_rankings r JOIN competitors c ON c.competitor_id = r.competitor_id WHERE r.movement = 0 ORDER BY r.`rank`;
-- C4 total points for Croatia
SELECT c.country, SUM(r.points) AS total_points FROM competitor_rankings r JOIN competitors c ON c.competitor_id = r.competitor_id WHERE c.country = 'Croatia' GROUP BY c.country;
-- C5 competitors per country
SELECT country, COUNT(*) AS competitors FROM competitors GROUP BY country ORDER BY competitors DESC;
-- C6 highest points in the latest week
SELECT c.name, c.country, r.points FROM competitor_rankings r JOIN competitors c ON c.competitor_id = r.competitor_id
WHERE (r.year, r.week) = (SELECT year, week FROM competitor_rankings ORDER BY year DESC, week DESC LIMIT 1) ORDER BY r.points DESC LIMIT 10;
