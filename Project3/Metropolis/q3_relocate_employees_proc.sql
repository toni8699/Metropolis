CONNECT TO COMP421@

DROP PROCEDURE MarkRentedVehiclesAndReport@

CREATE PROCEDURE MarkRentedVehiclesAndReport (
    IN p_target_status VARCHAR(30),
    OUT p_vehicle_updates INT
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

    OPEN c_vins;

    vehicle_loop:
    LOOP
        SET v_done = 0;
        FETCH c_vins INTO v_vin;

        IF v_done = 1 THEN
            LEAVE vehicle_loop;
        END IF;

        UPDATE Vehicle
        SET status = p_target_status
        WHERE vin = v_vin
          AND status <> p_target_status;

        GET DIAGNOSTICS v_rows = ROW_COUNT;
        SET p_vehicle_updates = p_vehicle_updates + v_rows;
    END LOOP;

    CLOSE c_vins;
END@