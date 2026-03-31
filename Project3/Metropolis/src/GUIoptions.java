import java.math.BigDecimal;
import java.sql.*;
import java.sql.Date;
import java.util.*;

class GUIOptions {

    static String lookupCustomerReservation(Connection con, String email) {
        if (email == null || email.isBlank()) {
            return "Please enter a customer email.";
        }

        try {
            if (!customerExists(con, email.trim())) {
                return "Customer does not exist. Please add customer first (Option 4).";
            }
        } catch (SQLException e) {
            return formatSqlError("Lookup failed.", e);
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

        StringBuilder sb = new StringBuilder();
        boolean hasRows = false;

        try (PreparedStatement pstmt = con.prepareStatement(detailSql)) {
            pstmt.setString(1, email.trim());

            try (ResultSet rs = pstmt.executeQuery()) {
                sb.append("--- Reservations for ").append(email.trim()).append(" ---\n\n");

                while (rs.next()) {
                    hasRows = true;

                    int resID = rs.getInt("resID");
                    Timestamp bookedAt = rs.getTimestamp("bookedAtTime");
                    Date pickupDate = rs.getDate("pickupDate");
                    Date returnDate = rs.getDate("returnDate");
                    int contractID = rs.getInt("contractID");
                    String planType = rs.getString("planType");
                    BigDecimal totalCost = rs.getBigDecimal("totalCost");
                    String employeeName = rs.getString("employeeName");
                    String className = rs.getString("className");
                    String make = rs.getString("make");
                    String model = rs.getString("model");
                    String city = rs.getString("city");
                    String areaName = rs.getString("areaName");

                    sb.append("Reservation ").append(resID)
                            .append(" | booked: ").append(bookedAt)
                            .append(" | pickup: ").append(pickupDate)
                            .append(" | return: ").append(returnDate)
                            .append("\n");

                    if (planType != null) {
                        sb.append("  Agreement ").append(contractID)
                                .append(" | plan: ").append(planType)
                                .append(" | cost: ").append(totalCost)
                                .append("\n");

                        sb.append("  Handled by: ").append(employeeName).append("\n");

                        sb.append("  Vehicle: ").append(className)
                                .append(" (").append(make).append(" ").append(model).append(")")
                                .append(" | location: ").append(city).append(", ").append(areaName)
                                .append("\n");
                    } else {
                        sb.append("  No agreement linked yet.\n");
                    }

                    sb.append("\n");
                }
            }
        } catch (SQLException e) {
            return formatSqlError("Lookup failed.", e);
        }

        if (!hasRows) {
            return "No reservations found for this email.";
        }

        return sb.toString();
    }

    static String addCustomer(
            Connection con,
            String email,
            String name,
            String address,
            String expiry
    ) {
        if (isBlank(email) || isBlank(name) || isBlank(address) || isBlank(expiry)) {
            return "Please fill in all customer fields.";
        }

        String sql = "INSERT INTO Customer (email, name, address, license_expiry) VALUES (?, ?, ?, ?)";

        try (PreparedStatement pstmt = con.prepareStatement(sql)) {
            pstmt.setString(1, email.trim());
            pstmt.setString(2, name.trim());
            pstmt.setString(3, address.trim());
            pstmt.setDate(4, Date.valueOf(expiry.trim()));
            pstmt.executeUpdate();
            return "Customer added successfully.";
        } catch (SQLException e) {
            return formatSqlError("Add customer failed.", e);
        } catch (IllegalArgumentException e) {
            return "Invalid date format. Please use YYYY-MM-DD.";
        }
    }

    static String rewardTopEmployees(Connection con) {
        String topSql =
                "SELECT e.eID, e.name, COUNT(a.contractID) AS num_agreements " +
                        "FROM Employee e " +
                        "JOIN Agreement a ON e.eID = a.eID " +
                        "GROUP BY e.eID, e.name " +
                        "ORDER BY num_agreements DESC " +
                        "FETCH FIRST 3 ROWS ONLY";

        String updateSql = "UPDATE Employee SET salary = salary * ? WHERE eID = ?";
        double[] multipliers = {1.15, 1.10, 1.05};

        StringBuilder sb = new StringBuilder();

        try {
            con.setAutoCommit(false);

            List<Integer> topEmployeeIds = new ArrayList<>();
            List<String> topEmployeeNames = new ArrayList<>();
            List<Integer> agreementCounts = new ArrayList<>();

            try (PreparedStatement ps = con.prepareStatement(topSql);
                 ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    topEmployeeIds.add(rs.getInt("eID"));
                    topEmployeeNames.add(rs.getString("name"));
                    agreementCounts.add(rs.getInt("num_agreements"));
                }
            }

            if (topEmployeeIds.isEmpty()) {
                con.rollback();
                return "No eligible employees found to reward.";
            }

            try (PreparedStatement ps = con.prepareStatement(updateSql)) {
                for (int i = 0; i < topEmployeeIds.size(); i++) {
                    ps.setDouble(1, multipliers[i]);
                    ps.setInt(2, topEmployeeIds.get(i));
                    ps.executeUpdate();
                }
            }

            con.commit();

            sb.append("Rewarded top employees:\n\n");
            for (int i = 0; i < topEmployeeIds.size(); i++) {
                int pct = (int) ((multipliers[i] - 1.0) * 100);
                sb.append(i + 1).append(". ")
                        .append(topEmployeeNames.get(i))
                        .append(" (eID=").append(topEmployeeIds.get(i))
                        .append(", agreements=").append(agreementCounts.get(i))
                        .append(") -> +").append(pct).append("%\n");
            }

            return sb.toString();

        } catch (SQLException e) {
            try {
                con.rollback();
            } catch (SQLException ignored) {
            }
            return formatSqlError("Reward operation failed.", e);
        } finally {
            try {
                con.setAutoCommit(true);
            } catch (SQLException ignored) {
            }
        }
    }


