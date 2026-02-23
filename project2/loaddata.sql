-- Include your INSERT SQL statements in this file.
-- Make sure to terminate each statement with a semicolon (;)

-- LEAVE this statement on. It is required to connect to your database.
CONNECT TO COMP421;

-- Remember to put the INSERT statements for the tables with foreign key references
--    ONLY AFTER the insert for the parent tables!

-- This is only an example of how you add INSERT statements to this file.
--   You may remove it.
INSERT INTO MYTEST01 (id, value) VALUES(4, 1300);
-- A more complex syntax that saves you typing effort.
INSERT INTO MYTEST01 (id, value) VALUES
 (7, 5144),
 (3, 73423),
 (6, -1222)
;
