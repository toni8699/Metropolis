cat <<'EOF' > high_utilization.sql
CONNECT TO COMP421;

SELECT b.branchID,
       b.city,
       COUNT(DISTINCT v.vin) AS fleet_size,
       COUNT(DISTINCT r.resID) AS active_reservations,
       ROUND(100.0 * COUNT(DISTINCT r.resID) / NULLIF(COUNT(DISTINCT v.vin),0), 2) AS utilization_pct
FROM Branch b
JOIN Vehicle v ON v.branchID = b.branchID
LEFT JOIN Agreement a ON a.vin = v.vin
LEFT JOIN Reservation r ON r.resID = a.resID
GROUP BY b.branchID, b.city
HAVING COUNT(DISTINCT r.resID) >= 0.3 * COUNT(DISTINCT v.vin)
ORDER BY utilization_pct DESC;
EOF
