import javafx.geometry.Pos;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.control.TextArea;
import javafx.scene.control.TextField;
import javafx.scene.layout.BorderPane;
import javafx.scene.layout.VBox;

import java.sql.Connection;

public class AddCustomerPane extends VBox {

    public AddCustomerPane(BorderPane root, Connection con) {

        Label title = new Label("Add Customer");
        title.setStyle("-fx-font-size: 20px; -fx-font-weight: bold;");

        TextField emailField = new TextField();
        emailField.setPromptText("Enter email");
        emailField.setMaxWidth(300);

        TextField nameField = new TextField();
        nameField.setPromptText("Enter name");
        nameField.setMaxWidth(300);

        TextField addressField = new TextField();
        addressField.setPromptText("Enter address");
        addressField.setMaxWidth(300);

        TextField expiryField = new TextField();
        expiryField.setPromptText("Enter license expiry (YYYY-MM-DD)");
        expiryField.setMaxWidth(300);

        Button addButton = new Button("Add Customer");
        Button backButton = new Button("Back");

        TextArea resultArea = new TextArea();
        resultArea.setEditable(false);
        resultArea.setWrapText(true);
        resultArea.setMaxHeight(300);
        resultArea.setMaxWidth(700);


        addButton.setOnAction(e -> {
            String email = emailField.getText().trim();
            String name = nameField.getText().trim();
            String address = addressField.getText().trim();
            String expiry = expiryField.getText().trim();

            String result = GUIOptions.addCustomer(con, email, name, address, expiry);
            resultArea.setText(result);
        });

        backButton.setOnAction(e -> {
            root.setCenter(new HomeScreen(root, con));
        });

        setSpacing(12);
        setAlignment(Pos.CENTER);

        getChildren().addAll(
                title,
                emailField,
                nameField,
                addressField,
                expiryField,
                addButton,
                backButton,
                resultArea
        );
    }
}
