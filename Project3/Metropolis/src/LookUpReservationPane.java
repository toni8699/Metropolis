import javafx.application.Application;
import javafx.geometry.Pos;
import javafx.scene.Scene;
import javafx.scene.control.TextField;
import javafx.scene.layout.BorderPane;
import javafx.scene.layout.VBox;
import javafx.stage.Stage;
import javafx.scene.control.*;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

public class LookUpReservationPane extends VBox {

    public LookUpReservationPane(BorderPane root, Connection con) {

        Label title = new Label("Look Up Reservation");
        title.setStyle("-fx-font-size: 20px; -fx-font-weight: bold;");

        // Set up text field to enter email
        TextField emailField = new TextField();
        emailField.setPromptText("Enter Customer Email");
        TextArea resultArea = new TextArea();

        // Declare Buttons
        Button searchButton = new Button("Search");
        Button backButton = new Button("Back");

        // Button actions
        backButton.setOnAction(e -> {
            root.setCenter(new HomeScreen(root, con));
        });

        searchButton.setOnAction(e -> {
            String email = emailField.getText().trim();
            String result = GUIOptions.lookupCustomerReservation(con, email);
            resultArea.setText(result);
        });

        // Stylistic Tweaks
        backButton.setPrefWidth(200);
        searchButton.setPrefWidth(200);
        emailField.setMaxWidth(300);
        resultArea.setMaxWidth(700);
        resultArea.setPrefHeight(300);

        setSpacing(10);
        setAlignment(Pos.CENTER);

        getChildren().addAll(title, emailField, searchButton, backButton, resultArea);

    }

}
