from collections import Counter
import csv
from datetime import datetime
import json
import os
from pathlib import Path
import time


# 1.3 ლოგირების ფუნქცია
def log(message):
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)
    log_file = output_dir / "log.txt"
    with open(log_file, "a", encoding="utf-8") as f:
        timestamp = datetime.now().isoformat()
        f.write(f"[{timestamp}] {message}\n")


# 4.1 საკუთარი კონტექსტ-მენეჯერი Timer
class Timer:

    def __init__(self, name):
        self.name = name
        self.start_time = None

    def __enter__(self):
        print(f"START {self.name}")
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.perf_counter() - self.start_time
        if exc_type is None:
            print(f"FINISH {self.name} in {elapsed:.4f} seconds")
        else:
            print(
                f"FAILED {self.name}: {exc_type.__name__} after {elapsed:.4f} seconds"
            )
            # დაბრუნება False-ის (ან არაფრის, რადგან ნაგულისხმევად None იგულისხმება, რაც False-ია)
            # ნიშნავს, რომ შეცდომა არ „გაიყლაპება“ და ზემოთ გადაიცემა.
            return False


# ნაწილი 1.1: საქაღალდის შექმნა და ფაილის შემოწმება
def setup_environment():
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = Path("data") / "employees.csv"
    if not csv_path.exists():
        print(
            "შეცდომა: data/employees.csv ფაილი არ არსებობს! გთხოვთ, შეამოწმოთ ბილიკი."
        )
        log("CRITICAL: data/employees.csv არ მოიძებნა. პროგრამა შეწყდა.")
        exit(1)
    else:
        print(f"ფაილის აბსოლუტური ბილიკი: {csv_path.resolve()}")
        log(f"ფაილი ნაპოვნია: {csv_path.resolve()}")

    return csv_path


# ნაწილი 1.2: ფაილის ასლის შექმნა
def backup_file(src, dst):
    line_count = 0
    with open(src, "r", encoding="utf-8", newline="") as f_src, open(
        dst, "w", encoding="utf-8", newline=""
    ) as f_dst:
        for line in f_src:
            f_dst.write(line)
            line_count += 1
    return line_count


# ნაწილი 1.4: Lock ფაილის შექმნა რეჟიმით 'x'
def create_lock_file():
    lock_path = Path("output") / "lock.txt"
    try:
        with open(lock_path, "x", encoding="utf-8") as f:
            f.write(datetime.now().isoformat())
        log("Lock ფაილი წარმატებით შეიქმნა.")
    except FileExistsError:
        print("ანგარიში უკვე შექმნილია")
        log("Lock ფაილი უკვე არსებობს (განმეორებითი გაშვება).")


# ნაწილი 2.1 & 2.2 & 2.3 & 2.4: CSV ანალიზი და დამუშავება
def process_csv_reports(csv_path):
    # 2.1 csv.reader-ით დაბეჭდვა
    print("\n--- 2.1 CSV Reader შედეგები ---")
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        print("სათაური:", header)

        first_three = []
        rows = []
        for row in reader:
            rows.append(row)
            if len(first_three) < 3:
                first_three.append(row)

        print("პირველი 3 თანამშრომელი:")
        for emp in first_three:
            print(emp)
        print("ჩანაწერების რაოდენობა (სათაურის გარეშე):", len(rows))

    # 2.2 csv.DictReader-ით ანალიზი
    dept_counts = Counter()
    dept_salaries = {}
    active_count = 0
    inactive_count = 0
    all_employees = []

    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        dict_reader = csv.DictReader(f)
        for row in dict_reader:
            dept = row["department"]
            salary = int(row["salary"])
            is_active_bool = row["is_active"] == "True"

            # აქტიურობა
            if is_active_bool:
                active_count += 1
            else:
                inactive_count += 1

            # დეპარტამენტი
            dept_counts[dept] += 1
            if dept not in dept_salaries:
                dept_salaries[dept] = []
            dept_salaries[dept].append(salary)

            # სია მაღალანაზღაურებადებისთვის და მაღალი ხელფასებისთვის
            all_employees.append(
                {
                    "id": row["id"],
                    "first_name": row["first_name"],
                    "last_name": row["last_name"],
                    "full_name": f"{row['first_name']} {row['last_name']}",
                    "department": dept,
                    "salary": salary,
                    "is_active": is_active_bool,
                }
            )

    print("\n--- 2.2 DictReader სტატისტიკა ---")
    print(
        f"ჩანაწერები / აქტიური / არააქტიური: {len(all_employees)} / {active_count} / {inactive_count}"
    )

    dept_stats_list = []
    print("დეპარტამენტები (თანამშრომლები და საშუალო ხელფასი):")
    for dept, count in dept_counts.items():
        avg_sal = sum(dept_salaries[dept]) / count
        print(f"{dept}: თანამშრომლები {count}, საშუალო ხელფასი {avg_sal:.2f}")
        dept_stats_list.append(
            {
                "department": dept,
                "employee_count": count,
                "avg_salary": round(avg_sal, 2),
            }
        )

    # TOP 3 აქტიური თანამშრომელი ხელფასით
    active_employees = [e for e in all_employees if e["is_active"]]
    top_3_active = sorted(
        active_employees, key=lambda x: x["salary"], reverse=True
    )[:3]
    print("TOP 3 აქტიური ხელფასით:")
    for emp in top_3_active:
        print(f"{emp['full_name']} {emp['salary']}")

    # 2.3 csv.DictWriter - დეპარტამენტის სტატისტიკის ჩაწერა (დალაგებული საშუალო ხელფასის კლებადობით)
    dept_stats_list.sort(key=lambda x: x["avg_salary"], reverse=True)
    stats_path = Path("output") / "department_stats.csv"
    with open(stats_path, "w", encoding="utf-8", newline="") as f:
        fieldnames = ["department", "employee_count", "avg_salary"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(dept_stats_list)

    # 2.4 csv.writer - მაღალანაზღაურებადი აქტიურები (>= 5000)
    high_earners = [
        e for e in active_employees if e["salary"] >= 5000
    ]  # ან ზოგადად ყველა აქტიური 5000+
    # პირობაში წერია: "ყველა აქტიური თანამშრომლისთვის, რომლის ხელფასიც 5000 ან მეტია"
    high_earners_path = Path("output") / "high_earners.csv"
    with open(high_earners_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "full_name", "department", "salary"])
        for emp in high_earners:
            writer.writerow(
                [
                    emp["id"],
                    emp["full_name"],
                    emp["department"],
                    emp["salary"],
                ]
            )

    log("მე-2 ნაწილის დამუშავება დასრულდა.")
    return dept_stats_list, all_employees


