DELETE FROM Relocation;

INSERT INTO Relocation (sourceAreaID, targetAreaID, fee)
WITH base(a1, a2, fee) AS (
  VALUES
    (1, 2, 220.00),
    (1, 5, 260.00),
    (1, 6, 180.00),
    (2, 5, 210.00),
    (2, 6, 380.00),
    (5, 6, 300.00),
    (3, 4, 230.00),
    (2, 4, 700.00),
    (2, 3, 900.00),
    (1, 4, 780.00),
    (1, 3, 980.00),
    (5, 4, 760.00),
    (5, 3, 960.00),
    (6, 4, 820.00),
    (6, 3, 1020.00)
),
pairs(sourceAreaID, targetAreaID, fee) AS (
  SELECT a1, a2, fee FROM base
  UNION ALL
  SELECT a2, a1, fee FROM base
)
SELECT sourceAreaID, targetAreaID, fee
FROM pairs;