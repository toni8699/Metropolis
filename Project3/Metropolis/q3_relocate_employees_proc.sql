CONNECT TO COMP421@

DECLARE v_rows INT DEFAULT 0;

...

UPDATE Vehicle
SET status = 'Rented'
WHERE vin = v_vin
  AND status <> 'Rented';

GET DIAGNOSTICS v_rows = ROW_COUNT;
SET p_vehicle_updates = p_vehicle_updates + v_rows;

...

UPDATE Employee
SET salary = salary * (1 + p_raise_pct)
WHERE eID IN (SELECT DISTINCT eID FROM Agreement);

GET DIAGNOSTICS p_employee_updates = ROW_COUNT;
END@