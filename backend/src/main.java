import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.Scanner;

class main {

    public static void main(String[] args) {
        try (Scanner sc = new Scanner(System.in);
             Connection con = Database.connect()) {
            System.out.println("Connected to PostgreSQL.");
            runMainMenu(con, sc);
        } catch (SQLException e) {
            System.out.println("Database connection/setup failed");
            System.out.println("SQLState: " + e.getSQLState());
            System.out.println(e.getMessage());
        }
    }

    private static void runMainMenu(Connection con, Scanner sc) {
        boolean running = true;
        while (running) {
            printMainMenu();
            int option = readInt(sc, "Please enter your option: ");
            switch (option) {
                case 1:
                    options.option1LookupCustomerReservation(con, sc);
                    break;
                case 2:
                    options.option2CreateReservationAgreement(con, sc);
                    break;
                case 3:
                    options.option3CancellationReassignment(con, sc);
                    break;
                case 4:
                    options.option4AddCustomer(con, sc);
                    break;
                case 5:
                    options.option5RewardTopEmployees(con, sc);
                    break;
                case 6:
                    options.option8RevenueByAreaAndClass(con, sc);
                    break;
                case 7:
                    options.option9AvailableVehiclesByArea(con, sc);
                    break;
                case 8:
                    options.option10RelocationPlannerSimulation(con, sc);
                    break;
                case 9:
                    optionSelectAll(con, sc);
                    break;
                case 10:
                    running = false;
                    System.out.println("Goodbye.");
                    break;
                default:
                    System.out.println("Invalid option.");
            }
        }
    }

    private static void printMainMenu() {
        System.out.println();
        System.out.println("=== Metropolis Nexus Main Menu ===");
        System.out.println("1. Lookup Customer Reservation");
        System.out.println("2. Create Reservation + Agreement");
        System.out.println("3. Cancellation Reassignment");
        System.out.println("4. Add Customer");
        System.out.println("5. Reward Top Employees");
        System.out.println("6. Revenue by Area and Vehicle Class");
        System.out.println("7. Available Vehicles by Area");
        System.out.println("8. Relocation Planner (Simulation)");
        System.out.println("9. Select ALL");
        System.out.println("10. Quit");
    }

    private static int readInt(Scanner sc, String prompt) {
        while (true) {
            System.out.print(prompt);
            String input = sc.nextLine().trim();
            try {
                return Integer.parseInt(input);
            } catch (NumberFormatException e) {
                System.out.println("Please enter a valid number.");
            }
        }
    }

    private static void optionSelectAll(Connection con, Scanner sc) {
        System.out.print("Enter table name: ");
        String tableName = sc.nextLine().trim();
        if (!tableName.matches("[A-Za-z0-9_]+")) {
            System.out.println("Invalid table name.");
            return;
        }

        String result = RentalService.selectAllFromTable(con, tableName);
        System.out.println(result);
    }
}
