

--    ONLY AFTER the insert for the parent tables!

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

-- Legacy Customer / Reservation / RentalPeriod / Agreement seeds removed (migration 010).
-- Vehicles
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000001XXX', 'PL958B', 82360, 'Camry', 'Relocating', 'Hyundai', 14, 104);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000002XXX', 'PL958A', 21081, 'CR-V', 'Rented', 'Nissan', 12, 100);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000003XXX', 'PL100A', 18046, 'Camry', 'Rented', 'Chevrolet', 11, 103);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000004XXX', 'PL803C', 20406, 'Civic', 'Rented', 'Ford', 10, 104);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000005XXX', 'PL488C', 52137, 'Accord', 'Available', 'Toyota', 10, 101);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000006XXX', 'PL870B', 27449, 'Escape', 'Relocating', 'Toyota', 11, 100);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000007XXX', 'PL130A', 19208, 'Camry', 'Available', 'Mazda', 12, 104);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000008XXX', 'PL478C', 65598, 'Corolla', 'Maintenance', 'Honda', 14, 103);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000009XXX', 'PL990A', 79483, 'CX-5', 'Maintenance', 'Ford', 10, 103);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000010XXX', 'PL785C', 7814, 'Rogue', 'Relocating', 'Toyota', 10, 103);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000011XXX', 'PL226A', 10978, 'Camry', 'Relocating', 'Chevrolet', 10, 104);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000012XXX', 'PL430B', 58104, 'Accord', 'Relocating', 'Mazda', 14, 103);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000013XXX', 'PL541C', 27544, 'Accord', 'Available', 'Ford', 11, 104);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000014XXX', 'PL674A', 37017, 'F-150', 'Relocating', 'Chevrolet', 11, 100);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000015XXX', 'PL490B', 57450, 'Rogue', 'Available', 'Mazda', 11, 101);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000016XXX', 'PL211A', 18042, 'Accord', 'Available', 'Kia', 12, 100);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000017XXX', 'PL633A', 56646, 'CR-V', 'Rented', 'Toyota', 14, 100);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000018XXX', 'PL804C', 52146, 'Corolla', 'Rented', 'Mazda', 12, 100);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000019XXX', 'PL212A', 73400, 'Sierra', 'Maintenance', 'Mazda', 11, 103);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000020XXX', 'PL652A', 47643, 'F-150', 'Available', 'Hyundai', 11, 102);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000021XXX', 'PL763A', 54117, 'CR-V', 'Relocating', 'Kia', 12, 103);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000022XXX', 'PL505B', 68910, 'Civic', 'Available', 'Kia', 14, 101);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000023XXX', 'PL475B', 73470, 'Sierra', 'Relocating', 'Honda', 12, 101);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000024XXX', 'PL906A', 73045, 'Corolla', 'Relocating', 'Honda', 12, 101);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000025XXX', 'PL209B', 8552, 'Escape', 'Maintenance', 'Kia', 11, 102);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000026XXX', 'PL363A', 65148, 'Camry', 'Available', 'Kia', 14, 103);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000027XXX', 'PL323A', 6841, 'Civic', 'Rented', 'Ford', 13, 101);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000028XXX', 'PL348C', 32049, 'Civic', 'Rented', 'Nissan', 10, 104);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000029XXX', 'PL239C', 53362, 'CX-5', 'Available', 'Kia', 13, 102);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000030XXX', 'PL746A', 21428, 'Civic', 'Maintenance', 'Ford', 12, 102);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000031XXX', 'PL702A', 85220, 'Rogue', 'Relocating', 'Honda', 11, 104);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000032XXX', 'PL222C', 57595, 'Sierra', 'Available', 'Hyundai', 12, 103);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000033XXX', 'PL740C', 24799, 'Civic', 'Maintenance', 'Nissan', 11, 101);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000034XXX', 'PL514A', 79051, 'Accord', 'Maintenance', 'Chevrolet', 10, 102);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000035XXX', 'PL187B', 16106, 'CR-V', 'Maintenance', 'Toyota', 10, 103);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000036XXX', 'PL436A', 17604, 'Civic', 'Available', 'Ford', 14, 100);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000037XXX', 'PL838C', 57433, 'CR-V', 'Rented', 'Chevrolet', 10, 103);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000038XXX', 'PL923B', 75416, 'CR-V', 'Available', 'Honda', 12, 101);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000039XXX', 'PL355C', 17585, 'CX-5', 'Relocating', 'Toyota', 14, 103);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000040XXX', 'PL511B', 15163, 'Accord', 'Available', 'Honda', 10, 102);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000041XXX', 'PL867A', 80704, 'Corolla', 'Maintenance', 'Toyota', 11, 103);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000042XXX', 'PL950C', 74058, 'CX-5', 'Maintenance', 'Hyundai', 10, 100);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000043XXX', 'PL345C', 60567, 'CX-5', 'Relocating', 'Hyundai', 10, 100);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000044XXX', 'PL671C', 46957, 'Accord', 'Maintenance', 'Honda', 11, 100);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000045XXX', 'PL715B', 68528, 'Corolla', 'Rented', 'Toyota', 11, 103);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000046XXX', 'PL264C', 46659, 'Corolla', 'Maintenance', 'Toyota', 14, 104);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000047XXX', 'PL776C', 25990, 'Accord', 'Maintenance', 'Mazda', 10, 102);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000048XXX', 'PL491C', 58241, 'CR-V', 'Maintenance', 'Ford', 12, 102);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000049XXX', 'PL348B', 53000, 'Accord', 'Rented', 'Honda', 13, 102);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000050XXX', 'PL728A', 66191, 'Corolla', 'Relocating', 'Hyundai', 14, 103);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000051XXX', 'PL431C', 43354, 'Escape', 'Relocating', 'Kia', 14, 102);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000052XXX', 'PL220A', 60958, 'Accord', 'Maintenance', 'Hyundai', 11, 102);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000053XXX', 'PL806A', 10521, 'Accord', 'Relocating', 'Chevrolet', 13, 102);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000054XXX', 'PL119B', 43431, 'F-150', 'Rented', 'Nissan', 13, 102);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000055XXX', 'PL710C', 12139, 'Sierra', 'Maintenance', 'Honda', 10, 100);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000056XXX', 'PL383B', 28227, 'CX-5', 'Maintenance', 'Kia', 14, 104);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000057XXX', 'PL635A', 63249, 'Accord', 'Maintenance', 'Kia', 12, 101);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000058XXX', 'PL944A', 71774, 'Sierra', 'Available', 'Toyota', 11, 101);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000059XXX', 'PL268C', 34063, 'Civic', 'Relocating', 'Honda', 13, 103);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000060XXX', 'PL864C', 64520, 'Camry', 'Available', 'Toyota', 13, 101);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000061XXX', 'PL901A', 21000, 'Civic', 'Available', 'Honda', 10, 100);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000062XXX', 'PL902B', 15000, 'Corolla', 'Available', 'Toyota', 11, 100);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000063XXX', 'PL903C', 18000, 'Rogue', 'Maintenance', 'Nissan', 12, 100);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000064XXX', 'PL904A', 12500, 'CX-5', 'Available', 'Mazda', 12, 100);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000065XXX', 'PL905B', 9100, 'Camry', 'Available', 'Hyundai', 14, 100);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000066XXX', 'PL906C', 23000, 'Civic', 'Maintenance', 'Honda', 10, 100);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000067XXX', 'PL907A', 45000, 'Corolla', 'Available', 'Kia', 11, 101);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000068XXX', 'PL908B', 32000, 'Escape', 'Available', 'Ford', 11, 101);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000069XXX', 'PL909C', 41000, 'Camry', 'Available', 'Toyota', 14, 101);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000070XXX', 'PL910A', 38000, 'Civic', 'Available', 'Honda', 10, 101);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000071XXX', 'PL911B', 29000, 'CR-V', 'Maintenance', 'Subaru', 12, 101);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000072XXX', 'PL912C', 27000, 'CX-5', 'Available', 'Mazda', 12, 102);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000073XXX', 'PL913A', 23000, 'Altima', 'Available', 'Nissan', 11, 102);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000074XXX', 'PL914B', 19500, 'Rogue', 'Maintenance', 'Nissan', 13, 102);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000075XXX', 'PL915C', 20500, 'Corolla', 'Available', 'Toyota', 11, 102);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000076XXX', 'PL916A', 22500, 'F-150', 'Available', 'Ford', 13, 103);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000077XXX', 'PL917B', 34000, 'Sierra', 'Available', 'Chevrolet', 13, 103);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000078XXX', 'PL918C', 41000, 'CX-5', 'Available', 'Mazda', 12, 103);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000079XXX', 'PL919A', 39000, 'Camry', 'Available', 'Toyota', 14, 103);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000080XXX', 'PL920B', 29000, 'Civic', 'Maintenance', 'Honda', 10, 103);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000081XXX', 'PL921C', 18000, 'Rogue', 'Available', 'Hyundai', 13, 104);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000082XXX', 'PL922A', 20000, 'Camry', 'Available', 'Toyota', 11, 104);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000083XXX', 'PL923B', 21500, 'CX-5', 'Maintenance', 'Mazda', 12, 104);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000084XXX', 'PL924C', 24000, 'Corolla', 'Available', 'Toyota', 11, 104);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000085XXX', 'PL925A', 31000, 'Sierra', 'Available', 'Chevrolet', 13, 104);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000086XXX', 'PL926B', 27000, 'F-150', 'Available', 'Ford', 13, 104);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000087XXX', 'PL927C', 22000, 'CR-V', 'Available', 'Honda', 12, 104);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000088XXX', 'PL928A', 24500, 'Camry', 'Available', 'Hyundai', 14, 102);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000089XXX', 'PL929B', 26000, 'Civic', 'Available', 'Toyota', 10, 101);
INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('VIN000000090XXX', 'PL930C', 24000, 'Corolla', 'Available', 'Mazda', 11, 100);


DELETE FROM Relocation;

INSERT INTO Relocation (sourceAreaID, targetAreaID, fee)
WITH base(a1, a2, fee) AS (
  VALUES
    (1, 2, 220.00),
    (1, 5, 260.00),
    (1, 6, 180.00),
    (2, 5, 210.00),
    (2, 6, 380.00),
    (5, 6, 300.00),
    (3, 4, 230.00),
    (2, 4, 700.00),
    (2, 3, 900.00),
    (1, 4, 780.00),
    (1, 3, 980.00),
    (5, 4, 760.00),
    (5, 3, 960.00),
    (6, 4, 820.00),
    (6, 3, 1020.00)
),
pairs(sourceAreaID, targetAreaID, fee) AS (
  SELECT a1, a2, fee FROM base
  UNION ALL
  SELECT a2, a1, fee FROM base
)
SELECT sourceAreaID, targetAreaID, fee
FROM pairs;