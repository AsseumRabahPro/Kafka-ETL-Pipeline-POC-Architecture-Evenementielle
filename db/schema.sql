-- Table de faits pour les commandes
CREATE TABLE IF NOT EXISTS fact_orders (
    id SERIAL PRIMARY KEY,
    order_id INT UNIQUE NOT NULL,
    user_id INT NOT NULL,
    amount DECIMAL(10,2),
    items INT,
    status VARCHAR(20),
    rejection_reason TEXT,
    order_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

-- Index pour optimiser les requêtes analytiques
CREATE INDEX IF NOT EXISTS idx_fact_orders_status ON fact_orders(status);
CREATE INDEX IF NOT EXISTS idx_fact_orders_order_date ON fact_orders(order_date);
CREATE INDEX IF NOT EXISTS idx_fact_orders_user_id ON fact_orders(user_id);

-- Table de dimension pour les utilisateurs
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour les utilisateurs
CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Vues analytiques

-- Vue: Total commandes par jour
CREATE OR REPLACE VIEW v_orders_by_day AS
SELECT 
    order_date,
    COUNT(*) as total_orders,
    COUNT(CASE WHEN status = 'validated' THEN 1 END) as validated_count,
    COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_count,
    ROUND(100.0 * COUNT(CASE WHEN status = 'rejected' THEN 1 END) / COUNT(*), 2) as rejection_rate
FROM fact_orders
GROUP BY order_date
ORDER BY order_date DESC;

-- Vue: Montants par jour
CREATE OR REPLACE VIEW v_revenue_by_day AS
SELECT 
    order_date,
    COUNT(*) as total_orders,
    SUM(CASE WHEN status = 'validated' THEN amount ELSE 0 END) as validated_revenue,
    SUM(CASE WHEN status = 'rejected' THEN amount ELSE 0 END) as rejected_revenue,
    SUM(amount) as total_revenue,
    ROUND(AVG(CASE WHEN status = 'validated' THEN amount END), 2) as avg_validated_amount
FROM fact_orders
GROUP BY order_date
ORDER BY order_date DESC;

-- Vue: Statistiques globales
CREATE OR REPLACE VIEW v_orders_statistics AS
SELECT 
    COUNT(*) as total_orders,
    COUNT(CASE WHEN status = 'validated' THEN 1 END) as validated_count,
    COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_count,
    ROUND(100.0 * COUNT(CASE WHEN status = 'rejected' THEN 1 END) / COUNT(*), 2) as rejection_rate,
    SUM(amount) as total_revenue,
    ROUND(AVG(amount), 2) as avg_amount,
    MIN(amount) as min_amount,
    MAX(amount) as max_amount
FROM fact_orders
WHERE status = 'validated';
