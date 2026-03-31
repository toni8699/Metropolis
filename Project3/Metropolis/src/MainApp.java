import javafx.application.Application;
import javafx.scene.Scene;
import javafx.scene.layout.BorderPane;
import javafx.stage.Stage;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.util.Scanner;

public class MainApp extends Application {

    private static final String URL =
            "jdbc:db2://winter2026-comp421.cs.mcgill.ca:50000/comp421";

    private Connection con;

    @Override
    public void start(Stage stage) {
        try {
            registerDriver();

            // temporary: hardcode while building
            Scanner sc = new Scanner(System.in);

            System.out.print("Enter DB username: ");
            String user = sc.nextLine();

            System.out.print("Enter DB password: ");
            String password = sc.nextLine();

            con = DriverManager.getConnection(URL, user, password);

            BorderPane root = new BorderPane();
            root.setCenter(new HomeScreen(root, con));

            Scene scene = new Scene(root, 800, 600);
            stage.setFullScreen(true);
            stage.setScene(scene);
            stage.setTitle("Metropolis Nexus");
            stage.show();

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void registerDriver() {
        try {
            Class.forName("com.ibm.db2.jcc.DB2Driver");
        } catch (ClassNotFoundException e) {
            throw new RuntimeException("Could not load DB2 JDBC driver.", e);
        }
    }

    @Override
    public void stop() {
        try {
            if (con != null && !con.isClosed()) {
                con.close();
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
    }

    public static void main(String[] args) {
        launch();
    }
}
