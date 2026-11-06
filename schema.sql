-- MySQL 8 DDL (etl.py creates the same schema on SQLite/PostgreSQL via SQLAlchemy)
CREATE TABLE categories (category_id VARCHAR(50) PRIMARY KEY, category_name VARCHAR(100) NOT NULL);
CREATE TABLE competitions (
  competition_id VARCHAR(50) PRIMARY KEY, competition_name VARCHAR(100) NOT NULL, parent_id VARCHAR(50),
  type VARCHAR(20) NOT NULL, gender VARCHAR(10) NOT NULL, category_id VARCHAR(50),
  FOREIGN KEY (category_id) REFERENCES categories(category_id),
  INDEX ix_comp_category (category_id), INDEX ix_comp_parent (parent_id));
CREATE TABLE complexes (complex_id VARCHAR(50) PRIMARY KEY, complex_name VARCHAR(100) NOT NULL);
CREATE TABLE venues (
  venue_id VARCHAR(50) PRIMARY KEY, venue_name VARCHAR(100) NOT NULL, city_name VARCHAR(100) NOT NULL, country_name VARCHAR(100) NOT NULL,
  country_code CHAR(3) NOT NULL, timezone VARCHAR(100) NOT NULL, complex_id VARCHAR(50),
  FOREIGN KEY (complex_id) REFERENCES complexes(complex_id), INDEX ix_venue_country (country_name), INDEX ix_venue_complex (complex_id));
CREATE TABLE competitors (
  competitor_id VARCHAR(50) PRIMARY KEY, name VARCHAR(100) NOT NULL, country VARCHAR(100) NOT NULL,
  country_code CHAR(3) NOT NULL, abbreviation VARCHAR(10) NOT NULL, INDEX ix_competitor_country (country));
CREATE TABLE competitor_rankings (
  rank_id INT PRIMARY KEY AUTO_INCREMENT, `rank` INT NOT NULL, movement INT NOT NULL, points INT NOT NULL, competitions_played INT NOT NULL,
  competitor_id VARCHAR(50) NOT NULL, ranking_name VARCHAR(50), gender VARCHAR(10), year INT, week INT,
  FOREIGN KEY (competitor_id) REFERENCES competitors(competitor_id), INDEX ix_rank_competitor (competitor_id), INDEX ix_rank_period (year, week));