    static String cancellationReassignment(Connection con, String oldVin) {
        if (isBlank(oldVin)) {
            return "Please enter a VIN.";
        }

        String findAgreements =
                "SELECT a.contractID, v.classID, a.resID " +
                        "FROM Agreement a " +
                        "JOIN Vehicle v ON a.vin = v.vin " +
                        "WHERE a.vin = ?";

        StringBuilder sb = new StringBuilder();

        try {
            con.setAutoCommit(false);

            try (PreparedStatement pstmt = con.prepareStatement(findAgreements)) {
                pstmt.setString(1, oldVin.trim());

                try (ResultSet rs = pstmt.executeQuery()) {
                    while (rs.next()) {
                        int contractID = rs.getInt("contractID");
                        int classID = rs.getInt("classID");

                        String findNewVin =
                                "SELECT vin FROM Vehicle " +
                                        "WHERE classID = ? AND status = 'Available' AND vin <> ? " +
                                        "FETCH FIRST 1 ROWS ONLY";

                        String newVin = null;

                        try (PreparedStatement pstmt2 = con.prepareStatement(findNewVin)) {
                            pstmt2.setInt(1, classID);
                            pstmt2.setString(2, oldVin.trim());

                            try (ResultSet rs2 = pstmt2.executeQuery()) {
                                if (rs2.next()) {
                                    newVin = rs2.getString("vin");
                                }
                            }
                        }

                        if (newVin != null) {
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

                            sb.append("Reassigned Agreement ")
                                    .append(contractID)
                                    .append(" to new vehicle ")
                                    .append(newVin)
                                    .append("\n");
                        } else {
                            sb.append("Could not find an available vehicle for Agreement ")
                                    .append(contractID)
                                    .append(". Customer might need manual notification.\n");
                        }
                    }
                }
            }

            String updateOldV = "UPDATE Vehicle SET status = 'Maintenance' WHERE vin = ?";
            try (PreparedStatement pstmt = con.prepareStatement(updateOldV)) {
                pstmt.setString(1, oldVin);
                int updated = pstmt.executeUpdate();

                if (updated != 1) {
                    con.rollback();
                    return "Vehicle VIN " + oldVin + " does not exist.";
                }
            }

            con.commit();

            if (sb.length() == 0) {
                sb.append("No agreements were linked to vehicle ").append(oldVin.trim()).append(".\n");
            }

            sb.append("Vehicle ").append(oldVin.trim())
                    .append(" is now in maintenance. Reassignments completed.");

            return sb.toString();

        } catch (SQLException e) {
            try {
                con.rollback();
            } catch (SQLException ignored) {
            }
            return formatSqlError("Cancellation/reassignment failed.", e);
        } finally {
            try {
                con.setAutoCommit(true);
            } catch (SQLException ignored) {
            }
        }
    }

