import javafx.application.Application;
import javafx.geometry.Pos;
import javafx.scene.Node;
import javafx.scene.Scene;
import javafx.scene.control.Label;
import javafx.scene.layout.BorderPane;
import javafx.scene.layout.VBox;
import javafx.stage.Stage;
import javafx.scene.control.Button;
import java.sql.Connection;

public class HomeScreen extends VBox {

    public HomeScreen(BorderPane root, Connection con) {

        Label title = new Label("Home Menu");
        title.setStyle("-fx-font-size: 20px; -fx-font-weight: bold;");

        // Declaring button objects corresponding to the actions
        Button lookupButton = new Button("Lookup Customer Reservation");
        Button createReservation = new Button("Create Reservation + Agreement");
        Button cancellationReassignment = new Button("Cancellation Reassignment");
        Button addCustomer = new Button("Add Customer");
        Button rewardTopEmployees = new Button("Reward Top Employees");
        Button testSelectAllFromTable = new Button ("Test: SELECT * FROM table");
        Button runRevenueReport = new Button("Run Revenue Report");
        Button availVehiclesByArea = new Button("Available Vehicles By Area");
        Button relocationPlanner = new Button("Relocation Planner Simulation");
        //Button quit = new Button("Quit");

        // Stylistic Tweaks
        lookupButton.setPrefWidth(200);
        createReservation.setPrefWidth(200);
        cancellationReassignment.setPrefWidth(200);
        addCustomer.setPrefWidth(200);
        rewardTopEmployees.setPrefWidth(200);
        testSelectAllFromTable.setPrefWidth(200);
        //quit.setPrefWidth(200);
        runRevenueReport.setPrefWidth(200);
        availVehiclesByArea.setPrefWidth(200);
        relocationPlanner.setPrefWidth(200);

        setAlignment(Pos.CENTER);
        setSpacing(10);

        // Mapping the buttons to the corresponding action

        lookupButton.setOnAction(e -> {
            root.setCenter(new LookUpReservationPane(root, con));
        });


        cancellationReassignment.setOnAction(e -> {
            root.setCenter(new CancellationPane(root, con));
        });


        addCustomer.setOnAction(e -> {
            root.setCenter(new AddCustomerPane(root, con));
        });

        rewardTopEmployees.setOnAction(e -> {
            root.setCenter(new RewardPane(root, con));
        });

        /*
        quit.setOnAction(e -> {
            System.exit(1);
        });
         */

        runRevenueReport.setOnAction(e -> {
            root.setCenter(new RevenuePane(root, con));
        });

        availVehiclesByArea.setOnAction(e -> {
            root.setCenter(new AvailableVehiclesPane(root, con));
        });

        relocationPlanner.setOnAction(e -> {
            root.setCenter(new RelocationPlannerPane(root, con));
        });

        createReservation.setOnAction(e -> {
            root.setCenter(new CreateReservationAgreementPane(root, con));
        });

        // Adding the nodes to the scene
        getChildren().addAll(title, lookupButton, createReservation, cancellationReassignment,
                addCustomer, rewardTopEmployees, runRevenueReport, availVehiclesByArea, relocationPlanner);
    }
}
