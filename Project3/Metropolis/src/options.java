import java.sql.*;
import java.util.Scanner;

class options {
    /**
     * Option 1: Lookup reservations for a customer email.
     * Validates customer existence and lists reservation IDs with booking times.
     */
    static void option1LookupCustomerReservation(Connection con, Scanner sc) {
        System.out.print("Enter customer email: ");
        String email = sc.nextLine().trim();

        try {
            if (!customerExists(con, email)) {
                System.out.println("Customer does not exist. Please add customer first (Option 4).");
                return;
            }
        } catch (SQLException e) {
            System.out.println("Test failed");
            System.out.println("Code: " + e.getErrorCode() + " SQLState: " + e.getSQLState());
            System.out.println(e.getMessage());
            return;
        }

        String detailSql =
            "SELECT r.resID, r.bookedAtTime, rp.pickupDate, rp.returnDate, " +
            "a.contractID, a.planType, a.totalCost, " +
            "e.name AS employeeName, " +
            "v.vin, v.make, v.model, vc.className, " +
            "b.branchID, b.city, ar.areaName " +
            "FROM Reservation r " +
            "LEFT JOIN RentalPeriod rp ON rp.resID = r.resID " +
            "LEFT JOIN Agreement a ON a.resID = r.resID " +
            "LEFT JOIN Employee e ON e.eID = a.eID " +
            "LEFT JOIN Vehicle v ON v.vin = a.vin " +
            "LEFT JOIN VehicleClass vc ON vc.classID = v.classID " +
            "LEFT JOIN Branch b ON b.branchID = v.branchID " +
            "LEFT JOIN Area ar ON ar.areaID = b.areaID " +
            "WHERE r.email = ? " +
            "ORDER BY r.resID, rp.periodID";

        boolean hasRows = false;
        try (PreparedStatement pstmt = con.prepareStatement(detailSql)) {
            pstmt.setString(1, email);
            try (ResultSet rs = pstmt.executeQuery()) {
                System.out.println("\n--- Reservations for " + email + " ---");
                while (rs.next()) {
                    hasRows = true;
                    int resID = rs.getInt("resID");
                    Timestamp bookedAt = rs.getTimestamp("bookedAtTime");
                    Date pickupDate = rs.getDate("pickupDate");
                    Date returnDate = rs.getDate("returnDate");
                    int contractID = rs.getInt("contractID");
                    String planType = rs.getString("planType");
                    java.math.BigDecimal totalCost = rs.getBigDecimal("totalCost");
                    String employeeName = rs.getString("employeeName");
                    String className = rs.getString("className");
                    String make = rs.getString("make");
                    String model = rs.getString("model");
                    String city = rs.getString("city");
                    String areaName = rs.getString("areaName");

                    System.out.println(
                        "Reservation " + resID +
                        " | booked: " + bookedAt +
                        " | pickup: " + pickupDate +
                        " | return: " + returnDate
                    );
                    if (planType != null) {
                        System.out.println(
                            "  Agreement " + contractID +
                            " | plan: " + planType +
                            " | cost: " + totalCost
                        );
                        System.out.println("  Handled by: " + employeeName);
                        System.out.println(
                            "  Vehicle: " + className +
                            " (" + make + " " + model + ")" +
                            " | location: " + city + ", " + areaName
                        );
                    } else {
                        System.out.println("  No agreement linked yet.");
                    }
                }
            }
        } catch (SQLException e) {
            System.out.println("Test failed");
            System.out.println("Code: " + e.getErrorCode() + " SQLState: " + e.getSQLState());
            System.out.println(e.getMessage());
            return;
        }

        if (!hasRows) {
            System.out.println("No reservations found for this email.");
            return;
        }
    }