# ნაწილი 3.1: safe_read ფუნქცია
def safe_read(path):
    file_path = Path(path)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        log(f"FileNotFoundError: ფაილი ვერ მოიძებნა ბილიკზე {file_path}")
        return ""
    except UnicodeDecodeError:
        log(
            f"UnicodeDecodeError: დეკოდირების შეცდომა ფაილში {file_path}, იხსნება errors='replace'-ით."
        )
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()


# ნაწილი 3.2: ქალაქების სტატისტიკა და Counter
def process_cities(all_employees):
    cities = [emp.get("city", "Unknown") for emp in all_employees]
    # რადგან all_employees-ში city არ შეგვიყვანია DictReader-ისას, მოდით პირდაპირ ფაილიდან წავიკითხოთ ქალაქები:
    cities = []
    with open(
        Path("output") / "employees_backup.csv", "r", encoding="utf-8", newline=""
    ) as f:
        reader = csv.DictReader(f)
        for row in reader:
            cities.append(row["city"])

    city_counter = Counter(cities)
    top_3_cities = city_counter.most_common(3)

    print("\n--- 3.2 ქალაქების TOP 3 ---")
    for city, count in top_3_cities:
        print(f"{city}: {count}")

    cities_txt_path = Path("output") / "cities.txt"
    with open(cities_txt_path, "w", encoding="utf-8") as f:
        print(f"ქალაქების TOP 3:", file=f)
        for city, count in top_3_cities:
            print(f"{city}: {count}", file=f)

    log("ქალაქების სტატისტიკა დამუშავდა.")


# ნაწილი 3.3: უსაფრთხო JSON შენახვა
def save_json_safe(data, path):
    target_path = Path(path)
    tmp_path = Path(str(path) + ".tmp")

    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    os.replace(tmp_path, target_path)
    log(f"JSON ფაილი წარმატებით შეინახა და ჩანაცვლდა: {target_path}")


# ტესტირების დამხმარე ფუნქცია 3.1-ისთვის
def test_safe_read():
    output_dir = Path("output")
    # 1. არარსებული ფაილის ტესტი
    missing_file = output_dir / "missing.txt"
    res1 = safe_read(missing_file)
    print("safe_read არარსებულზე:", repr(res1))

    # 2. დაზიანებული ფაილის ტესტი (ბინარული ჩაწერა)
    broken_file = output_dir / "broken.txt"
    with open(broken_file, "wb") as f:
        f.write(bytes([99, 97, 102, 233, 32, 255]))
    res2 = safe_read(broken_file)
    print("safe_read დაზიანებულზე (replace):", repr(res2))


