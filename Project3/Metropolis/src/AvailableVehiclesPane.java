import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.control.TextArea;
import javafx.scene.layout.BorderPane;
import javafx.scene.layout.VBox;

import java.sql.Connection;

public class AvailableVehiclesPane extends VBox {

    public AvailableVehiclesPane(BorderPane root, Connection con) {
        Label title = new Label("Available Vehicles by Area");
        title.setStyle("-fx-font-size: 20px; -fx-font-weight: bold;");

        Button runButton = new Button("Run Availability Report");
        Button backButton = new Button("Back");

        TextArea resultArea = new TextArea();
        resultArea.setEditable(false);
        resultArea.setWrapText(true);
        resultArea.setPrefHeight(350);

        runButton.setOnAction(e -> {
            String result = GUIOptions.availableVehiclesByArea(con);
            resultArea.setText(result);
        });

        backButton.setOnAction(e -> {
            root.setCenter(new HomeScreen(root, con));
        });

        setSpacing(12);
        setPadding(new Insets(20));
        setAlignment(Pos.CENTER);

        runButton.setPrefWidth(220);
        backButton.setPrefWidth(220);
        resultArea.setMaxWidth(750);

        getChildren().addAll(
                title,
                runButton,
                backButton,
                resultArea
        );
    }
}
