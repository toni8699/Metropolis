import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.control.TextArea;
import javafx.scene.control.TextField;
import javafx.scene.layout.BorderPane;
import javafx.scene.layout.VBox;

import java.sql.Connection;

public class SelectAllPane extends VBox {

    public SelectAllPane(BorderPane root, Connection con) {
        Label title = new Label("SELECT ALL");
        title.setStyle("-fx-font-size: 20px; -fx-font-weight: bold;");

        TextField tableField = new TextField();
        tableField.setPromptText("Table name");
        tableField.setMaxWidth(350);

        Button runButton = new Button("Run SELECT");
        Button backButton = new Button("Back");
        runButton.setPrefWidth(200);
        backButton.setPrefWidth(200);

        TextArea resultArea = new TextArea();
        resultArea.setEditable(false);
        resultArea.setWrapText(false);
        resultArea.setPrefHeight(350);
        resultArea.setMaxWidth(750);

        runButton.setOnAction(e -> {
            String result = GUIOptions.selectAllFromTable(con, tableField.getText());
            resultArea.setText(result);
        });

        backButton.setOnAction(e -> root.setCenter(new HomeScreen(root, con)));

        setSpacing(12);
        setPadding(new Insets(20));
        setAlignment(Pos.CENTER);

        getChildren().addAll(
                title,
                tableField,
                runButton,
                backButton,
                resultArea
        );
    }
}
