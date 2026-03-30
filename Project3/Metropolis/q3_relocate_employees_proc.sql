CONNECT TO COMP421@

DROP PROCEDURE RelocateEmployeesForDemand@

CREATE PROCEDURE RelocateEmployeesForDemand (
    IN p_target_branch INT,
    IN p_source_branch INT,
    IN p_max_to_move INT,
    OUT p_moved_count INT
)
LANGUAGE SQL
BEGIN
    DECLARE v_target_fleet INT DEFAULT 0;
    DECLARE v_target_active INT DEFAULT 0;
    DECLARE v_source_fleet INT DEFAULT 0;
    DECLARE v_source_active INT DEFAULT 0;
    DECLARE v_target_util DECIMAL(10,4) DEFAULT 0.0;
    DECLARE v_source_util DECIMAL(10,4) DEFAULT 0.0;
    DECLARE v_emp_id INT;
    DECLARE v_done INT DEFAULT 0;

    DECLARE c_employees CURSOR FOR
        SELECT e.eID
        FROM Employee e
        LEFT JOIN Agreement a ON a.eID = e.eID
        WHERE e.branchID = p_source_branch
          AND e.supervisorID IS NOT NULL
          AND e.eID NOT IN (SELECT bm.eID FROM BranchManager bm)
          AND NOT EXISTS (SELECT 1 FROM Employee s WHERE s.supervisorID = e.eID)
        GROUP BY e.eID
        ORDER BY COUNT(a.contractID) DESC, e.eID;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = 1;

    SET p_moved_count = 0;

    IF p_max_to_move <= 0 OR p_target_branch = p_source_branch THEN
        RETURN;
    END IF;

    SELECT
        COUNT(DISTINCT v.vin),
        COUNT(DISTINCT r.resID)
    INTO v_target_fleet, v_target_active
    FROM Branch b
    JOIN Vehicle v ON v.branchID = b.branchID
    LEFT JOIN Agreement a ON a.vin = v.vin
    LEFT JOIN Reservation r ON r.resID = a.resID
    WHERE b.branchID = p_target_branch;

    SELECT
        COUNT(DISTINCT v.vin),
        COUNT(DISTINCT r.resID)
    INTO v_source_fleet, v_source_active
    FROM Branch b
    JOIN Vehicle v ON v.branchID = b.branchID
    LEFT JOIN Agreement a ON a.vin = v.vin
    LEFT JOIN Reservation r ON r.resID = a.resID
    WHERE b.branchID = p_source_branch;

    IF v_target_fleet > 0 THEN
        SET v_target_util = DECIMAL(v_target_active, 10, 4) / DECIMAL(v_target_fleet, 10, 4);
    END IF;

    IF v_source_fleet > 0 THEN
        SET v_source_util = DECIMAL(v_source_active, 10, 4) / DECIMAL(v_source_fleet, 10, 4);
    END IF;

    IF v_target_util <= v_source_util THEN
        RETURN;
    END IF;

    OPEN c_employees;

    move_loop:
    LOOP
        IF p_moved_count >= p_max_to_move THEN
            LEAVE move_loop;
        END IF;

        SET v_done = 0;
        FETCH c_employees INTO v_emp_id;

        IF v_done = 1 THEN
            LEAVE move_loop;
        END IF;

        UPDATE Employee
        SET branchID = p_target_branch,
            salary = salary * 1.02
        WHERE eID = v_emp_id;

        SET p_moved_count = p_moved_count + 1;
    END LOOP;

    CLOSE c_employees;
END@