    static String revenueByAreaAndClass(Connection con) {
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

        StringBuilder sb = new StringBuilder();

        try (Statement stmt = con.createStatement();
             ResultSet rs = stmt.executeQuery(sql)) {
            boolean hasRows = false;
            sb.append("Area | Class | NumAgreements | TotalRevenue\n");

            while (rs.next()) {
                hasRows = true;
                sb.append(rs.getString("areaname")).append(" | ")
                        .append(rs.getString("classname")).append(" | ")
                        .append(rs.getInt("num_agreements")).append(" | ")
                        .append(rs.getBigDecimal("total_revenue")).append("\n");
            }

            return hasRows ? sb.toString() : "No rows found.";

        } catch (SQLException e) {
            return formatSqlError("Revenue query failed.", e);
        }
    }

    static String availableVehiclesByArea(Connection con) {
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

        StringBuilder sb = new StringBuilder();

        try (Statement stmt = con.createStatement();
             ResultSet rs = stmt.executeQuery(sql)) {
            boolean hasRows = false;
            sb.append("Area | NumberAvailableVehicles\n");

            while (rs.next()) {
                hasRows = true;
                sb.append(rs.getString("areaname")).append(" | ")
                        .append(rs.getInt("number_vehicles")).append("\n");
            }

            return hasRows ? sb.toString() : "No rows found.";

        } catch (SQLException e) {
            return formatSqlError("Available vehicles query failed.", e);
        }
    }

