import java.io.Console;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.Arrays;
import java.util.Scanner;

class main {
    private static final String URL = "jdbc:db2://winter2026-comp421.cs.mcgill.ca:50000/comp421";

    public static void main(String[] args) {
        registerDriver();

        try (Scanner sc = new Scanner(System.in)) {
            String[] credentials = resolveCredentials(sc);
            if (credentials == null) {
                System.err.println("Missing credentials. Exiting.");
                return;
            }

            try (Connection con = DriverManager.getConnection(URL, credentials[0], credentials[1])) {
                System.out.println("Connected to DB2.");
                runMainMenu(con, sc);
            }
        } catch (SQLException e) {
            System.out.println("Database connection/setup failed");
            System.out.println("Code: " + e.getErrorCode() + " SQLState: " + e.getSQLState());
            System.out.println(e.getMessage());
        }
    }

    private static void registerDriver() {
        try {
            Class.forName("com.ibm.db2.jcc.DB2Driver");
        } catch (ClassNotFoundException e) {
            System.out.println("Could not load DB2 JDBC driver class.");
            System.out.println(e.getMessage());
            System.exit(1);
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
                    option7TestSelectAll(con, sc);
                    break;
                case 7:
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
        System.out.println("6. Test: SELECT * FROM table");
        System.out.println("7. Quit");
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

    private static void option7TestSelectAll(Connection con, Scanner sc) {
        System.out.print("Enter table name: ");
        String tableName = sc.nextLine().trim();
        if (!tableName.matches("[A-Za-z0-9_]+")) {
            System.out.println("Invalid table name.");
            return;
        }

        String sql = "SELECT * FROM " + tableName;
        try (Statement st = con.createStatement(); ResultSet rs = st.executeQuery(sql)) {
            ResultSetMetaData md = rs.getMetaData();
            int cols = md.getColumnCount();

            for (int i = 1; i <= cols; i++) {
                if (i > 1) {
                    System.out.print(" | ");
                }
                System.out.print(md.getColumnName(i));
            }
            System.out.println();

            while (rs.next()) {
                for (int i = 1; i <= cols; i++) {
                    if (i > 1) {
                        System.out.print(" | ");
                    }
                    System.out.print(rs.getString(i));
                }
                System.out.println();
            }
        } catch (SQLException e) {
            System.out.println("SELECT test failed");
            System.out.println("Code: " + e.getErrorCode() + " SQLState: " + e.getSQLState());
            System.out.println(e.getMessage());
        }
    }

    private static String[] resolveCredentials(Scanner sc) {
        Console console = System.console();
        if (console != null) {
            String promptUser = trimToNull(console.readLine("DB2 username: "));
            char[] pwdChars = console.readPassword("DB2 password: ");
            String promptPassword = pwdChars == null ? null : trimToNull(new String(pwdChars));
            if (pwdChars != null) {
                Arrays.fill(pwdChars, '\0');
            }
            if (promptUser != null && promptPassword != null) {
                return new String[] {promptUser, promptPassword};
            }
            return null;
        }

        System.out.print("DB2 username: ");
        String promptUser = trimToNull(sc.nextLine());
        System.out.print("DB2 password: ");
        String promptPassword = trimToNull(sc.nextLine());
        if (promptUser == null || promptPassword == null) {
            return null;
        }
        return new String[] {promptUser, promptPassword};
    }

    private static String trimToNull(String value) {
        if (value == null) {
            return null;
        }
        String trimmed = value.trim();
        return trimmed.isEmpty() ? null : trimmed;
    }
}
