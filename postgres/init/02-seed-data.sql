-- Seed data for e-commerce

-- Insert customers
INSERT INTO customers (first_name, last_name, email, phone, state, city) VALUES
('João', 'Silva', 'joao.silva@email.com', '11999999999', 'SP', 'São Paulo'),
('Maria', 'Santos', 'maria.santos@email.com', '21988888888', 'RJ', 'Rio de Janeiro'),
('Pedro', 'Oliveira', 'pedro.oliveira@email.com', '31977777777', 'MG', 'Belo Horizonte'),
('Ana', 'Costa', 'ana.costa@email.com', '41966666666', 'PR', 'Curitiba'),
('Carlos', 'Ferreira', 'carlos.ferreira@email.com', '51955555555', 'RS', 'Porto Alegre'),
('Juliana', 'Lima', 'juliana.lima@email.com', '61944444444', 'DF', 'Brasília'),
('Fernando', 'Alves', 'fernando.alves@email.com', '71933333333', 'BA', 'Salvador'),
('Patricia', 'Rocha', 'patricia.rocha@email.com', '81922222222', 'PE', 'Recife'),
('Roberto', 'Souza', 'roberto.souza@email.com', '85911111111', 'CE', 'Fortaleza'),
('Camila', 'Martins', 'camila.martins@email.com', '11988887777', 'SP', 'Campinas');

-- Insert products
INSERT INTO products (product_name, category, price, cost) VALUES
('Notebook Dell Inspiron', 'Eletrônicos', 3500.00, 2800.00),
('Mouse Logitech MX Master', 'Periféricos', 450.00, 300.00),
('Teclado Mecânico Keychron', 'Periféricos', 650.00, 450.00),
('Monitor LG 27"', 'Eletrônicos', 1200.00, 900.00),
('Webcam Logitech C920', 'Periféricos', 550.00, 380.00),
('Headset HyperX Cloud', 'Periféricos', 380.00, 250.00),
('SSD Samsung 1TB', 'Armazenamento', 480.00, 350.00),
('Memória RAM 16GB', 'Componentes', 320.00, 220.00),
('Cadeira Gamer', 'Mobiliário', 1100.00, 750.00),
('Mesa para Computador', 'Mobiliário', 450.00, 300.00),
('Mousepad Grande', 'Acessórios', 85.00, 45.00),
('Hub USB-C', 'Acessórios', 180.00, 120.00),
('Cabo HDMI 2m', 'Acessórios', 45.00, 25.00),
('Suporte para Notebook', 'Acessórios', 95.00, 55.00),
('Luminária LED', 'Iluminação', 120.00, 75.00);

-- Insert orders and items
DO $$
DECLARE
    v_order_id INTEGER;
    v_customer_id INTEGER;
    v_product_id INTEGER;
    v_quantity INTEGER;
    v_unit_price DECIMAL(10,2);
    v_order_total DECIMAL(10,2);
BEGIN
    FOR i IN 1..100 LOOP
        v_customer_id := (RANDOM() * 9 + 1)::INTEGER;
        v_order_total := 0;
        
        INSERT INTO orders (customer_id, order_date, status, total_amount)
        VALUES (
            v_customer_id,
            CURRENT_TIMESTAMP - (RANDOM() * INTERVAL '365 days'),
            CASE (RANDOM() * 4)::INTEGER
                WHEN 0 THEN 'pending'
                WHEN 1 THEN 'processing'
                WHEN 2 THEN 'shipped'
                ELSE 'delivered'
            END,
            0
        )
        RETURNING order_id INTO v_order_id;
        
        FOR j IN 1..(RANDOM() * 4 + 1)::INTEGER LOOP
            v_product_id := (RANDOM() * 14 + 1)::INTEGER;
            v_quantity := (RANDOM() * 3 + 1)::INTEGER;
            
            SELECT price INTO v_unit_price FROM products WHERE product_id = v_product_id;
            
            INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
            VALUES (
                v_order_id,
                v_product_id,
                v_quantity,
                v_unit_price,
                v_quantity * v_unit_price
            );
            
            v_order_total := v_order_total + (v_quantity * v_unit_price);
        END LOOP;
        
        UPDATE orders SET total_amount = v_order_total WHERE order_id = v_order_id;
    END LOOP;
END $$;
