-- Insert data into users table
INSERT INTO "users" ("email", "hashed_password", "is_active", "created_at", "updated_at") VALUES
('john.doe@example.com', 'hashed_password_1', TRUE, NOW(), NOW()),
('jane.smith@example.com', 'hashed_password_2', TRUE, NOW(), NOW()),
('alice.johnson@example.com', 'hashed_password_3', TRUE, NOW(), NOW());

-- Insert data into companies table and store the results
WITH inserted_companies AS (
    INSERT INTO "companies" ("name", "address", "admin_user_id", "created_at", "updated_at") VALUES
    ('OilCorp', '123 Main St', 1, NOW(), NOW()),
    ('EnergyPlus', '456 Elm St', 2, NOW(), NOW()),
    ('PetroTech', '789 Oak St', 1, NOW(), NOW()),
    ('GreenEnergy', '101 Pine St', 3, NOW(), NOW())
    RETURNING id, name
),
-- Insert data into equipment table and store the results
inserted_equipment AS (
    INSERT INTO "equipment" ("company_id", "equipment_id", "name", "created_at", "updated_at")
    SELECT 
        c.id,
        e.equipment_id,
        e.name,
        NOW(),
        NOW()
    FROM (
        VALUES
        ('OilCorp', 'EQ-12495', 'Compressor A'),
        ('OilCorp', 'EQ-12496', 'Compressor B'),
        ('EnergyPlus', 'EQ-12497', 'Turbine A'),
        ('EnergyPlus', 'EQ-12498', 'Turbine B'),
        ('PetroTech', 'EQ-12499', 'Pump A'),
        ('PetroTech', 'EQ-12500', 'Pump B'),
        ('GreenEnergy', 'EQ-12501', 'Generator A'),
        ('GreenEnergy', 'EQ-12502', 'Generator B')
    ) AS e(company_name, equipment_id, name)
    JOIN inserted_companies c ON c.name = e.company_name
    RETURNING id, equipment_id
)
-- Insert data into sensor_data table using the inserted equipment IDs
INSERT INTO "sensor_data" ("equipment_id", "timestamp", "value")
SELECT id, timestamp::timestamp with time zone, value
FROM (
    VALUES
    ('EQ-12495', '2023-02-12T01:30:00.000-05:00', 78.8),
    ('EQ-12496', '2023-01-12T01:30:00.000-05:00', 8.8),
    ('EQ-12497', '2023-03-15T14:00:00.000-05:00', 65.3),
    ('EQ-12498', '2023-04-10T10:20:00.000-05:00', 42.1),
    ('EQ-12499', '2023-05-20T18:00:00.000-05:00', 95.4),
    ('EQ-12500', '2023-06-25T16:15:00.000-05:00', 34.7),
    ('EQ-12501', '2023-07-30T08:45:00.000-05:00', 81.9),
    ('EQ-12502', '2023-08-01T12:30:00.000-05:00', 56.2),
    ('EQ-12495', '2023-09-15T14:00:00.000-05:00', 90.4),
    ('EQ-12496', '2023-10-10T10:20:00.000-05:00', 15.3),
    ('EQ-12497', '2023-11-20T18:00:00.000-05:00', 85.7),
    ('EQ-12498', '2023-12-25T16:15:00.000-05:00', 50.1),
    ('EQ-12499', '2024-01-30T08:45:00.000-05:00', 67.3),
    ('EQ-12500', '2024-02-01T12:30:00.000-05:00', 23.5),
    ('EQ-12501', '2024-03-15T14:00:00.000-05:00', 72.4),
    ('EQ-12502', '2024-04-10T10:20:00.000-05:00', 36.9),
    ('EQ-12495', '2024-05-20T18:00:00.000-05:00', 88.2),
    ('EQ-12496', '2024-06-25T16:15:00.000-05:00', 19.4),
    ('EQ-12497', '2024-07-30T08:45:00.000-05:00', 54.6),
    ('EQ-12498', '2024-08-01T12:30:00.000-05:00', 61.7)
) AS sensor_data(equipment_id, timestamp, value)
JOIN inserted_equipment ON inserted_equipment.equipment_id = sensor_data.equipment_id;
