-- Include your drop table DDL statements in this file.
-- Make sure to terminate each statement with a semicolon (;)

-- LEAVE this statement on. It is required to connect to your database.
CONNECT TO COMP421;

-- Drop child tables before parents.
ALTER TABLE Branch DROP FOREIGN KEY fk_branch_manager;
DROP TABLE Relocation;
DROP TABLE Agreement;
DROP TABLE Vehicle;
DROP TABLE RentalPeriod;
DROP TABLE Reservation;
DROP TABLE Customer;
DROP TABLE BranchManager;
DROP TABLE Employee;
DROP TABLE Branch;
DROP TABLE VehicleClass;
DROP TABLE Area;
