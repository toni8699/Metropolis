-- Include your create table DDL statements in this file.
-- Make sure to terminate each statement with a semicolon (;)

-- LEAVE this statement on. It is required to connect to your database.
CONNECT TO COMP421;

-- Parent tables first so that dependent tables can reference them.
CREATE TABLE Area
(
  areaID INT NOT NULL PRIMARY KEY,
  areaName VARCHAR(100) NOT NULL
);

CREATE TABLE VehicleClass
(
  classID INT NOT NULL PRIMARY KEY,
  className VARCHAR(100) NOT NULL,
  securityDeposit DECIMAL(10,2) NOT NULL
);

CREATE TABLE Branch
(
  branchID INT NOT NULL PRIMARY KEY,
  address VARCHAR(200),
  phone_number VARCHAR(20),
  city VARCHAR(100),
  areaID INT NOT NULL,
  managerID INT,
  FOREIGN KEY (areaID) REFERENCES Area(areaID)
);

CREATE TABLE Employee
(
  eID INT NOT NULL PRIMARY KEY,
  name VARCHAR(150) NOT NULL,
  salary DECIMAL(12,2),
  branchID INT NOT NULL,
  supervisorID INT,
  FOREIGN KEY (branchID) REFERENCES Branch(branchID),
  FOREIGN KEY (supervisorID) REFERENCES Employee(eID)
);

CREATE TABLE BranchManager
(
  eID INT NOT NULL PRIMARY KEY,
  branchID INT NOT NULL UNIQUE,
  FOREIGN KEY (eID) REFERENCES Employee(eID),
  FOREIGN KEY (branchID) REFERENCES Branch(branchID)
);

ALTER TABLE Branch
  ADD CONSTRAINT fk_branch_manager FOREIGN KEY (managerID) REFERENCES Employee(eID);

CREATE TABLE Customer
(
  email VARCHAR(255) NOT NULL PRIMARY KEY,
  name VARCHAR(150),
  address VARCHAR(200),
  license_expiry DATE
);

CREATE TABLE Reservation
(
  resID INT NOT NULL PRIMARY KEY,
  bookedAtTime TIMESTAMP NOT NULL,
  email VARCHAR(255) NOT NULL,
  FOREIGN KEY (email) REFERENCES Customer(email)
);

CREATE TABLE RentalPeriod
(
  resID INT NOT NULL,
  periodID INT NOT NULL,
  pickupDate DATE,
  returnDate DATE,
  PRIMARY KEY (resID, periodID),
  FOREIGN KEY (resID) REFERENCES Reservation(resID)
);

CREATE TABLE Vehicle
(
  vin CHAR(17) NOT NULL PRIMARY KEY,
  license_plate VARCHAR(20),
  mileage INT,
  model VARCHAR(100),
  status VARCHAR(30),
  make VARCHAR(50),
  classID INT NOT NULL,
  branchID INT NOT NULL,
  FOREIGN KEY (classID) REFERENCES VehicleClass(classID),
  FOREIGN KEY (branchID) REFERENCES Branch(branchID)
);

CREATE TABLE Agreement
(
  contractID INT NOT NULL PRIMARY KEY,
  planType VARCHAR(50),
  totalCost DECIMAL(12,2),
  eID INT NOT NULL,
  vin CHAR(17) NOT NULL,
  resID INT NOT NULL,
  FOREIGN KEY (eID) REFERENCES Employee(eID),
  FOREIGN KEY (vin) REFERENCES Vehicle(vin),
  FOREIGN KEY (resID) REFERENCES Reservation(resID)
);

CREATE TABLE Relocation
(
  sourceAreaID INT NOT NULL,
  targetAreaID INT NOT NULL,
  fee DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (sourceAreaID, targetAreaID),
  FOREIGN KEY (sourceAreaID) REFERENCES Area(areaID),
  FOREIGN KEY (targetAreaID) REFERENCES Area(areaID),
  CHECK (sourceAreaID <> targetAreaID)
);


