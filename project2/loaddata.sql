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
-- Customers
INSERT INTO Customer (email, name, address, license_expiry) VALUES ('mike.mccarthy@example.com', 'Mike McCarthy', '10 Queen St, Montreal', '2027-06-14');
INSERT INTO Customer (email, name, address, license_expiry) VALUES ('sara.goldman@example.com', 'Sara Goldman', '45 King St, Toronto', '2027-09-06');
INSERT INTO Customer (email, name, address, license_expiry) VALUES ('nina.carter@example.com', 'Nina Carter', '120 Granville, Vancouver', '2027-07-22');
INSERT INTO Customer (email, name, address, license_expiry) VALUES ('ethan.ross@example.com', 'Ethan Ross', '62 3rd Ave, Calgary', '2027-09-29');
INSERT INTO Customer (email, name, address, license_expiry) VALUES ('lisa.adjani@example.com', 'Lisa Adjani', '420 Rideau, Ottawa', '2027-01-22');
INSERT INTO Customer (email, name, address, license_expiry) VALUES ('alex.jones@example.com', 'Alex Jones', '88 Elm St, Quebec City', '2027-04-29');
INSERT INTO Customer (email, name, address, license_expiry) VALUES ('rosa.rivera@example.com', 'Rosa Rivera', '2100 Saint Laurent, Montreal', '2027-07-07');
INSERT INTO Customer (email, name, address, license_expiry) VALUES ('samir.khan@example.com', 'Samir Khan', '19 Yonge St, Toronto', '2027-09-02');
INSERT INTO Customer (email, name, address, license_expiry) VALUES ('ivy.norris@example.com', 'Ivy Norris', '540 Howe St, Vancouver', '2027-08-20');
INSERT INTO Customer (email, name, address, license_expiry) VALUES ('cole.lewis@example.com', 'Cole Lewis', '33 Macleod Trail, Calgary', '2027-03-30');

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

