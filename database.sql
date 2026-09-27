-- ==============================================================
-- FOOD NUTRITION ANALYZER DATABASE SCHEMA
-- Database: food_nutrition_db
-- ==============================================================

CREATE DATABASE IF NOT EXISTS `food_nutrition_db` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `food_nutrition_db`;

-- --------------------------------------------------------------
-- Table: users
-- Stores registered users and their physical profile metrics
-- --------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL,
    `email` VARCHAR(150) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `age` INT NOT NULL,
    `gender` ENUM('Male', 'Female', 'Other') NOT NULL DEFAULT 'Male',
    `height_cm` FLOAT NOT NULL,
    `weight_kg` FLOAT NOT NULL,
    `activity_level` ENUM('Sedentary', 'Lightly Active', 'Moderately Active', 'Very Active', 'Extra Active') NOT NULL DEFAULT 'Moderately Active',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- --------------------------------------------------------------
-- Table: admins
-- Stores administrative accounts for system and food management
-- --------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `admins` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(50) NOT NULL UNIQUE,
    `email` VARCHAR(150) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `full_name` VARCHAR(100) NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- --------------------------------------------------------------
-- Table: food_items
-- Food repository containing baseline nutrition facts per 100 grams
-- --------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `food_items` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(150) NOT NULL,
    `category` ENUM('Fruits', 'Vegetables', 'Grains', 'Pulses', 'Dairy', 'Eggs', 'Meat', 'Snacks', 'Beverages') NOT NULL,
    `serving_size` VARCHAR(100) NOT NULL DEFAULT '100g',
    `calories_per_100g` FLOAT NOT NULL,
    `protein_per_100g` FLOAT NOT NULL,
    `carbs_per_100g` FLOAT NOT NULL,
    `fat_per_100g` FLOAT NOT NULL,
    `fiber_per_100g` FLOAT NOT NULL DEFAULT 0.0,
    `micronutrients` VARCHAR(255) DEFAULT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- --------------------------------------------------------------
