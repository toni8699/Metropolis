import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.control.TextArea;
import javafx.scene.layout.BorderPane;
import javafx.scene.layout.VBox;

import java.sql.Connection;

public class RevenuePane extends VBox {

    public RevenuePane(BorderPane root, Connection con) {
        Label title = new Label("Revenue by Area and Vehicle Class");
        title.setStyle("-fx-font-size: 20px; -fx-font-weight: bold;");

        Button runButton = new Button("Run Revenue Report");
        Button backButton = new Button("Back");

        TextArea resultArea = new TextArea();
        resultArea.setEditable(false);
        resultArea.setWrapText(true);
        resultArea.setPrefHeight(350);

        runButton.setOnAction(e -> {
            String result = GUIOptions.revenueByAreaAndClass(con);
            resultArea.setText(result);
        });

        backButton.setOnAction(e -> {
            root.setCenter(new HomeScreen(root, con));
        });

        setSpacing(12);
        setPadding(new Insets(20));
        setAlignment(Pos.CENTER);

        runButton.setPrefWidth(200);
        backButton.setPrefWidth(200);
        resultArea.setMaxWidth(750);

        getChildren().addAll(
                title,
                runButton,
                backButton,
                resultArea
        );
    }
}