-- Reservations & RentalPeriods
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2000, '2026-03-24 13:57:00', 'alex.jones@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2000, 1, '2026-04-05', '2026-04-11');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2001, '2026-03-14 03:32:00', 'ethan.ross@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2001, 1, '2026-03-22', '2026-03-30');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2002, '2026-03-08 00:07:00', 'ivy.norris@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2002, 1, '2026-03-17', '2026-03-26');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2003, '2026-03-23 17:34:00', 'nina.carter@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2003, 1, '2026-04-09', '2026-04-18');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2004, '2026-02-17 16:00:00', 'lisa.adjani@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2004, 1, '2026-02-28', '2026-03-02');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2005, '2026-03-11 16:14:00', 'rosa.rivera@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2005, 1, '2026-03-26', '2026-03-28');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2006, '2026-02-20 23:03:00', 'sara.goldman@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2006, 1, '2026-03-08', '2026-03-18');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2007, '2026-03-04 05:06:00', 'alex.jones@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2007, 1, '2026-03-12', '2026-03-17');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2008, '2026-03-17 00:48:00', 'mike.mccarthy@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2008, 1, '2026-04-03', '2026-04-05');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2009, '2026-03-22 06:31:00', 'alex.jones@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2009, 1, '2026-04-02', '2026-04-05');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2010, '2026-02-24 22:49:00', 'nina.carter@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2010, 1, '2026-03-13', '2026-03-19');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2011, '2026-02-21 23:42:00', 'nina.carter@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2011, 1, '2026-03-12', '2026-03-20');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2012, '2026-03-10 14:27:00', 'ivy.norris@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2012, 1, '2026-03-20', '2026-03-29');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2013, '2026-03-22 15:15:00', 'rosa.rivera@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2013, 1, '2026-04-08', '2026-04-10');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2014, '2026-02-21 20:05:00', 'lisa.adjani@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2014, 1, '2026-03-01', '2026-03-09');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2015, '2026-02-21 13:05:00', 'ethan.ross@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2015, 1, '2026-02-24', '2026-03-04');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2016, '2026-02-18 02:56:00', 'cole.lewis@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2016, 1, '2026-02-23', '2026-02-24');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2017, '2026-03-18 10:56:00', 'ivy.norris@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2017, 1, '2026-03-26', '2026-03-29');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2018, '2026-03-12 19:07:00', 'rosa.rivera@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2018, 1, '2026-04-02', '2026-04-04');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2019, '2026-03-15 20:37:00', 'cole.lewis@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2019, 1, '2026-03-23', '2026-03-24');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2020, '2026-03-23 05:31:00', 'ethan.ross@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2020, 1, '2026-03-26', '2026-03-28');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2021, '2026-03-06 13:21:00', 'alex.jones@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2021, 1, '2026-03-09', '2026-03-16');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2022, '2026-03-08 09:21:00', 'sara.goldman@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2022, 1, '2026-03-19', '2026-03-27');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2023, '2026-03-01 00:24:00', 'nina.carter@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2023, 1, '2026-03-18', '2026-03-20');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2024, '2026-02-22 17:59:00', 'lisa.adjani@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2024, 1, '2026-03-12', '2026-03-22');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2025, '2026-03-17 16:02:00', 'cole.lewis@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2025, 1, '2026-03-26', '2026-04-03');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2026, '2026-03-31 02:48:00', 'ethan.ross@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2026, 1, '2026-04-12', '2026-04-17');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2027, '2026-04-01 09:19:00', 'ivy.norris@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2027, 1, '2026-04-08', '2026-04-12');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2028, '2026-03-22 10:52:00', 'sara.goldman@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2028, 1, '2026-04-07', '2026-04-13');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2029, '2026-02-22 17:19:00', 'ivy.norris@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2029, 1, '2026-03-06', '2026-03-07');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2030, '2026-02-27 20:49:00', 'sara.goldman@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2030, 1, '2026-03-20', '2026-03-23');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2031, '2026-02-15 20:09:00', 'cole.lewis@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2031, 1, '2026-03-08', '2026-03-10');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2032, '2026-03-13 20:27:00', 'ivy.norris@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2032, 1, '2026-03-30', '2026-04-09');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2033, '2026-03-29 13:12:00', 'samir.khan@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2033, 1, '2026-04-18', '2026-04-23');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2034, '2026-02-18 04:49:00', 'mike.mccarthy@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2034, 1, '2026-02-25', '2026-03-05');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2035, '2026-03-30 10:36:00', 'samir.khan@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2035, 1, '2026-04-15', '2026-04-17');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2036, '2026-03-03 11:29:00', 'cole.lewis@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2036, 1, '2026-03-09', '2026-03-12');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2037, '2026-03-05 08:24:00', 'sara.goldman@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2037, 1, '2026-03-13', '2026-03-23');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2038, '2026-03-27 05:03:00', 'cole.lewis@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2038, 1, '2026-04-18', '2026-04-24');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2039, '2026-03-30 23:17:00', 'samir.khan@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2039, 1, '2026-04-01', '2026-04-11');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2040, '2026-03-25 01:26:00', 'ethan.ross@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2040, 1, '2026-04-12', '2026-04-18');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2041, '2026-03-08 18:50:00', 'ivy.norris@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2041, 1, '2026-03-21', '2026-03-28');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2042, '2026-03-15 16:01:00', 'ivy.norris@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2042, 1, '2026-03-25', '2026-04-03');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2043, '2026-03-16 20:36:00', 'ethan.ross@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2043, 1, '2026-03-25', '2026-04-02');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2044, '2026-03-02 01:56:00', 'lisa.adjani@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2044, 1, '2026-03-14', '2026-03-15');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2045, '2026-02-23 20:52:00', 'sara.goldman@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2045, 1, '2026-03-10', '2026-03-19');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2046, '2026-03-18 08:52:00', 'alex.jones@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2046, 1, '2026-04-02', '2026-04-03');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2047, '2026-03-22 22:13:00', 'ivy.norris@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2047, 1, '2026-03-31', '2026-04-04');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2048, '2026-02-19 21:59:00', 'nina.carter@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2048, 1, '2026-02-25', '2026-03-05');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2049, '2026-03-29 05:05:00', 'samir.khan@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2049, 1, '2026-04-05', '2026-04-11');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2050, '2026-03-23 08:49:00', 'rosa.rivera@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2050, 1, '2026-04-02', '2026-04-03');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2051, '2026-03-24 06:23:00', 'samir.khan@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2051, 1, '2026-04-10', '2026-04-19');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2052, '2026-02-25 03:26:00', 'cole.lewis@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2052, 1, '2026-03-15', '2026-03-22');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2053, '2026-03-28 23:14:00', 'ivy.norris@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2053, 1, '2026-04-05', '2026-04-15');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2054, '2026-03-08 12:42:00', 'ethan.ross@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2054, 1, '2026-03-16', '2026-03-26');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2055, '2026-03-16 09:43:00', 'sara.goldman@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2055, 1, '2026-03-29', '2026-04-02');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2056, '2026-03-28 16:04:00', 'nina.carter@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2056, 1, '2026-03-30', '2026-04-06');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2057, '2026-03-19 03:21:00', 'samir.khan@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2057, 1, '2026-03-27', '2026-04-03');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2058, '2026-02-23 17:25:00', 'alex.jones@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2058, 1, '2026-02-27', '2026-03-01');
INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (2059, '2026-03-04 06:30:00', 'ivy.norris@example.com');
INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (2059, 1, '2026-03-21', '2026-03-28');

