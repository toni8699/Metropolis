import java.net.URI;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

final class Database {

    private Database() {
    }

    static Connection connect() throws SQLException {
        loadDriver();

        String jdbcUrl = env("JDBC_URL");
        String user = env("DB_USER");
        String password = env("DB_PASSWORD");

        if (jdbcUrl == null) {
            jdbcUrl = jdbcUrlFromDatabaseUrl();
        }
        if (user == null) {
            user = userFromDatabaseUrl();
        }
        if (password == null) {
            password = passwordFromDatabaseUrl();
        }

        if (jdbcUrl == null) {
            throw new SQLException(
                    "Missing database config. Set DATABASE_URL (Neon) or JDBC_URL, DB_USER, and DB_PASSWORD.");
        }

        if (user != null && password != null) {
            return DriverManager.getConnection(jdbcUrl, user, password);
        }
        return DriverManager.getConnection(jdbcUrl);
    }

    private static void loadDriver() throws SQLException {
        try {
            Class.forName("org.postgresql.Driver");
        } catch (ClassNotFoundException e) {
            throw new SQLException(
                    "PostgreSQL JDBC driver not found. Run backend/scripts/build.sh to download it.", e);
        }
    }

    private static String jdbcUrlFromDatabaseUrl() throws SQLException {
        String databaseUrl = env("DATABASE_URL");
        if (databaseUrl == null) {
            return null;
        }

        URI uri = URI.create(databaseUrl.replace("postgres://", "postgresql://"));
        String host = uri.getHost();
        int port = uri.getPort() > 0 ? uri.getPort() : 5432;
        String path = uri.getPath();
        if (path == null || path.isEmpty() || "/".equals(path)) {
            throw new SQLException("DATABASE_URL must include a database name.");
        }
        String dbName = path.startsWith("/") ? path.substring(1) : path;

        StringBuilder jdbc = new StringBuilder("jdbc:postgresql://")
                .append(host)
                .append(":")
                .append(port)
                .append("/")
                .append(dbName);

        String query = uri.getQuery();
        if (query == null || query.isBlank()) {
            jdbc.append("?sslmode=require");
        } else if (!query.contains("sslmode=")) {
            jdbc.append("?").append(query).append("&sslmode=require");
        } else {
            jdbc.append("?").append(query);
        }
        return jdbc.toString();
    }

    private static String userFromDatabaseUrl() {
        String databaseUrl = env("DATABASE_URL");
        if (databaseUrl == null) {
            return null;
        }
        URI uri = URI.create(databaseUrl.replace("postgres://", "postgresql://"));
        if (uri.getUserInfo() == null) {
            return null;
        }
        String[] parts = uri.getUserInfo().split(":", 2);
        return decode(parts[0]);
    }

    private static String passwordFromDatabaseUrl() {
        String databaseUrl = env("DATABASE_URL");
        if (databaseUrl == null) {
            return null;
        }
        URI uri = URI.create(databaseUrl.replace("postgres://", "postgresql://"));
        if (uri.getUserInfo() == null) {
            return null;
        }
        String[] parts = uri.getUserInfo().split(":", 2);
        return parts.length > 1 ? decode(parts[1]) : "";
    }

    private static String env(String key) {
        String value = System.getenv(key);
        if (value == null || value.isBlank()) {
            return null;
        }
        return value.trim();
    }

    private static String decode(String value) {
        return URLDecoder.decode(value, StandardCharsets.UTF_8);
    }
}
