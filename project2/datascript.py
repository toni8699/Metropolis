import random
from datetime import datetime, date, timedelta

customers = [
    ("mike.mccarthy", "Mike McCarthy", "10 Queen St, Montreal"),
    ("sara.goldman", "Sara Goldman", "45 King St, Toronto"),
    ("nina.carter", "Nina Carter", "120 Granville, Vancouver"),
    ("ethan.ross", "Ethan Ross", "62 3rd Ave, Calgary"),
    ("lisa.adjani", "Lisa Adjani", "420 Rideau, Ottawa"),
    ("alex.jones", "Alex Jones", "88 Elm St, Quebec City"),
    ("rosa.rivera", "Rosa Rivera", "2100 Saint Laurent, Montreal"),
    ("samir.khan", "Samir Khan", "19 Yonge St, Toronto"),
    ("ivy.norris", "Ivy Norris", "540 Howe St, Vancouver"),
    ("cole.lewis", "Cole Lewis", "33 Macleod Trail, Calgary")
]

models = ["Civic", "Accord", "Corolla", "Camry", "Escape", "CR-V", "Rogue", "F-150", "Sierra", "CX-5"]
makes = ["Honda", "Toyota", "Ford", "Nissan", "Mazda", "Chevrolet", "Kia", "Hyundai"]
statuses = ["Available", "Rented", "Maintenance", "Relocating"]
area_ids = [1, 2, 3, 4, 5]
class_ids = [10, 11, 12, 13, 14]
branches = [100, 101, 102, 103, 104]

def random_vin(i):
    return f"VIN{i:09d}XXX"

def random_date(start=date(2026, 3, 1), days=60):
    delta = timedelta(days=random.randint(0, days))
    base = datetime.combine(start + delta, datetime.min.time())
    return base + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))

print("-- Customers")
for email, name, addr in customers:
    expiry = random_date(date(2027, 1, 1), days=365)
    print(f"INSERT INTO Customer (email, name, address, license_expiry) VALUES ('{email}@example.com', '{name}', '{addr}', '{expiry.strftime('%Y-%m-%d')}');")

print("\n-- Vehicles")
for i in range(60):
    vin = random_vin(i + 1)
    license_plate = f"PL{random.randint(100, 999)}{random.choice('ABC')}"
    mileage = random.randint(5000, 90000)
    model = random.choice(models)
    make = random.choice(makes)
    status = random.choice(statuses)
    class_id = random.choice(class_ids)
    branch_id = random.choice(branches)
    print(f"INSERT INTO Vehicle (vin, license_plate, mileage, model, status, make, classID, branchID) VALUES ('{vin}', '{license_plate}', {mileage}, '{model}', '{status}', '{make}', {class_id}, {branch_id});")

print("\n-- Reservations & RentalPeriods")
reservation_base = 2000
for i in range(60):
    res_id = reservation_base + i
    cust = random.choice(customers)[0]
    book_dt = random_date(date(2026, 2, 15), days=45)
    print(f"INSERT INTO Reservation (resID, bookedAtTime, email) VALUES ({res_id}, '{book_dt.strftime('%Y-%m-%d %H:%M:%S')}', '{cust}@example.com');")
    pickup = random_date(book_dt.date() + timedelta(days=2), days=20)
    dropoff = pickup + timedelta(days=random.randint(1, 10))
    print(f"INSERT INTO RentalPeriod (resID, periodID, pickupDate, returnDate) VALUES ({res_id}, 1, '{pickup.strftime('%Y-%m-%d')}', '{dropoff.strftime('%Y-%m-%d')}');")

print("\n-- Agreements")
agreement_base = 5000
employee_ids = [200, 201, 202, 203, 204, 205, 206, 207, 208, 209]
vehicle_vins = [f"VIN{i:09d}XXX" for i in range(1, 61)]
for i in range(60):
    contract = agreement_base + i
    res_id = reservation_base + i
    vin = vehicle_vins[i]
    emp = random.choice(employee_ids)
    plan = random.choice(["Daily", "Weekly", "Monthly"])
    total = round(random.uniform(200, 3200), 2)
    print(f"INSERT INTO Agreement (contractID, planType, totalCost, eID, vin, resID) VALUES ({contract}, '{plan}', {total}, {emp}, '{vin}', {res_id});")

print("\n-- Relocations")
pairs = [(1, 2), (1, 3), (2, 4), (3, 5), (4, 5)]
for src, tgt in pairs:
    fee = random.randint(400, 800)
    print(f"INSERT INTO Relocation (sourceAreaID, targetAreaID, fee) VALUES ({src}, {tgt}, {fee});")