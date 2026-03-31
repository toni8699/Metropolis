import javafx.geometry.Pos;
import javafx.scene.control.*;
import javafx.scene.layout.*;

import java.sql.Connection;

public class RewardPane extends VBox {

    public RewardPane(BorderPane root, Connection con) {

        Label title = new Label("Reward Top Employees");
        title.setStyle("-fx-font-size: 20px; -fx-font-weight: bold;");

        Button runButton = new Button("Run Reward");
        TextArea resultArea = new TextArea();
        Button backButton = new Button("Back");
        runButton.setPrefWidth(200);
        backButton.setPrefWidth(200);
        resultArea.setMaxWidth(700);
        resultArea.setMaxHeight(500);

        runButton.setOnAction(e -> {
            String result = GUIOptions.rewardTopEmployees(con);
            resultArea.setText(result);
        });

        backButton.setOnAction(e -> {
            root.setCenter(new HomeScreen(root, con));
        });

        setSpacing(10);
        setAlignment(Pos.CENTER);

        getChildren().addAll(title, runButton, backButton, resultArea);
    }
}