    /**
     * Option 2: Create reservation, rental period, and optional agreement.
     * Runs as one transaction and rolls back on failure.
     */
static void option2CreateReservationAgreement(Connection con, Scanner sc) {
        try {
            con.setAutoCommit(false);

            System.out.print("Enter customer email: ");
            String email = sc.nextLine().trim();

            if (!customerExists(con, email)) {
                System.out.println("Customer does not exist. Please add customer first (Option 4).");
                con.rollback();
                return;
            }

            int resID;
            java.util.Set<Integer> existingResIds = new java.util.HashSet<>();
            String existingResSql = "SELECT resID, bookedAtTime FROM Reservation WHERE email = ? ORDER BY bookedAtTime DESC";
            try (PreparedStatement ps = con.prepareStatement(existingResSql)) {
                ps.setString(1, email);
                try (ResultSet rs = ps.executeQuery()) {
                    System.out.println("\nExisting reservations:");
                    while (rs.next()) {
                        int existingResID = rs.getInt("resID");
                        Timestamp bookedAt = rs.getTimestamp("bookedAtTime");
                        existingResIds.add(existingResID);
                        System.out.println("  resID=" + existingResID + " bookedAt=" + bookedAt);
                    }
                }
            }

            if (!existingResIds.isEmpty()) {
                System.out.print("Enter an existing resID to link, or 0 for walk-in: ");
                int chosenResID = readIntInput(sc);
                if (chosenResID == 0) {
                    resID = nextReservationId(con);
                    createWalkInReservation(con, email, resID, sc);
                } else if (existingResIds.contains(chosenResID)) {
                    resID = chosenResID;
                } else {
                    System.out.println("Invalid reservation selection.");
                    con.rollback();
                    return;
                }
            } else {
                System.out.println("No existing reservation found. Creating walk-in reservation.");
                resID = nextReservationId(con);
                createWalkInReservation(con, email, resID, sc);
            }

            java.util.Set<Integer> branchIds = new java.util.HashSet<>();
            String branchSql = "SELECT branchID, city FROM Branch ORDER BY city";
            System.out.println("\nAvailable branches:");
            try (Statement st = con.createStatement();
                 ResultSet rs = st.executeQuery(branchSql)) {
                while (rs.next()) {
                    int branchID = rs.getInt("branchID");
                    branchIds.add(branchID);
                    System.out.println("  branchID=" + branchID + " city=" + rs.getString("city"));
                }
            }
            System.out.print("Choose branchID: ");
            int branchID = readIntInput(sc);
            if (!branchIds.contains(branchID)) {
                System.out.println("Invalid branch selection.");
                con.rollback();
                return;
            }

            java.util.Set<Integer> employeeIds = new java.util.HashSet<>();
            String employeeSql = "SELECT eID, name FROM Employee WHERE branchID = ? ORDER BY eID";
            System.out.println("\nEmployees in selected branch:");
            try (PreparedStatement ps = con.prepareStatement(employeeSql)) {
                ps.setInt(1, branchID);
                try (ResultSet rs = ps.executeQuery()) {
                    while (rs.next()) {
                        int employeeId = rs.getInt("eID");
                        employeeIds.add(employeeId);
                        System.out.println("  eID=" + employeeId + " name=" + rs.getString("name"));
                    }
                }
            }
            if (employeeIds.isEmpty()) {
                System.out.println("No employees available in selected branch.");
                con.rollback();
                return;
            }
            System.out.print("Choose employee eID handling this rental: ");
            int eID = readIntInput(sc);
            if (!employeeIds.contains(eID)) {
                System.out.println("Invalid employee selection for this branch.");
                con.rollback();
                return;
            }

            java.util.Set<String> availableVins = new java.util.HashSet<>();
            String vehicleSql =
                "SELECT v.vin, vc.className, v.make, v.model, v.mileage " +
                "FROM Vehicle v " +
                "JOIN VehicleClass vc ON vc.classID = v.classID " +
                "WHERE v.branchID = ? AND v.status = 'Available' " +
                "ORDER BY vc.className, v.make, v.model";
            System.out.println("\nAvailable vehicles in selected branch:");
            try (PreparedStatement ps = con.prepareStatement(vehicleSql)) {
                ps.setInt(1, branchID);
                try (ResultSet rs = ps.executeQuery()) {
                    while (rs.next()) {
                        String vin = rs.getString("vin");
                        availableVins.add(vin);
                        System.out.println(
                            "  vin=" + vin +
                            " class=" + rs.getString("className") +
                            " make/model=" + rs.getString("make") + " " + rs.getString("model") +
                            " mileage=" + rs.getInt("mileage")
                        );
                    }
                }
            }
            if (availableVins.isEmpty()) {
                System.out.println("No available vehicles in selected branch.");
                con.rollback();
                return;
            }

            System.out.print("Choose vehicle VIN: ");
            String vin = sc.nextLine().trim();
            if (!availableVins.contains(vin)) {
                System.out.println("Invalid VIN selection.");
                con.rollback();
                return;
            }

            System.out.print("Enter Agreement ID: ");
            int contractID = readIntInput(sc);
            System.out.print("Enter Plan Type (Daily/Weekly/Monthly): ");
            String planType = sc.nextLine().trim();
            System.out.print("Enter Total Cost: ");
            double totalCost = Double.parseDouble(sc.nextLine().trim());

            String aSql = "INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (?, ?, ?, ?, ?, ?)";
            try (PreparedStatement pstmt = con.prepareStatement(aSql)) {
                pstmt.setInt(1, contractID);
                pstmt.setString(2, planType);
                pstmt.setDouble(3, totalCost);
                pstmt.setInt(4, eID);
                pstmt.setString(5, vin);
                pstmt.setInt(6, resID);
                pstmt.executeUpdate();
            }

            String vSql = "UPDATE Vehicle SET status = 'Rented' WHERE vin = ? AND status = 'Available'";
            try (PreparedStatement pstmt = con.prepareStatement(vSql)) {
                pstmt.setString(1, vin);
                int updated = pstmt.executeUpdate();
                if (updated != 1) {
                    throw new SQLException("Selected vehicle is no longer available.");
                }
            }

            con.commit();
            System.out.println("Agreement created successfully. Linked reservation " + resID + " to customer " + email + ".");

        } catch (SQLException e) {
            try { con.rollback(); } catch (SQLException se) { se.printStackTrace(); }
            System.out.println("SQL failed");
            System.out.println("Code: " + e.getErrorCode() + " SQLState: " + e.getSQLState());
            System.out.println(e.getMessage());
        } catch (IllegalArgumentException e) {
            try { con.rollback(); } catch (SQLException se) { se.printStackTrace(); }
            System.out.println("Invalid input format.");
        } finally {
            try { con.setAutoCommit(true); } catch (SQLException e) { e.printStackTrace(); }
        }
    }
    /**
     * Option 3: Reassign agreements when a vehicle is moved to maintenance.
     * Finds same-class replacement vehicles and updates affected agreements.
     */
static void option3CancellationReassignment(Connection con, Scanner sc) {
        System.out.print("Enter VIN of the vehicle being sent to maintenance: ");
        String oldVin = sc.nextLine().trim();

        String findAgreements = "SELECT a.contractID, v.classID, a.resID FROM Agreement a JOIN Vehicle v ON a.vin = v.vin WHERE a.vin = ?";
        
        try {
            con.setAutoCommit(false);
            try (PreparedStatement pstmt = con.prepareStatement(findAgreements)) {
                pstmt.setString(1, oldVin);
                try (ResultSet rs = pstmt.executeQuery()) {
                    while (rs.next()) {
                        int contractID = rs.getInt("contractID");
                        int classID = rs.getInt("classID");
                        
                        // Find an available vehicle of the same class
                        String findNewVin = "SELECT vin FROM Vehicle WHERE classID = ? AND status = 'Available' AND vin <> ? FETCH FIRST 1 ROWS ONLY";
                        String newVin = null;
                        try (PreparedStatement pstmt2 = con.prepareStatement(findNewVin)) {
                            pstmt2.setInt(1, classID);
                            pstmt2.setString(2, oldVin);
                            try (ResultSet rs2 = pstmt2.executeQuery()) {
                                if (rs2.next()) {
                                newVin = rs2.getString("vin");
                                }
                            }
                        }
                        if (newVin != null) {
                            // Reassign
                            String updateAg = "UPDATE Agreement SET vin = ? WHERE contractID = ?";
                            try (PreparedStatement pstmt3 = con.prepareStatement(updateAg)) {
                                pstmt3.setString(1, newVin);
                                pstmt3.setInt(2, contractID);
                                pstmt3.executeUpdate();
                            }
                            
                            String updateNewV = "UPDATE Vehicle SET status = 'Rented' WHERE vin = ?";
                            try (PreparedStatement pstmt4 = con.prepareStatement(updateNewV)) {
                                pstmt4.setString(1, newVin);
                                pstmt4.executeUpdate();
                            }
                            System.out.println("Reassigned Agreement " + contractID + " to new vehicle " + newVin);
                        } else {
                            System.out.println("Could not find an available vehicle for Agreement " + contractID + ". Customer might need manual notification.");
                        }
                    }
                }
            }
            
            // Set old vehicle to maintenance
            String updateOldV = "UPDATE Vehicle SET status = 'Maintenance' WHERE vin = ?";
            try (PreparedStatement pstmt = con.prepareStatement(updateOldV)) {
                pstmt.setString(1, oldVin);
                pstmt.executeUpdate();
            }
            
            con.commit();
            System.out.println("Vehicle " + oldVin + " is now in maintenance. Reassignments completed.");
            
        } catch (SQLException e) {
            try { con.rollback(); } catch (SQLException se) { se.printStackTrace(); }
            System.out.println("Test failed");
            System.out.println("Code: " + e.getErrorCode() + " SQLState: " + e.getSQLState());
            System.out.println(e.getMessage());
        } finally {
            try { con.setAutoCommit(true); } catch (SQLException e) { e.printStackTrace(); }
        }
    }

