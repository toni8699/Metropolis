-- Include your INSERT SQL statements in this file.
-- Make sure to terminate each statement with a semicolon (;)

-- LEAVE this statement on. It is required to connect to your database.
CONNECT TO COMP421;

-- Remember to put the INSERT statements for the tables with foreign key references
--    ONLY AFTER the insert for the parent tables!

-- This is only an example of how you add INSERT statements to this file.
-- Areas
INSERT INTO Area (areaID, areaName) VALUES
  (1, 'Montreal Metro'),
  (2, 'Toronto Downtown'),
  (3, 'Vancouver Downtown'),
  (4, 'Calgary Downtown'),
  (5, 'Ottawa Capital Region'),
  (6, 'Quebec City');

-- Vehicle classes
INSERT INTO VehicleClass (classID, className, securityDeposit) VALUES
  (10, 'Economy', 100.00),
  (11, 'Compact', 150.00),
  (12, 'SUV', 250.00),
  (13, 'Truck', 300.00),
  (14, 'Luxury', 500.00);

-- Branches (managerID left NULL for now so employees can insert)
INSERT INTO Branch (branchID, address, phone_number, city, areaID, managerID) VALUES
  (100, '123 Main St', '514-123-4000', 'Montreal', 1, NULL),
  (101, '200 King St', '416-555-0101', 'Toronto', 2, NULL),
  (102, '500 Granville Rd', '604-555-0202', 'Vancouver', 3, NULL),
  (103, '1500 Bow Valley Tr', '403-555-0303', 'Calgary', 4, NULL),
  (104, '77 Rideau St', '613-555-0404', 'Ottawa', 5, NULL);

-- Employees (some supervisors reference another employee)
INSERT INTO Employee (eID, name, salary, branchID, supervisorID) VALUES
  (200, 'Ava Leblanc', 60000, 100, NULL),
  (201, 'Liam Chen', 58000, 100, 200),
  (202, 'Noah Patel', 62000, 101, NULL),
  (203, 'Emma Davis', 54000, 101, 202),
  (204, 'Maya Singh', 61000, 102, NULL),
  (205, 'Elijah Harris', 52000, 102, 204),
  (206, 'Sophia Liu', 63000, 103, NULL),
  (207, 'Lucas Brown', 53000, 103, 206),
  (208, 'Chloe Wilson', 61500, 104, NULL),
  (209, 'Daniel White', 51500, 104, 208);

-- Branch managers (one per branch)
INSERT INTO BranchManager (eID, branchID) VALUES
  (200, 100),
  (202, 101),
  (204, 102),
  (206, 103),
  (208, 104);

-- Update branches so managerID matches the employee
UPDATE Branch SET managerID = 200 WHERE branchID = 100;
UPDATE Branch SET managerID = 202 WHERE branchID = 101;
UPDATE Branch SET managerID = 204 WHERE branchID = 102;
UPDATE Branch SET managerID = 206 WHERE branchID = 103;
UPDATE Branch SET managerID = 208 WHERE branchID = 104;

-- Customers
INSERT INTO Customer (email, name, address, license_expiry) VALUES
  ('mike@example.com', 'Mike McCarthy', '10 Queen St, Montreal', '2027-07-01'),
  ('sara@example.com', 'Sara Goldman', '45 King St, Toronto', '2026-11-14'),
  ('nina@example.com', 'Nina Carter', '120 Granville, Vancouver', '2028-01-30'),
  ('ethan@example.com', 'Ethan Ross', '62 3rd Ave, Calgary', '2026-06-05'),
  ('lisa@example.com', 'Lisa Adjani', '420 Rideau, Ottawa', '2027-03-18');

-- Reservations
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES
  (1000, '2026-03-01 09:15:00', 'mike@example.com'),
  (1001, '2026-03-02 14:40:00', 'sara@example.com'),
  (1002, '2026-03-03 18:00:00', 'nina@example.com'),
  (1003, '2026-03-04 08:30:00', 'ethan@example.com'),
  (1004, '2026-03-04 19:20:00', 'lisa@example.com'),
  (1005, '2026-03-05 07:50:00', 'mike@example.com');

-- Rental periods
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES
  (1000, 1, '2026-03-10', '2026-03-14'),
  (1001, 1, '2026-03-05', '2026-03-09'),
  (1002, 1, '2026-03-12', '2026-03-17'),
  (1003, 1, '2026-03-15', '2026-03-18'),
  (1004, 1, '2026-03-20', '2026-03-25'),
  (1005, 1, '2026-03-22', '2026-03-23');

-- Vehicles
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES
  ('1HGBH41JXMN109186', 'ABC123', 12000, 'Civic', 'Available', 'Honda', 11, 100),
  ('2FTRX18W1XCA01234', 'TOR456', 50000, 'F-150', 'Rented', 'Ford', 13, 101),
  ('JH4KA8260MC000000', 'VAN789', 32000, 'Accord', 'Available', 'Honda', 11, 102),
  ('1N4AL11D75C109151', 'CAL321', 45000, 'Altima', 'Available', 'Nissan', 12, 103),
  ('5N1AT2MV6EC806375', 'OTT654', 22000, 'Rogue', 'Available', 'Nissan', 12, 104),
  ('1FTFW1ET4EFA01234', 'MTL987', 8000, 'F-250', 'Available', 'Ford', 13, 100);

-- Agreements
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES
  (3000, 'Daily', 340.00, 200, '1HGBH41JXMN109186', 1000),
  (3001, 'Weekly', 1800.00, 202, '2FTRX18W1XCA01234', 1001),
  (3002, 'Daily', 420.00, 204, 'JH4KA8260MC000000', 1002),
  (3003, 'Monthly', 3200.00, 206, '1N4AL11D75C109151', 1003),
  (3004, 'Weekly', 2100.00, 208, '5N1AT2MV6EC806375', 1004),
  (3005, 'Daily', 360.00, 200, '1FTFW1ET4EFA01234', 1005);

-- Relocations
INSERT INTO Relocation (sourceAreaID, targetAreaID, fee) VALUES
  (1, 2, 520.00),
  (2, 3, 700.00),
  (3, 4, 450.00),
  (4, 5, 480.00),
  (5, 1, 610.00);