-- Table: meal_entries
-- Tracks user-consumed meals with dynamic gram calculations
-- --------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `meal_entries` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `food_id` INT NOT NULL,
    `meal_type` ENUM('Breakfast', 'Lunch', 'Dinner', 'Snacks') NOT NULL,
    `quantity_grams` FLOAT NOT NULL,
    `calories` FLOAT NOT NULL,
    `protein` FLOAT NOT NULL,
    `carbs` FLOAT NOT NULL,
    `fat` FLOAT NOT NULL,
    `fiber` FLOAT NOT NULL,
    `entry_date` DATE NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_meal_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_meal_food` FOREIGN KEY (`food_id`) REFERENCES `food_items` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ==============================================================
-- SEED DATA
-- ==============================================================

-- 1. Insert Default Admin (Password: Rakshitha@456)
INSERT IGNORE INTO `admins` (`username`, `email`, `password_hash`, `full_name`) VALUES
('admin', 'admin@nutrition.com', 'scrypt:32768:8:1$JzAPPegaXTq17Jzx$4a2684a02788638ddd8b03bad59d6358e7d43f819a8f96bb20d2bb366c0e1bceda46580cb3502f9f278a0129e2c6406b2572c946bb62643e4ca390fd5d8e47db', 'System Administrator');

-- 2. Insert Demo User (Password: User@123)
-- Age 22, Male, 175 cm, 70 kg, Moderately Active -> BMI = 22.86 (Normal weight)
INSERT IGNORE INTO `users` (`id`, `name`, `email`, `password_hash`, `age`, `gender`, `height_cm`, `weight_kg`, `activity_level`) VALUES
(1, 'John Doe', 'john@example.com', 'scrypt:32768:8:1$4rmMbrQglfcWpdSn$dc7741c6e9a57d91b245381e509d58d60652cfc379892ab13d24d1b8d314936dba7acc358663d2e55c85514d545cfc0760920459489876ce76203fb715282ee6', 22, 'Male', 175.0, 70.0, 'Moderately Active');

-- 3. Insert Comprehensive Food Items (Per 100g standard measurements)
INSERT IGNORE INTO `food_items` (`id`, `name`, `category`, `serving_size`, `calories_per_100g`, `protein_per_100g`, `carbs_per_100g`, `fat_per_100g`, `fiber_per_100g`, `micronutrients`) VALUES
(1, 'Apple (Raw)', 'Fruits', '1 medium (182g)', 52.0, 0.3, 14.0, 0.2, 2.4, 'Vitamin C, Potassium'),
(2, 'Banana', 'Fruits', '1 medium (118g)', 89.0, 1.1, 22.8, 0.3, 2.6, 'Potassium, Vitamin B6, Magnesium'),
(3, 'Orange', 'Fruits', '1 medium (131g)', 47.0, 0.9, 11.8, 0.1, 2.4, 'Vitamin C, Folate, Thiamine'),
(4, 'Mango', 'Fruits', '1 cup sliced (165g)', 60.0, 0.8, 15.0, 0.4, 1.6, 'Vitamin A, Vitamin C, Folate'),
(5, 'Strawberries', 'Fruits', '1 cup halves (152g)', 32.0, 0.7, 7.7, 0.3, 2.0, 'Vitamin C, Manganese, Antioxidants'),
(6, 'Watermelon', 'Fruits', '1 wedge (286g)', 30.0, 0.6, 7.6, 0.2, 0.4, 'Vitamin A, Lycopene, Citrulline'),
(7, 'Papaya', 'Fruits', '1 cup pieces (145g)', 43.0, 0.5, 10.8, 0.3, 1.7, 'Vitamin C, Folate, Papain Enzyme'),
(8, 'Spinach (Raw)', 'Vegetables', '1 cup (30g)', 23.0, 2.9, 3.6, 0.4, 2.2, 'Iron, Vitamin K, Calcium, Folate'),
(9, 'Broccoli (Steamed)', 'Vegetables', '1 cup chopped (91g)', 34.0, 2.8, 6.6, 0.4, 2.6, 'Vitamin C, Vitamin K, Chromium'),
(10, 'Carrot (Raw)', 'Vegetables', '1 medium (61g)', 41.0, 0.9, 9.6, 0.2, 2.8, 'Beta-Carotene, Vitamin A, Biotin'),
(11, 'Tomato (Fresh)', 'Vegetables', '1 medium (123g)', 18.0, 0.9, 3.9, 0.2, 1.2, 'Lycopene, Potassium, Vitamin C'),
(12, 'Boiled Potato', 'Vegetables', '1 medium (173g)', 87.0, 1.9, 20.1, 0.1, 1.8, 'Potassium, Vitamin C, Vitamin B6'),
(13, 'Cucumber (with peel)', 'Vegetables', '1 cup sliced (119g)', 15.0, 0.7, 3.6, 0.1, 0.5, 'Vitamin K, Silica, Potassium'),
(14, 'Cauliflower (Cooked)', 'Vegetables', '1 cup pieces (100g)', 25.0, 1.9, 5.0, 0.3, 2.0, 'Choline, Vitamin C, Sulforaphane'),
(15, 'Cooked White Rice', 'Grains', '1 cup (158g)', 130.0, 2.7, 28.2, 0.3, 0.4, 'Selenium, Niacin, Manganese'),
(16, 'Cooked Brown Rice', 'Grains', '1 cup (195g)', 111.0, 2.6, 23.0, 0.9, 1.8, 'Magnesium, Phosphorus, Fiber'),
(17, 'Rolled Oats (Dry)', 'Grains', '1/2 cup (40g)', 389.0, 16.9, 66.3, 6.9, 10.6, 'Beta-glucan, Iron, Zinc, Phosphorus'),
(18, 'Whole Wheat Bread', 'Grains', '1 slice (40g)', 247.0, 13.0, 41.3, 3.4, 7.0, 'B Vitamins, Iron, Dietary Fiber'),
(19, 'Chapati (Whole Wheat Roti)', 'Grains', '1 roti (40g)', 297.0, 9.3, 58.0, 3.8, 9.8, 'Complex Carbs, B-Complex, Fiber'),
(20, 'Cooked Quinoa', 'Grains', '1 cup (185g)', 120.0, 4.4, 21.3, 1.9, 2.8, 'Complete Protein, Folate, Iron'),
(21, 'Cooked Yellow Dal (Moong/Toor)', 'Pulses', '1 cup (200g)', 116.0, 9.0, 20.1, 0.4, 7.9, 'Folate, Iron, Potassium'),
(22, 'Cooked Chickpeas (Chole)', 'Pulses', '1 cup (164g)', 164.0, 8.9, 27.4, 2.6, 7.6, 'Folate, Manganese, Copper'),
(23, 'Cooked Kidney Beans (Rajma)', 'Pulses', '1 cup (177g)', 127.0, 8.7, 22.8, 0.5, 6.4, 'Iron, Potassium, Dietary Fiber'),
(24, 'Cooked Black Beans', 'Pulses', '1 cup (172g)', 132.0, 8.9, 23.7, 0.5, 8.7, 'Antioxidants, Magnesium, Protein'),
(25, 'Soybeans (Boiled)', 'Pulses', '1 cup (172g)', 173.0, 16.6, 9.9, 9.0, 6.0, 'Isoflavones, Calcium, Complete Protein'),
(26, 'Whole Cow Milk', 'Dairy', '1 cup (244ml)', 61.0, 3.2, 4.8, 3.3, 0.0, 'Calcium, Vitamin D, Vitamin B12'),
(27, 'Skimmed Milk', 'Dairy', '1 cup (245ml)', 34.0, 3.4, 5.0, 0.1, 0.0, 'Calcium, Protein, Riboflavin'),
(28, 'Plain Greek Yogurt', 'Dairy', '1 cup (170g)', 59.0, 10.0, 3.6, 0.4, 0.0, 'Probiotics, Calcium, Zinc'),
(29, 'Paneer (Indian Cottage Cheese)', 'Dairy', '100g cube', 265.0, 18.3, 1.2, 20.8, 0.0, 'Calcium, Phosphorus, Casein'),
(30, 'Cheddar Cheese', 'Dairy', '1 slice (28g)', 403.0, 24.9, 1.3, 33.1, 0.0, 'Calcium, Vitamin A, Zinc'),
(31, 'Whole Boiled Egg', 'Eggs', '1 large egg (50g)', 155.0, 12.6, 1.1, 10.6, 0.0, 'Choline, Vitamin B12, Selenium'),
(32, 'Egg White (Boiled)', 'Eggs', '1 large white (33g)', 52.0, 10.9, 0.7, 0.2, 0.0, 'Pure Albumin, Potassium, Sodium'),
(33, 'Scrambled Eggs (1 egg)', 'Eggs', '1 egg serving (60g)', 149.0, 10.0, 1.6, 11.0, 0.0, 'Vitamin A, Riboflavin, Lutein'),
(34, 'Chicken Breast (Grilled/Skinless)', 'Meat', '1 breast piece (150g)', 165.0, 31.0, 0.0, 3.6, 0.0, 'Niacin, Phosphorus, Vitamin B6'),
(35, 'Salmon Fillet (Baked)', 'Meat', '1 fillet (150g)', 208.0, 22.0, 0.0, 13.0, 0.0, 'Omega-3 EPA/DHA, Vitamin D, B12'),
(36, 'Canned Tuna in Water', 'Meat', '1 can drained (165g)', 116.0, 25.5, 0.0, 0.8, 0.0, 'Selenium, Niacin, Lean Protein'),
(37, 'Lean Minced Beef (90%)', 'Meat', '100g patty', 215.0, 26.0, 0.0, 12.0, 0.0, 'Heme Iron, Zinc, Vitamin B12'),
(38, 'Raw Almonds', 'Snacks', '1 handful (28g)', 579.0, 21.2, 21.6, 49.9, 12.5, 'Vitamin E, Magnesium, Riboflavin'),
(39, 'Walnuts', 'Snacks', '1 handful (28g)', 654.0, 15.2, 13.7, 65.2, 6.7, 'Alpha-Linolenic Acid (Omega-3)'),
(40, 'Dark Chocolate (70% Cocoa)', 'Snacks', '1 square (20g)', 598.0, 7.8, 45.9, 42.6, 10.9, 'Flavonoids, Copper, Iron'),
(41, 'Air-Popped Popcorn', 'Snacks', '1 cup (8g)', 387.0, 12.9, 77.8, 4.5, 14.5, 'Whole Grain Polyphenols, Fiber'),
(42, 'Peanut Butter (Smooth)', 'Snacks', '2 tbsp (32g)', 588.0, 25.1, 20.0, 50.4, 6.0, 'Niacin, Magnesium, Vitamin E'),
(43, 'Green Tea (Brewed/Unsweetened)', 'Beverages', '1 cup (240ml)', 1.0, 0.2, 0.0, 0.0, 0.0, 'EGCG Catechins, Flavonoids'),
(44, 'Black Coffee (Unsweetened)', 'Beverages', '1 cup (240ml)', 2.0, 0.3, 0.0, 0.0, 0.0, 'Chlorogenic Acid, Potassium'),
(45, 'Fresh Orange Juice', 'Beverages', '1 glass (200ml)', 45.0, 0.7, 10.4, 0.2, 0.2, 'Vitamin C, Potassium, Folate'),
(46, 'Unsweetened Soy Milk', 'Beverages', '1 cup (240ml)', 33.0, 2.8, 1.8, 1.6, 0.4, 'Isoflavones, Calcium, Vitamin D'),
(47, 'Coconut Water', 'Beverages', '1 glass (240ml)', 19.0, 0.7, 3.7, 0.2, 1.1, 'Electrolytes, Potassium, Magnesium');

-- 4. Insert Sample Meal Entries for Demo User
INSERT IGNORE INTO `meal_entries` (`id`, `user_id`, `food_id`, `meal_type`, `quantity_grams`, `calories`, `protein`, `carbs`, `fat`, `fiber`, `entry_date`) VALUES
(1, 1, 17, 'Breakfast', 60.0, 233.4, 10.1, 39.8, 4.1, 6.4, CURDATE()),
(2, 1, 26, 'Breakfast', 200.0, 122.0, 6.4, 9.6, 6.6, 0.0, CURDATE()),
(3, 1, 2, 'Breakfast', 100.0, 89.0, 1.1, 22.8, 0.3, 2.6, CURDATE()),
(4, 1, 19, 'Lunch', 80.0, 237.6, 7.4, 46.4, 3.0, 7.8, CURDATE()),
(5, 1, 21, 'Lunch', 150.0, 174.0, 13.5, 30.2, 0.6, 11.9, CURDATE()),
(6, 1, 34, 'Lunch', 120.0, 198.0, 37.2, 0.0, 4.3, 0.0, CURDATE()),
(7, 1, 39, 'Snacks', 30.0, 173.7, 6.4, 6.5, 15.0, 3.8, CURDATE()),
(8, 1, 44, 'Snacks', 250.0, 2.5, 0.5, 0.0, 0.0, 0.0, CURDATE()),
(9, 1, 16, 'Dinner', 150.0, 166.5, 3.9, 34.5, 1.4, 2.7, CURDATE()),
(10, 1, 29, 'Dinner', 100.0, 265.0, 18.3, 1.2, 20.8, 0.0, CURDATE()),
(11, 1, 8, 'Dinner', 100.0, 23.0, 2.9, 3.6, 0.4, 2.2, CURDATE());
