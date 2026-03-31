import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.control.TextArea;
import javafx.scene.layout.BorderPane;
import javafx.scene.layout.VBox;

import java.sql.Connection;

public class RelocationPlannerPane extends VBox {

    public RelocationPlannerPane(BorderPane root, Connection con) {
        Label title = new Label("Relocation Planner Simulation");
        title.setStyle("-fx-font-size: 20px; -fx-font-weight: bold;");

        Button runButton = new Button("Run Relocation Planner");
        Button backButton = new Button("Back");

        TextArea resultArea = new TextArea();
        resultArea.setEditable(false);
        resultArea.setWrapText(true);
        resultArea.setPrefHeight(380);

        runButton.setOnAction(e -> {
            String result = GUIOptions.relocationPlannerSimulation(con);
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
        resultArea.setMaxWidth(780);

        getChildren().addAll(title, runButton, backButton, resultArea);
    }
}
