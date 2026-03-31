import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.control.*;
import javafx.scene.layout.BorderPane;
import javafx.scene.layout.VBox;

import java.sql.Connection;

public class CreateReservationAgreementPane extends VBox {

    public CreateReservationAgreementPane(BorderPane root, Connection con) {
        Label title = new Label("Create Reservation + Agreement");
        title.setStyle("-fx-font-size: 20px; -fx-font-weight: bold;");

        TextField emailField = new TextField();
        emailField.setPromptText("Customer email");

        Button loadReservationsButton = new Button("Load Existing Reservations");
        TextArea reservationsArea = new TextArea();
        reservationsArea.setEditable(false);
        reservationsArea.setWrapText(true);
        reservationsArea.setPrefHeight(100);

        CheckBox walkInCheck = new CheckBox("Create walk-in reservation");
        TextField existingResIdField = new TextField();
        existingResIdField.setPromptText("Existing resID (ignored if walk-in checked)");

        TextField pickupDateField = new TextField();
        pickupDateField.setPromptText("Pickup Date (YYYY-MM-DD)");

        TextField returnDateField = new TextField();
        returnDateField.setPromptText("Return Date (YYYY-MM-DD)");

        Button loadBranchesButton = new Button("Load Branches");
        TextArea branchesArea = new TextArea();
        branchesArea.setEditable(false);
        branchesArea.setWrapText(true);
        branchesArea.setPrefHeight(90);

        TextField branchIdField = new TextField();
        branchIdField.setPromptText("Branch ID");

        Button loadEmployeesButton = new Button("Load Employees for Branch");
        TextArea employeesArea = new TextArea();
        employeesArea.setEditable(false);
        employeesArea.setWrapText(true);
        employeesArea.setPrefHeight(90);

        TextField employeeIdField = new TextField();
        employeeIdField.setPromptText("Employee ID");

        Button loadVehiclesButton = new Button("Load Available Vehicles");
        TextArea vehiclesArea = new TextArea();
        vehiclesArea.setEditable(false);
        vehiclesArea.setWrapText(true);
        vehiclesArea.setPrefHeight(100);

        TextField vinField = new TextField();
        vinField.setPromptText("Vehicle VIN");

        TextField contractIdField = new TextField();
        contractIdField.setPromptText("Agreement ID");

        TextField planTypeField = new TextField();
        planTypeField.setPromptText("Plan Type (Daily/Weekly/Monthly)");

        TextField totalCostField = new TextField();
        totalCostField.setPromptText("Total Cost");

        Button submitButton = new Button("Create Reservation + Agreement");
        Button backButton = new Button("Back");

        TextArea resultArea = new TextArea();
        resultArea.setEditable(false);
        resultArea.setWrapText(true);
        resultArea.setPrefHeight(140);

        loadReservationsButton.setOnAction(e -> {
            String email = emailField.getText().trim();
            reservationsArea.setText(GUIOptions.getExistingReservations(con, email));
        });

        loadBranchesButton.setOnAction(e -> {
            branchesArea.setText(GUIOptions.getBranches(con));
        });

        loadEmployeesButton.setOnAction(e -> {
            try {
                int branchID = Integer.parseInt(branchIdField.getText().trim());
                employeesArea.setText(GUIOptions.getEmployeesForBranch(con, branchID));
            } catch (NumberFormatException ex) {
                employeesArea.setText("Please enter a valid branch ID.");
            }
        });

        loadVehiclesButton.setOnAction(e -> {
            try {
                int branchID = Integer.parseInt(branchIdField.getText().trim());
                vehiclesArea.setText(GUIOptions.getAvailableVehiclesForBranch(con, branchID));
            } catch (NumberFormatException ex) {
                vehiclesArea.setText("Please enter a valid branch ID.");
            }
        });

        submitButton.setOnAction(e -> {
            try {
                String email = emailField.getText().trim();
                boolean createWalkIn = walkInCheck.isSelected();

                int chosenResID = existingResIdField.getText().trim().isEmpty()
                        ? 0
                        : Integer.parseInt(existingResIdField.getText().trim());

                String pickupDate = pickupDateField.getText().trim();
                String returnDate = returnDateField.getText().trim();

                int branchID = Integer.parseInt(branchIdField.getText().trim());
                int eID = Integer.parseInt(employeeIdField.getText().trim());
                String vin = vinField.getText().trim();
                int contractID = Integer.parseInt(contractIdField.getText().trim());
                String planType = planTypeField.getText().trim();
                double totalCost = Double.parseDouble(totalCostField.getText().trim());

                String result = GUIOptions.createReservationAgreement(
                        con, email, chosenResID, createWalkIn, pickupDate, returnDate,
                        branchID, eID, vin, contractID, planType, totalCost
                );

                resultArea.setText(result);

            } catch (NumberFormatException ex) {
                resultArea.setText("Please check numeric fields: reservation ID, branch ID, employee ID, agreement ID, and total cost.");
            }
        });

        backButton.setOnAction(e -> root.setCenter(new HomeScreen(root, con)));

        setSpacing(10);
        setPadding(new Insets(20));
        setAlignment(Pos.CENTER);

        emailField.setMaxWidth(350);
        existingResIdField.setMaxWidth(350);
        pickupDateField.setMaxWidth(350);
        returnDateField.setMaxWidth(350);
        branchIdField.setMaxWidth(350);
        employeeIdField.setMaxWidth(350);
        vinField.setMaxWidth(350);
        contractIdField.setMaxWidth(350);
        planTypeField.setMaxWidth(350);
        totalCostField.setMaxWidth(350);

        reservationsArea.setMaxWidth(700);
        branchesArea.setMaxWidth(700);
        employeesArea.setMaxWidth(700);
        vehiclesArea.setMaxWidth(700);
        resultArea.setMaxWidth(700);

        getChildren().addAll(
                title,
                emailField,
                loadReservationsButton,
                reservationsArea,
                walkInCheck,
                existingResIdField,
                pickupDateField,
                returnDateField,
                loadBranchesButton,
                branchesArea,
                branchIdField,
                loadEmployeesButton,
                employeesArea,
                employeeIdField,
                loadVehiclesButton,
                vehiclesArea,
                vinField,
                contractIdField,
                planTypeField,
                totalCostField,
                submitButton,
                backButton,
                resultArea
        );
    }
}
