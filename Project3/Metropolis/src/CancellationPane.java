import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.control.TextArea;
import javafx.scene.control.TextField;
import javafx.scene.layout.BorderPane;
import javafx.scene.layout.VBox;

import java.sql.Connection;

public class CancellationPane extends VBox {

    public CancellationPane(BorderPane root, Connection con) {
        Label title = new Label("Cancellation & Reassignment");
        title.setStyle("-fx-font-size: 20px; -fx-font-weight: bold;");

        Label vinLabel = new Label("Vehicle VIN:");
        TextField vinField = new TextField();
        vinField.setPromptText("Enter VIN of vehicle going to maintenance");

        Button runButton = new Button("Run Reassignment");
        Button backButton = new Button("Back");

        TextArea resultArea = new TextArea();
        resultArea.setEditable(false);
        resultArea.setWrapText(true);
        resultArea.setPrefHeight(300);

        runButton.setOnAction(e -> {
            String vin = vinField.getText().trim();

            if (vin.isEmpty()) {
                resultArea.setText("Please enter a VIN.");
                return;
            }

            String result = GUIOptions.cancellationReassignment(con, vin);
            resultArea.setText(result);
        });

        backButton.setOnAction(e -> {
            root.setCenter(new HomeScreen(root, con));
        });

        setSpacing(12);
        setPadding(new Insets(20));
        setAlignment(Pos.CENTER);

        runButton.setPrefWidth(180);
        backButton.setPrefWidth(180);
        vinField.setMaxWidth(300);
        resultArea.setMaxWidth(700);

        getChildren().addAll(
                title,
                vinLabel,
                vinField,
                runButton,
                backButton,
                resultArea
        );
    }
}
