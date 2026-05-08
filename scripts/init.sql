-- IIV Bot Database Initialization
-- Bu fayl faqat birinchi marta ishga tushganda bajariladi

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Full-text search uchun
CREATE EXTENSION IF NOT EXISTS "unaccent";