    /**
     * Option 4: Add a new customer record.
     * Inserts a Customer tuple from prompted values.
     */
    static void option4AddCustomer(Connection con, Scanner sc) {
        System.out.print("Enter email: ");
        String email = sc.nextLine().trim();
        System.out.print("Enter name: ");
        String name = sc.nextLine().trim();
        System.out.print("Enter address: ");
        String address = sc.nextLine().trim();
        System.out.print("Enter license expiry (YYYY-MM-DD): ");
        String expiry = sc.nextLine().trim();

        String sql = "INSERT INTO Customer (email, name, address, license_expiry) VALUES (?, ?, ?, ?)";
        try (PreparedStatement pstmt = con.prepareStatement(sql)) {
            pstmt.setString(1, email);
            pstmt.setString(2, name);
            pstmt.setString(3, address);
            pstmt.setDate(4, Date.valueOf(expiry));
            pstmt.executeUpdate();
            System.out.println("Customer added successfully.");
        } catch (SQLException e) {
            System.out.println("Test failed");
            System.out.println("Code: " + e.getErrorCode() + " SQLState: " + e.getSQLState());
            System.out.println(e.getMessage());
        } catch (IllegalArgumentException e) {
            System.out.println("Invalid date format.");
        }
    }

    //Maybe stricter rule for the update
    /**
     * Option 5: Reward top 3 employees by agreement volume.
     * Tuning: edit multipliers[] to change reward percentages (currently +15%, +10%, +5%).
     */
    static void option5RewardTopEmployees(Connection con, Scanner sc) {
        String topSql =
            "SELECT e.eID, e.name, COUNT(a.contractID) AS num_agreements " +
            "FROM Employee e " +
            "JOIN Agreement a ON e.eID = a.eID " +
            "GROUP BY e.eID, e.name " +
            "ORDER BY num_agreements DESC " +
            "FETCH FIRST 3 ROWS ONLY";

        String updateSql = "UPDATE Employee SET salary = salary * ? WHERE eID = ?";
        double[] multipliers = {1.15, 1.10, 1.05};

        try {
            con.setAutoCommit(false);

            java.util.List<Integer> topEmployeeIds = new java.util.ArrayList<>();
            java.util.List<String> topEmployeeNames = new java.util.ArrayList<>();
            java.util.List<Integer> agreementCounts = new java.util.ArrayList<>();

            try (PreparedStatement ps = con.prepareStatement(topSql);
                 ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    topEmployeeIds.add(rs.getInt("eID"));
                    topEmployeeNames.add(rs.getString("name"));
                    agreementCounts.add(rs.getInt("num_agreements"));
                }
            }

            if (topEmployeeIds.isEmpty()) {
                System.out.println("No eligible employees found to reward.");
                con.rollback();
                return;
            }

            System.out.println("Top performers before reward:");
            for (int i = 0; i < topEmployeeIds.size(); i++) {
                System.out.println(
                    (i + 1) + ". " + topEmployeeNames.get(i) +
                    " (eID=" + topEmployeeIds.get(i) +
                    ", agreements=" + agreementCounts.get(i) + ")"
                );
            }

            try (PreparedStatement ps = con.prepareStatement(updateSql)) {
                for (int i = 0; i < topEmployeeIds.size(); i++) {
                    ps.setDouble(1, multipliers[i]);
                    ps.setInt(2, topEmployeeIds.get(i));
                    ps.executeUpdate();
                }
            }

            con.commit();
            System.out.println("Rewarded top employees:");
            for (int i = 0; i < topEmployeeIds.size(); i++) {
                int pct = (int) ((multipliers[i] - 1.0) * 100);
                System.out.println(
                    (i + 1) + ". " + topEmployeeNames.get(i) +
                    " (eID=" + topEmployeeIds.get(i) +
                    ", agreements=" + agreementCounts.get(i) +
                    ") -> +" + pct + "%"
                );
            }
        } catch (SQLException e) {
            try { con.rollback(); } catch (SQLException ignored) {}
            System.out.println("Test failed");
            System.out.println("Code: " + e.getErrorCode() + " SQLState: " + e.getSQLState());
            System.out.println(e.getMessage());
        } finally {
            try { con.setAutoCommit(true); } catch (SQLException ignored) {}
        }
    }
    private static boolean customerExists(Connection con, String email) throws SQLException {
        String sql = "SELECT 1 FROM Customer WHERE email = ?";
        try (PreparedStatement pstmt = con.prepareStatement(sql)) {
            pstmt.setString(1, email);
            try (ResultSet rs = pstmt.executeQuery()) {
                return rs.next();
            }
        }
    }

    private static int readIntInput(Scanner sc) {
        return Integer.parseInt(sc.nextLine().trim());
    }

    private static int nextReservationId(Connection con) throws SQLException {
        String sql = "SELECT COALESCE(MAX(resID), 0) + 1 AS nextResID FROM Reservation";
        try (Statement st = con.createStatement();
             ResultSet rs = st.executeQuery(sql)) {
            rs.next();
            return rs.getInt("nextResID");
        }
    }

    // option 6 (?)
    private static void createWalkInReservation(Connection con, String email, int resID, Scanner sc) throws SQLException {
        String resSql = "INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (?, CURRENT TIMESTAMP, ?)";
        try (PreparedStatement ps = con.prepareStatement(resSql)) {
            ps.setInt(1, resID);
            ps.setString(2, email);
            ps.executeUpdate();
        }

        System.out.print("Enter Pickup Date (YYYY-MM-DD): ");
        String pickupDate = sc.nextLine().trim();
        System.out.print("Enter Return Date (YYYY-MM-DD): ");
        String returnDate = sc.nextLine().trim();

        String rpSql = "INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (?, 1, ?, ?)";
        try (PreparedStatement ps = con.prepareStatement(rpSql)) {
            ps.setInt(1, resID);
            ps.setDate(2, Date.valueOf(pickupDate));
            ps.setDate(3, Date.valueOf(returnDate));
            ps.executeUpdate();
        }
    }

    /**
     * Option 8: Revenue and agreement counts by area and vehicle class.
     */
    static void option8RevenueByAreaAndClass(Connection con, Scanner sc) {
        String sql =
            "SELECT Area.areaname, VehicleClass.classname, " +
            "COUNT(Agreement.contractid) AS num_agreements, " +
            "SUM(Agreement.totalcost) AS total_revenue " +
            "FROM Area " +
            "JOIN Branch ON Area.areaid = Branch.areaid " +
            "JOIN Vehicle ON Branch.branchid = Vehicle.branchid " +
            "JOIN VehicleClass ON Vehicle.classid = VehicleClass.classid " +
            "JOIN Agreement ON Vehicle.vin = Agreement.vin " +
            "GROUP BY Area.areaname, VehicleClass.classname " +
            "ORDER BY Area.areaname, total_revenue DESC";

        try (Statement stmt = con.createStatement();
             ResultSet rs = stmt.executeQuery(sql)) {
            boolean hasRows = false;
            System.out.println("Area | Class | NumAgreements | TotalRevenue");
            while (rs.next()) {
                hasRows = true;
                System.out.println(
                    rs.getString("areaname") + " | " +
                    rs.getString("classname") + " | " +
                    rs.getInt("num_agreements") + " | " +
                    rs.getBigDecimal("total_revenue")
                );
            }
            if (!hasRows) {
                System.out.println("No rows found.");
            }
        } catch (SQLException e) {
            System.out.println("Query failed");
            System.out.println("Code: " + e.getErrorCode() + " SQLState: " + e.getSQLState());
            System.out.println(e.getMessage());
        }
    }

    /**
     * Option 9: Count available vehicles per area.
     */
    static void option9AvailableVehiclesByArea(Connection con, Scanner sc) {
        String sql =
            "WITH VehiclesAreas AS ( " +
            "  SELECT Area.areaname, Vehicle.vin " +
            "  FROM Area " +
            "  JOIN Branch ON Area.areaid = Branch.areaid " +
            "  JOIN Vehicle ON Branch.branchid = Vehicle.branchid " +
            "  WHERE Vehicle.status = 'Available' " +
            ") " +
            "SELECT VehiclesAreas.areaname, COUNT(VehiclesAreas.vin) AS number_vehicles " +
            "FROM VehiclesAreas " +
            "GROUP BY VehiclesAreas.areaname " +
            "ORDER BY number_vehicles DESC";

        try (Statement stmt = con.createStatement();
             ResultSet rs = stmt.executeQuery(sql)) {
            boolean hasRows = false;
            System.out.println("Area | NumberAvailableVehicles");
            while (rs.next()) {
                hasRows = true;
                System.out.println(
                    rs.getString("areaname") + " | " +
                    rs.getInt("number_vehicles")
                );
            }
            if (!hasRows) {
                System.out.println("No rows found.");
            }
        } catch (SQLException e) {
            System.out.println("Query failed");
            System.out.println("Code: " + e.getErrorCode() + " SQLState: " + e.getSQLState());
            System.out.println(e.getMessage());
        }
    }



    /**
     * Option 10: Simulate fleet relocation plan using transfer and opportunity cost.
     * Score per candidate move:
     * totalCost = transferCost + opportunityCost
     * opportunityCost = ALPHA * max(0, donorUtilization - UTIL_SAFE_THRESHOLD)
     *                   + BETA * (donorActiveReservations / maxActiveReservations)
     * where donorUtilization = donorActiveReservations / donorFleetSize.
     * Algorithm:
     * 1) Build target set (utilization > UTIL_TARGET) and donor set (utilization < DONOR_MAX_UTIL).
     * 2) For each needed vehicle at each target, evaluate all feasible donors with route fees.
     * 3) Pick donor with minimum totalCost (greedy), decrement donor capacity, repeat.
     * Tuning: edit UTIL_TARGET, DONOR_MAX_UTIL, UTIL_SAFE_THRESHOLD, ALPHA, and BETA.
     * This is simulation-only and does not update branch assignments in the database.
     */
    static void option10RelocationPlannerSimulation(Connection con, Scanner sc) {
        final double UTIL_TARGET = 0.75; // Target utilization for overloaded branches.
        final double DONOR_MAX_UTIL = 0.65; // Max utilization for donors before they're too overloaded.
        final double UTIL_SAFE_THRESHOLD = 0.45; // Utilization threshold below which donor is safe to give.
        final double ALPHA = 100.0; // Weight for pressure factor (donorUtilization - UTIL_SAFE_THRESHOLD).
        final double BETA = 10.0; // Weight for demand (donorActiveReservations / maxActiveReservations).

        String branchStatsSql =
            "SELECT b.branchID, b.city, b.areaID, " +
            "COUNT(DISTINCT v.vin) AS fleet_size, " +
            "COUNT(DISTINCT r.resID) AS active_reservations, " +
            "SUM(CASE WHEN v.status = 'Available' THEN 1 ELSE 0 END) AS available_vehicles " +
            "FROM Branch b " +
            "JOIN Vehicle v ON v.branchID = b.branchID " +
            "LEFT JOIN Agreement a ON a.vin = v.vin " +
            "LEFT JOIN Reservation r ON r.resID = a.resID " +
            "GROUP BY b.branchID, b.city, b.areaID";

        String relocationFeeSql =
            "SELECT sourceAreaID, targetAreaID, fee FROM Relocation";

        try {
            java.util.List<BranchStats> branches = new java.util.ArrayList<>();
            java.util.Map<String, Double> feeMap = new java.util.HashMap<>();

            try (Statement st = con.createStatement();
                 ResultSet rs = st.executeQuery(branchStatsSql)) {
                while (rs.next()) {
                    BranchStats b = new BranchStats();
                    b.branchId = rs.getInt("branchID");
                    b.city = rs.getString("city");
                    b.areaId = rs.getInt("areaID");
                    b.fleetSize = rs.getInt("fleet_size");
                    b.activeReservations = rs.getInt("active_reservations");
                    b.availableVehicles = rs.getInt("available_vehicles");
                    b.utilization = b.fleetSize == 0 ? 0.0 : ((double) b.activeReservations / b.fleetSize);
                    b.needVehicles = Math.max(0, 2 * b.activeReservations - b.fleetSize);
                    int maxGiveWhileSafe = b.fleetSize - (int) Math.ceil(b.activeReservations / DONOR_MAX_UTIL);
                    b.donorCapacity = Math.max(0, Math.min(b.availableVehicles, maxGiveWhileSafe));
                    branches.add(b);
                }
            }

            try (Statement st = con.createStatement();
                 ResultSet rs = st.executeQuery(relocationFeeSql)) {
                while (rs.next()) {
                    int src = rs.getInt("sourceAreaID");
                    int dst = rs.getInt("targetAreaID");
                    double fee = rs.getDouble("fee");
                    feeMap.put(src + "->" + dst, fee);
                }
            }

            if (branches.isEmpty()) {
                System.out.println("No branch data found.");
                return;
            }

            int maxActive = 0;
            for (BranchStats b : branches) {
                if (b.activeReservations > maxActive) {
                    maxActive = b.activeReservations;
                }
            }
            double denomActive = Math.max(1.0, (double) maxActive);

            java.util.List<BranchStats> targets = new java.util.ArrayList<>();
            java.util.List<BranchStats> donors = new java.util.ArrayList<>();
            for (BranchStats b : branches) {
                if (b.utilization > UTIL_TARGET && b.needVehicles > 0) {
                    targets.add(b);
                }
                if (b.utilization < DONOR_MAX_UTIL && b.donorCapacity > 0) {
                    donors.add(b);
                }
            }

            System.out.println("=== Overloaded Branches (>75% utilization) ===");
            if (targets.isEmpty()) {
                System.out.println("None. No relocation needed.");
                return;
            }
            for (BranchStats t : targets) {
                System.out.println(
                    "Branch " + t.branchId + " (" + t.city + ") util=" +
                    String.format("%.2f", t.utilization * 100.0) + "% need=" + t.needVehicles
                );
            }

            java.util.Map<String, RelocationMove> moveMap = new java.util.LinkedHashMap<>();
            double totalTransferCost = 0.0;
            double totalOpportunityCost = 0.0;

            for (BranchStats target : targets) {
                int remainingNeed = target.needVehicles;
                while (remainingNeed > 0) {
                    BranchStats bestDonor = null;
                    double bestTotalCost = Double.MAX_VALUE;
                    double bestTransfer = 0.0;
                    double bestOpportunity = 0.0;

                    for (BranchStats donor : donors) {
                        if (donor.donorCapacity <= 0) {
                            continue;
                        }
                        String feeKey = donor.areaId + "->" + target.areaId;
                        Double transferFee = feeMap.get(feeKey);
                        if (transferFee == null) {
                            continue;
                        }

                        double sourceUtil = donor.fleetSize == 0 ? 0.0 : ((double) donor.activeReservations / donor.fleetSize);
                        double pressure = Math.max(0.0, sourceUtil - UTIL_SAFE_THRESHOLD);
                        double demandNorm = donor.activeReservations / denomActive;
                        double opportunityCost = (ALPHA * pressure) + (BETA * demandNorm);
                        double totalCost = transferFee + opportunityCost;

                        if (totalCost < bestTotalCost) {
                            bestTotalCost = totalCost;
                            bestDonor = donor;
                            bestTransfer = transferFee;
                            bestOpportunity = opportunityCost;
                        }
                    }

                    if (bestDonor == null) {
                        break;
                    }

                    bestDonor.donorCapacity -= 1;
                    remainingNeed -= 1;

                    String key = bestDonor.branchId + "->" + target.branchId;
                    RelocationMove move = moveMap.get(key);
                    if (move == null) {
                        move = new RelocationMove();
                        move.fromBranchId = bestDonor.branchId;
                        move.fromCity = bestDonor.city;
                        move.toBranchId = target.branchId;
                        move.toCity = target.city;
                        moveMap.put(key, move);
                    }
                    move.quantity += 1;
                    move.transferCost += bestTransfer;
                    move.opportunityCost += bestOpportunity;
                    move.totalCost += bestTotalCost;

                    totalTransferCost += bestTransfer;
                    totalOpportunityCost += bestOpportunity;
                }
            }

            System.out.println();
            System.out.println("=== Relocation Plan (Simulation) ===");
            if (moveMap.isEmpty()) {
                System.out.println("No feasible donor/route pairs found from Relocation table.");
                return;
            }

            int totalMoved = 0;
            for (RelocationMove m : moveMap.values()) {
                totalMoved += m.quantity;
                System.out.println(
                    "Move " + m.quantity + " vehicle(s): Branch " + m.fromBranchId + " (" + m.fromCity + ")" +
                    " -> Branch " + m.toBranchId + " (" + m.toCity + ")" +
                    " | transfer=" + String.format("%.2f", m.transferCost) +
                    " | opportunity=" + String.format("%.2f", m.opportunityCost) +
                    " | total=" + String.format("%.2f", m.totalCost)
                );
            }

            System.out.println();
            System.out.println("Total moved: " + totalMoved);
            System.out.println("Total transfer cost: " + String.format("%.2f", totalTransferCost));
            System.out.println("Total opportunity cost: " + String.format("%.2f", totalOpportunityCost));
            System.out.println("Grand total score: " + String.format("%.2f", (totalTransferCost + totalOpportunityCost)));
        } catch (SQLException e) {
            System.out.println("Planner query failed");
            System.out.println("Code: " + e.getErrorCode() + " SQLState: " + e.getSQLState());
            System.out.println(e.getMessage());
        }
    }

    private static class BranchStats {
        int branchId;
        String city;
        int areaId;
        int fleetSize;
        int activeReservations;
        int availableVehicles;
        double utilization;
        int needVehicles;
        int donorCapacity;
    }

    private static class RelocationMove {
        int fromBranchId;
        String fromCity;
        int toBranchId;
        String toCity;
        int quantity;
        double transferCost;
        double opportunityCost;
        double totalCost;
    }

}
