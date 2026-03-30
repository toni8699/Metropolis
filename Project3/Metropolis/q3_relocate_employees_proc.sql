CONNECT TO COMP421@

DROP PROCEDURE MarkRentedVehiclesAndReport@

CREATE PROCEDURE MarkRentedVehiclesAndReport (
    IN p_raise_pct DECIMAL(6,4),
    OUT p_vehicle_updates INT,
    OUT p_employee_updates INT
)
LANGUAGE SQL
BEGIN
    DECLARE v_vin CHAR(17);
    DECLARE v_done INT DEFAULT 0;
    DECLARE v_rows INT DEFAULT 0;

    DECLARE c_vins CURSOR FOR
        SELECT DISTINCT a.vin
        FROM Agreement a;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = 1;

    SET p_vehicle_updates = 0;
    SET p_employee_updates = 0;

    IF p_raise_pct < 0 THEN
        SET p_raise_pct = 0;
    END IF;

    OPEN c_vins;

    vehicle_loop:
    LOOP
        SET v_done = 0;
        FETCH c_vins INTO v_vin;

        IF v_done = 1 THEN
            LEAVE vehicle_loop;
        END IF;

        UPDATE Vehicle
        SET status = 'Rented'
        WHERE vin = v_vin
          AND status <> 'Rented';

        GET DIAGNOSTICS v_rows = ROW_COUNT;
        SET p_vehicle_updates = p_vehicle_updates + v_rows;
    END LOOP;

    CLOSE c_vins;

    UPDATE Employee
    SET salary = salary * (1 + p_raise_pct)
    WHERE eID IN (SELECT DISTINCT eID FROM Agreement);

    GET DIAGNOSTICS p_employee_updates = ROW_COUNT;
END@