-- Agreements
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5000, 'Weekly', 278.71, 204, 'VIN000000001XXX', 2000);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5001, 'Weekly', 794.95, 200, 'VIN000000002XXX', 2001);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5002, 'Daily', 2326.47, 200, 'VIN000000003XXX', 2002);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5003, 'Monthly', 262.88, 203, 'VIN000000004XXX', 2003);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5004, 'Daily', 1316.65, 201, 'VIN000000005XXX', 2004);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5005, 'Daily', 1359.33, 200, 'VIN000000006XXX', 2005);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5006, 'Daily', 2069.42, 200, 'VIN000000007XXX', 2006);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5007, 'Monthly', 311.66, 202, 'VIN000000008XXX', 2007);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5008, 'Monthly', 1346.99, 206, 'VIN000000009XXX', 2008);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5009, 'Daily', 2916.46, 205, 'VIN000000010XXX', 2009);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5010, 'Monthly', 2694.3, 206, 'VIN000000011XXX', 2010);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5011, 'Monthly', 1700.64, 207, 'VIN000000012XXX', 2011);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5012, 'Monthly', 1633.96, 201, 'VIN000000013XXX', 2012);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5013, 'Monthly', 238.27, 200, 'VIN000000014XXX', 2013);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5014, 'Daily', 2931.75, 208, 'VIN000000015XXX', 2014);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5015, 'Weekly', 2332.97, 200, 'VIN000000016XXX', 2015);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5016, 'Weekly', 2717.61, 209, 'VIN000000017XXX', 2016);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5017, 'Monthly', 2123.2, 206, 'VIN000000018XXX', 2017);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5018, 'Monthly', 775.32, 204, 'VIN000000019XXX', 2018);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5019, 'Daily', 3030.91, 206, 'VIN000000020XXX', 2019);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5020, 'Daily', 1929.66, 202, 'VIN000000021XXX', 2020);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5021, 'Weekly', 2378.95, 205, 'VIN000000022XXX', 2021);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5022, 'Monthly', 2025.33, 208, 'VIN000000023XXX', 2022);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5023, 'Weekly', 1693.37, 200, 'VIN000000024XXX', 2023);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5024, 'Daily', 1378.86, 208, 'VIN000000025XXX', 2024);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5025, 'Daily', 1200.96, 204, 'VIN000000026XXX', 2025);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5026, 'Monthly', 2461.94, 209, 'VIN000000027XXX', 2026);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5027, 'Weekly', 1836.41, 200, 'VIN000000028XXX', 2027);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5028, 'Daily', 1667.88, 200, 'VIN000000029XXX', 2028);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5029, 'Weekly', 1035.1, 200, 'VIN000000030XXX', 2029);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5030, 'Daily', 2368.79, 203, 'VIN000000031XXX', 2030);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5031, 'Weekly', 1920.35, 202, 'VIN000000032XXX', 2031);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5032, 'Monthly', 2772.17, 202, 'VIN000000033XXX', 2032);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5033, 'Weekly', 1491.7, 209, 'VIN000000034XXX', 2033);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5034, 'Daily', 2517.93, 207, 'VIN000000035XXX', 2034);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5035, 'Daily', 2555.91, 204, 'VIN000000036XXX', 2035);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5036, 'Weekly', 2038.11, 201, 'VIN000000037XXX', 2036);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5037, 'Monthly', 1252.16, 203, 'VIN000000038XXX', 2037);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5038, 'Monthly', 1898.08, 201, 'VIN000000039XXX', 2038);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5039, 'Daily', 846.3, 201, 'VIN000000040XXX', 2039);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5040, 'Weekly', 3143.35, 204, 'VIN000000041XXX', 2040);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5041, 'Monthly', 597.73, 200, 'VIN000000042XXX', 2041);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5042, 'Weekly', 2231.85, 201, 'VIN000000043XXX', 2042);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5043, 'Weekly', 1904.79, 203, 'VIN000000044XXX', 2043);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5044, 'Monthly', 2597.49, 209, 'VIN000000045XXX', 2044);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5045, 'Daily', 1745.22, 201, 'VIN000000046XXX', 2045);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5046, 'Monthly', 2724.65, 201, 'VIN000000047XXX', 2046);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5047, 'Weekly', 1600.99, 202, 'VIN000000048XXX', 2047);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5048, 'Monthly', 2299.97, 205, 'VIN000000049XXX', 2048);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5049, 'Daily', 1568.15, 206, 'VIN000000050XXX', 2049);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5050, 'Monthly', 1322.85, 201, 'VIN000000051XXX', 2050);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5051, 'Weekly', 2496.92, 204, 'VIN000000052XXX', 2051);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5052, 'Daily', 1241.57, 209, 'VIN000000053XXX', 2052);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5053, 'Daily', 230.11, 208, 'VIN000000054XXX', 2053);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5054, 'Daily', 1754.87, 203, 'VIN000000055XXX', 2054);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5055, 'Weekly', 2117.93, 200, 'VIN000000056XXX', 2055);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5056, 'Daily', 228.37, 203, 'VIN000000057XXX', 2056);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5057, 'Monthly', 651.38, 204, 'VIN000000058XXX', 2057);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5058, 'Monthly', 1454.61, 201, 'VIN000000059XXX', 2058);
INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (5059, 'Daily', 1886.89, 202, 'VIN000000060XXX', 2059);

-- Relocations
INSERT INTO Relocation (sourceAreaID, targetAreaID, fee) VALUES (1, 2, 524);
INSERT INTO Relocation (sourceAreaID, targetAreaID, fee) VALUES (1, 3, 454);
INSERT INTO Relocation (sourceAreaID, targetAreaID, fee) VALUES (2, 4, 473);
INSERT INTO Relocation (sourceAreaID, targetAreaID, fee) VALUES (3, 5, 700);
INSERT INTO Relocation (sourceAreaID, targetAreaID, fee) VALUES (4, 5, 543);