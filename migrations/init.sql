CREATE TABLE countries (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  capital VARCHAR(255),
  region VARCHAR(255),
  population BIGINT NOT NULL,
  currency_code VARCHAR(10),
  exchange_rate DOUBLE,
  estimated_gdp DOUBLE,
  flag_url VARCHAR(512),
  last_refreshed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE (name)
);

CREATE TABLE refresh_status (
  id INT PRIMARY KEY DEFAULT 1,
  last_refreshed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  total_countries INT DEFAULT 0
);

-- Create indexes for better performance
CREATE INDEX idx_countries_region ON countries(region);
CREATE INDEX idx_countries_currency ON countries(currency_code);
CREATE INDEX idx_countries_gdp ON countries(estimated_gdp);
CREATE INDEX idx_countries_name ON countries(name);