    static String relocationPlannerSimulation(Connection con) {
        final double UTIL_TARGET = 0.75;
        final double DONOR_MAX_UTIL = 0.65;
        final double UTIL_SAFE_THRESHOLD = 0.45;
        final double ALPHA = 100.0;
        final double BETA = 10.0;

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

        StringBuilder sb = new StringBuilder();

        try {
            List<BranchStats> branches = new ArrayList<>();
            Map<String, Double> feeMap = new HashMap<>();

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

                    int maxGiveWhileSafe =
                            b.fleetSize - (int) Math.ceil(b.activeReservations / DONOR_MAX_UTIL);
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
                return "No branch data found.";
            }

            int maxActive = 0;
            for (BranchStats b : branches) {
                if (b.activeReservations > maxActive) {
                    maxActive = b.activeReservations;
                }
            }
            double denomActive = Math.max(1.0, (double) maxActive);

            List<BranchStats> targets = new ArrayList<>();
            List<BranchStats> donors = new ArrayList<>();

            for (BranchStats b : branches) {
                if (b.utilization > UTIL_TARGET && b.needVehicles > 0) {
                    targets.add(b);
                }
                if (b.utilization < DONOR_MAX_UTIL && b.donorCapacity > 0) {
                    donors.add(b);
                }
            }

            sb.append("=== Overloaded Branches (>75% utilization) ===\n");
            if (targets.isEmpty()) {
                sb.append("None. No relocation needed.");
                return sb.toString();
            }

            for (BranchStats t : targets) {
                sb.append("Branch ")
                        .append(t.branchId)
                        .append(" (")
                        .append(t.city)
                        .append(") util=")
                        .append(String.format("%.2f", t.utilization * 100.0))
                        .append("% need=")
                        .append(t.needVehicles)
                        .append("\n");
            }

            Map<String, RelocationMove> moveMap = new LinkedHashMap<>();
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

                        double sourceUtil =
                                donor.fleetSize == 0 ? 0.0 :
                                        ((double) donor.activeReservations / donor.fleetSize);

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

            sb.append("\n=== Relocation Plan (Simulation) ===\n");
            if (moveMap.isEmpty()) {
                sb.append("No feasible donor/route pairs found from Relocation table.");
                return sb.toString();
            }

            int totalMoved = 0;
            for (RelocationMove m : moveMap.values()) {
                totalMoved += m.quantity;
                sb.append("Move ")
                        .append(m.quantity)
                        .append(" vehicle(s): Branch ")
                        .append(m.fromBranchId)
                        .append(" (")
                        .append(m.fromCity)
                        .append(") -> Branch ")
                        .append(m.toBranchId)
                        .append(" (")
                        .append(m.toCity)
                        .append(")")
                        .append(" | transfer=")
                        .append(String.format("%.2f", m.transferCost))
                        .append(" | opportunity=")
                        .append(String.format("%.2f", m.opportunityCost))
                        .append(" | total=")
                        .append(String.format("%.2f", m.totalCost))
                        .append("\n");
            }

            sb.append("\nTotal moved: ").append(totalMoved).append("\n");
            sb.append("Total transfer cost: ")
                    .append(String.format("%.2f", totalTransferCost))
                    .append("\n");
            sb.append("Total opportunity cost: ")
                    .append(String.format("%.2f", totalOpportunityCost))
                    .append("\n");
            sb.append("Grand total score: ")
                    .append(String.format("%.2f", totalTransferCost + totalOpportunityCost));

            return sb.toString();

        } catch (SQLException e) {
            return "Planner query failed\nCode: " + e.getErrorCode() +
                    " SQLState: " + e.getSQLState() +
                    "\n" + e.getMessage();
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

    private static boolean customerExists(Connection con, String email) throws SQLException {
        String sql = "SELECT 1 FROM Customer WHERE email = ?";
        try (PreparedStatement pstmt = con.prepareStatement(sql)) {
            pstmt.setString(1, email);
            try (ResultSet rs = pstmt.executeQuery()) {
                return rs.next();
            }
        }
    }

    private static boolean isBlank(String s) {
        return s == null || s.trim().isEmpty();
    }

    private static String formatSqlError(String prefix, SQLException e) {
        return prefix +
                "\nCode: " + e.getErrorCode() +
                " SQLState: " + e.getSQLState() +
                "\n" + e.getMessage();
    }

    // Helper Methods for Option 2 - Create Reservation
    static String getExistingReservations(Connection con, String email) {
        if (email == null || email.isBlank()) {
            return "Please enter a customer email.";
        }

        String sql = "SELECT resID, bookedAtTime FROM Reservation WHERE email = ? ORDER BY bookedAtTime DESC";
        StringBuilder sb = new StringBuilder();

        try {
            if (!customerExists(con, email.trim())) {
                return "Customer does not exist. Please add customer first.";
            }
        } catch (SQLException e) {
            return formatSqlError("Customer lookup failed.", e);
        }

        try (PreparedStatement ps = con.prepareStatement(sql)) {
            ps.setString(1, email.trim());
            try (ResultSet rs = ps.executeQuery()) {
                boolean hasRows = false;
                sb.append("Existing reservations:\n");
                while (rs.next()) {
                    hasRows = true;
                    sb.append("resID=")
                            .append(rs.getInt("resID"))
                            .append(" bookedAt=")
                            .append(rs.getTimestamp("bookedAtTime"))
                            .append("\n");
                }
                if (!hasRows) {
                    sb.append("No existing reservations found.");
                }
                return sb.toString();
            }
        } catch (SQLException e) {
            return formatSqlError("Reservation lookup failed.", e);
        }
    }

    static String getBranches(Connection con) {
        String sql = "SELECT branchID, city FROM Branch ORDER BY city";
        StringBuilder sb = new StringBuilder();

        try (Statement st = con.createStatement();
             ResultSet rs = st.executeQuery(sql)) {

            boolean hasRows = false;
            sb.append("Available branches:\n");
            while (rs.next()) {
                hasRows = true;
                sb.append("branchID=")
                        .append(rs.getInt("branchID"))
                        .append(" city=")
                        .append(rs.getString("city"))
                        .append("\n");
            }
            return hasRows ? sb.toString() : "No branches found.";
        } catch (SQLException e) {
            return formatSqlError("Branch lookup failed.", e);
        }
    }

    static String getEmployeesForBranch(Connection con, int branchID) {
        String sql = "SELECT eID, name FROM Employee WHERE branchID = ? ORDER BY eID";
        StringBuilder sb = new StringBuilder();

        try (PreparedStatement ps = con.prepareStatement(sql)) {
            ps.setInt(1, branchID);
            try (ResultSet rs = ps.executeQuery()) {
                boolean hasRows = false;
                sb.append("Employees in selected branch:\n");
                while (rs.next()) {
                    hasRows = true;
                    sb.append("eID=")
                            .append(rs.getInt("eID"))
                            .append(" name=")
                            .append(rs.getString("name"))
                            .append("\n");
                }
                return hasRows ? sb.toString() : "No employees available in selected branch.";
            }
        } catch (SQLException e) {
            return formatSqlError("Employee lookup failed.", e);
        }
    }

    static String getAvailableVehiclesForBranch(Connection con, int branchID) {
        String sql =
                "SELECT v.vin, vc.className, v.make, v.model, v.mileage " +
                        "FROM Vehicle v " +
                        "JOIN VehicleClass vc ON vc.classID = v.classID " +
                        "WHERE v.branchID = ? AND v.status = 'Available' " +
                        "ORDER BY vc.className, v.make, v.model";

        StringBuilder sb = new StringBuilder();

        try (PreparedStatement ps = con.prepareStatement(sql)) {
            ps.setInt(1, branchID);
            try (ResultSet rs = ps.executeQuery()) {
                boolean hasRows = false;
                sb.append("Available vehicles in selected branch:\n");
                while (rs.next()) {
                    hasRows = true;
                    sb.append("vin=")
                            .append(rs.getString("vin"))
                            .append(" class=")
                            .append(rs.getString("className"))
                            .append(" make/model=")
                            .append(rs.getString("make"))
                            .append(" ")
                            .append(rs.getString("model"))
                            .append(" mileage=")
                            .append(rs.getInt("mileage"))
                            .append("\n");
                }
                return hasRows ? sb.toString() : "No available vehicles in selected branch.";
            }
        } catch (SQLException e) {
            return formatSqlError("Vehicle lookup failed.", e);
        }
    }

    static void createWalkInReservation(
            Connection con,
            String email,
            int resID,
            String pickupDate,
            String returnDate
    ) throws SQLException {
        String resSql = "INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (?, CURRENT TIMESTAMP, ?)";
        try (PreparedStatement ps = con.prepareStatement(resSql)) {
            ps.setInt(1, resID);
            ps.setString(2, email);
            ps.executeUpdate();
        }

        String rpSql = "INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (?, 1, ?, ?)";
        try (PreparedStatement ps = con.prepareStatement(rpSql)) {
            ps.setInt(1, resID);
            ps.setDate(2, Date.valueOf(pickupDate));
            ps.setDate(3, Date.valueOf(returnDate));
            ps.executeUpdate();
        }
    }

    static int nextReservationId(Connection con) throws SQLException {
        String sql = "SELECT COALESCE(MAX(resID), 0) + 1 AS nextResID FROM Reservation";
        try (Statement st = con.createStatement();
             ResultSet rs = st.executeQuery(sql)) {
            rs.next();
            return rs.getInt("nextResID");
        }
    }

    static String createReservationAgreement(
            Connection con,
            String email,
            int chosenResID,
            boolean createWalkIn,
            String pickupDate,
            String returnDate,
            int branchID,
            int eID,
            String vin,
            int contractID,
            String planType,
            double totalCost
    ) {
        try {
            con.setAutoCommit(false);

            if (email == null || email.isBlank()) {
                con.rollback();
                return "Please enter customer email.";
            }

            if (!customerExists(con, email.trim())) {
                con.rollback();
                return "Customer does not exist. Please add customer first.";
            }

            int resID;
            if (createWalkIn) {
                resID = nextReservationId(con);
                createWalkInReservation(con, email.trim(), resID, pickupDate.trim(), returnDate.trim());
            } else {
                resID = chosenResID;
            }

            String aSql = "INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES (?, ?, ?, ?, ?, ?)";
            try (PreparedStatement pstmt = con.prepareStatement(aSql)) {
                pstmt.setInt(1, contractID);
                pstmt.setString(2, planType.trim());
                pstmt.setDouble(3, totalCost);
                pstmt.setInt(4, eID);
                pstmt.setString(5, vin.trim());
                pstmt.setInt(6, resID);
                pstmt.executeUpdate();
            }

            String vSql = "UPDATE Vehicle SET status = 'Rented' WHERE vin = ? AND status = 'Available'";
            try (PreparedStatement pstmt = con.prepareStatement(vSql)) {
                pstmt.setString(1, vin.trim());
                int updated = pstmt.executeUpdate();
                if (updated != 1) {
                    throw new SQLException("Selected vehicle is no longer available.");
                }
            }

            con.commit();
            return "Agreement created successfully. Linked reservation " + resID + " to customer " + email + ".";

        } catch (SQLException e) {
            try { con.rollback(); } catch (SQLException ignored) {}
            return formatSqlError("Create reservation/agreement failed.", e);
        } catch (IllegalArgumentException e) {
            try { con.rollback(); } catch (SQLException ignored) {}
            return "Invalid input format. Check dates, numbers, and plan type.";
        } finally {
            try { con.setAutoCommit(true); } catch (SQLException ignored) {}
        }
    }
}
