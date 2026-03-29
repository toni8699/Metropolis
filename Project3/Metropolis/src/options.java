import java.sql.*;
import java.util.Scanner;

class options {
    // TODO : implements these methods        
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

        String listSql = "SELECT resID, bookedAtTime FROM Reservation WHERE email = ?";
        java.util.List<Integer> resIds = new java.util.ArrayList<>();

        try (PreparedStatement pstmt = con.prepareStatement(listSql)) {
            pstmt.setString(1, email);
            try (ResultSet rs = pstmt.executeQuery()) {
                System.out.println("\n--- Reservations for " + email + " ---");
                while (rs.next()) {
                    int resID = rs.getInt("resID");
                    Timestamp bookedAt = rs.getTimestamp("bookedAtTime");
                    System.out.println("Reservation ID: " + resID + " (Booked at: " + bookedAt + ")");
                    resIds.add(resID);
                }
            }
        } catch (SQLException e) {
            System.out.println("Test failed");
            System.out.println("Code: " + e.getErrorCode() + " SQLState: " + e.getSQLState());
            System.out.println(e.getMessage());
            return;
        }

        if (resIds.isEmpty()) {
            System.out.println("No reservations found for this email.");
            return;
        }
    }

static void option2CreateReservationAgreement(Connection con, Scanner sc) {
        try {
            con.setAutoCommit(false);

            System.out.print("Enter customer email: ");
            String email = sc.nextLine().trim();

            // Check if customer exists
            if (!customerExists(con, email)) {
                System.out.println("Customer does not exist. Please add customer first (Option 4).");
                con.rollback();
                return;
            }

            System.out.print("Enter Reservation ID (int): ");
            int resID = Integer.parseInt(sc.nextLine().trim());
            System.out.print("Enter Pickup Date (YYYY-MM-DD): ");
            String pickupDate = sc.nextLine().trim();
            System.out.print("Enter Return Date (YYYY-MM-DD): ");
            String returnDate = sc.nextLine().trim();

            // Insert Reservation
            String resSql = "INSERT INTO Reservation (resID, bookedAtTime, email) VALUES (?, CURRENT TIMESTAMP, ?)";
            try (PreparedStatement pstmt = con.prepareStatement(resSql)) {
                pstmt.setInt(1, resID);
                pstmt.setString(2, email);
                pstmt.executeUpdate();
            }

            // Insert RentalPeriod
            String rpSql = "INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES (?, 1, ?, ?)";
            try (PreparedStatement pstmt = con.prepareStatement(rpSql)) {
                pstmt.setInt(1, resID);
                pstmt.setDate(2, Date.valueOf(pickupDate));
                pstmt.setDate(3, Date.valueOf(returnDate));
                pstmt.executeUpdate();
            }

            System.out.print("Make the agreement too? / Assign vehicle now? (y/n): ");
            if (sc.nextLine().trim().equalsIgnoreCase("y")) {
                System.out.print("Enter Vehicle VIN: ");
                String vin = sc.nextLine().trim();
                System.out.print("Enter Employee ID: ");
                int eID = Integer.parseInt(sc.nextLine().trim());
                System.out.print("Enter Agreement ID: ");
                int contractID = Integer.parseInt(sc.nextLine().trim());
                System.out.print("Enter Plan Type (Daily/Weekly/Monthly): ");
                String planType = sc.nextLine().trim();
                System.out.print("Enter Total Cost: ");
                double totalCost = Double.parseDouble(sc.nextLine().trim());

                // Insert Agreement
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

                // Update Vehicle status
                String vSql = "UPDATE Vehicle SET status = 'Rented' WHERE vin = ?";
                try (PreparedStatement pstmt = con.prepareStatement(vSql)) {
                    pstmt.setString(1, vin);
                    pstmt.executeUpdate();
                }
            }

            con.commit();
            System.out.println("Reservation and Agreement created successfully.");

        } catch (Exception e) {
            try { con.rollback(); } catch (SQLException se) { se.printStackTrace(); }
            if (e instanceof SQLException) {
                System.out.println("SQL failed");
            } else {
                System.out.println("Failed");
            }
        } finally {
            try { con.setAutoCommit(true); } catch (SQLException e) { e.printStackTrace(); }
        }
    }
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
    static void option5RewardTopEmployees(Connection con, Scanner sc) {
        double factor = 1.05;

        String sql = "UPDATE Employee SET salary = salary * ? WHERE eID IN (SELECT DISTINCT eID FROM Agreement)";
        try (PreparedStatement pstmt = con.prepareStatement(sql)) {
            pstmt.setDouble(1, factor);
            int count = pstmt.executeUpdate();
            System.out.println(count + " employees rewarded with a salary increase.");
        } catch (SQLException e) {
            System.out.println("Test failed");
            System.out.println("Code: " + e.getErrorCode() + " SQLState: " + e.getSQLState());
            System.out.println(e.getMessage());
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
}