def main():
    # 1.3 ლოგი: დასაწყისი
    log("პროგრამა დაიწყო.")

    # 1.1 გარემოს მომზადება
    csv_path = setup_environment()

    # 1.2 ბექაპი
    backup_path = Path("output") / "employees_backup.csv"
    lines_copied = backup_file(csv_path, backup_path)
    print(f"ბექაპი დასრულდა. გადაკოპირებული ხაზების რაოდენობა: {lines_copied}")
    log(f"შეიქმნა ბექაპი, ხაზების რაოდენობა: {lines_copied}")

    # 1.4 Lock ფაილი
    create_lock_file()
    log("ნაწილი 1 დასრულდა.")

    # ნაწილი 2: CSV ანალიზი Timer კონტექსტ-მენეჯერით
    with Timer("CSV ანალიზი"):
        dept_stats, all_employees = process_csv_reports(backup_path)

    log("ნაწილი 2 დასრულდა.")

    # ნაწილი 3: შეცდომები და რეალური პატერნები
    test_safe_read()
    process_cities(all_employees)

    # 3.3 დეპარტამენტის სტატისტიკის JSON-ში შენახვა
    summary_json_path = Path("output") / "summary.json"
    save_json_safe(dept_stats, summary_json_path)
    log("ნაწილი 3 დასრულდა.")

    # ნაწილი 4.2: Timer დემონსტრაცია ZeroDivisionError-ზე
    print("\n--- 4.2 Timer შეცდომის დემონსტრაცია ---")
    try:
        with Timer("test"):
            x = 1 / 0
    except ZeroDivisionError:
        print("შეცდომა წარმატებით დაიჭირა try/except ბლოკმა გარეთ!")

    # 1.3 ლოგი: ბოლო
    log("პროგრამა წარმატებით დასრულდა.")
    print("\nპროგრამამ წარმატებით დაასრულა მუშაობა!")


if __name__ == "__main__":
    main()


# =====================================================================
# ნაწილი 5: თეორიული კითხვები (პასუხები)
# =====================================================================
# 1. რატომ ითვლება რეჟიმი w სახიფათოდ და რომელ რეჟიმს გამოიყენებდით,
#    რომ არსებული ფაილი არ წაიშალოს?
#    პასუხი: რეჟიმი 'w' (write) სახიფათოა იმის გამო, რომ თუ მითითებული სახელით
#    ფაილი უკვე არსებობს, ის ავტომატურად სრულად იშლება და თავიდან იქმნება
#    ცარიელი ფაილი, რის გამოც ძველი მონაცემები სამუდამოდ იკარგება. იმისათვის,
#    რომ არსებული ფაილი არ წაიშალოს და მონაცემები მივამატოთ, გამოიყენება
#    რეჟიმი 'a' (append), ხოლო თუ გვინდა როგორც წაკითხვა, ისე ჩაწერა ისე,
#    რომ ძველი ინფორმაცია არ განადგურდეს, ვიყენებთ 'r+' ან 'a+' რეჟიმებს.
#
# 2. რას აკეთებს __exit__() და რატომ აჯობებს with ხელით close()-ს?
#    პასუხი: __exit__() მეთოდი არის კონტექსტ-მენეჯერის დამმახსოვრებელი ნაწილი,
#    რომელიც ავტომატურად გამოიძახება with ბლოკიდან გასვლისას (მიუხედავად იმისა,
#    კოდმა წარმატებით დაასრულა მუშაობა თუ შეცდომა/გამონაკლისი მოხდა). ის უზრუნველყოფს
#    რესურსების (ფაილების, კავშირების) სუფთა და უსაფრთხო დახურვას. with ჯობია
#    ხელით close()-ს, რადგან პროგრამისტს ხშირად ავიწყდება close()-ის გამოძახება
#    განსაკუთრებით მაშინ, როცა კოდში შეცდომა (exception) ამოვარდება, რამაც შეიძლება
#    მონაცემთა დაკარგვა (Buffer-ის ჩაუწერლობა) და რესურსების გაჟონვა გამოიწვიოს.
#
# 3. რატომ არ უნდა დავამუშაოთ CSV split(',')-ით? მოიყვანეთ მაგალითი.
#    პასუხი: CSV ფაილებში მონაცემები შეიძლება შეიცავდეს მძიმეებს თავად ტექსტის შიგნით
#    (მაგალითად, მისამართებში ან სახელებში, რომლებიც ბრჭყალებშია სრულად მოქცეული:
#    "Tbilisi, Chavchavadze 1"). თუ ამას მარტივი split(',')-ით დავამუშავებთ,
#    პროგრამა მძიმეს აღიქვამს როგორც სვეტების გამყოფს და არასწორად დაყოფს მონაცემებს
#    სვეტებად. csv მოდული ავტომატურად ითვალისწინებს ბრჭყალებს და მსგავს ნიუანსებს,
#    ხოლო split(',') ამას ვერ აკეთებს.