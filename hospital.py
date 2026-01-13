#Hospital Patient Management System
import csv
import json
import os

PATIENT_FILE = "patients.csv"
LOG_FILE = "audit.log"

#audit log function
def log_action(action, message, date="", time="", doctor="", patient_id=""):
    line = f"{action}|{date}|{time}|{doctor}|{patient_id}|{message}\n"
    try:
        with open(LOG_FILE, "a") as f:   
            f.write(line)
    except Exception as e:
        print("Log write failed:", e)

# DATA LOADING
def load_patients_from_csv():
   
    patients = {}

    if not os.path.exists(PATIENT_FILE):
        print("patients.csv not found. Starting with no patients.")
        return patients

    try:
        with open(PATIENT_FILE, "r") as f:   
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    pid = int(row.get("id", "").strip())
                except ValueError:
                    continue  

                patients[pid] = {
                    "name": row.get("name", "").strip(),
                    "diagnosis": row.get("diagnosis", "").strip(),
                    "medications": row.get("medications", "").strip(),
                }
    except Exception as e:
        print("Error reading patients.csv:", e)

    return patients

#ADD PATIENT
def add_new_patient(patients):
    try:
        pid = int(input("Enter new patient ID: ").strip())
    except ValueError:
        print("Invalid ID. Must be a number.")
        return

    if pid in patients:
        print("This patient ID already exists.")
        return

    name = input("Enter patient name: ").strip()
    diagnosis = input("Enter diagnosis: ").strip()
    medications = input("Enter medications: ").strip()

    patients[pid] = {
        "name": name,
        "diagnosis": diagnosis,
        "medications": medications,
    }

    file_exists = os.path.exists(PATIENT_FILE)

    try:
        with open(PATIENT_FILE, "a", newline="") as f:  
            fieldnames = ["id", "name", "diagnosis", "medications"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()
            writer.writerow({
                "id": pid,
                "name": name,
                "diagnosis": diagnosis,
                "medications": medications
            })

        msg = f"New patient added: ID {pid}, Name {name}"
        print(msg)
        log_action("ADD_PATIENT", msg, patient_id=str(pid))
    except Exception as e:
        print("Failed to write to patients.csv:", e)
        log_action("ERROR", f"Failed to add patient: {e}", patient_id=str(pid))

def has_overlap(appointments, date, time, doctor):
    for d, t, doc, _ in appointments:
        if d == date and t == time and doc == doctor:
            return True
    return False

#SCHEDULE APPOINTMENT
def schedule_appointment(patients, appointments):
    try:
        pid = int(input("Enter patient ID: ").strip())
    except ValueError:
        print("Invalid patient ID.")
        return

    if pid not in patients:
        msg = f"Appointment failed: patient ID {pid} not found."
        print(msg)
        log_action("ERROR", msg, patient_id=str(pid))
        return

    date = input("Enter date (YYYY-MM-DD): ").strip()
    time = input("Enter time (HH:MM): ").strip()
    doctor = input("Enter doctor name: ").strip()

    if has_overlap(appointments, date, time, doctor):
        msg = f"Overlap: {date} {time} with {doctor} already booked."
        print(msg)
        log_action("ERROR", msg, date, time, doctor, str(pid))
        return

    appt = (date, time, doctor, pid)
    appointments.append(appt)

    msg = f"Appointment scheduled for ID {pid} on {date} at {time} with {doctor}"
    print(msg)
    log_action("SCHEDULE", msg, date, time, doctor, str(pid))

#CANCEL APPOINTMENT
def cancel_appointment(appointments):
    try:
        pid = int(input("Enter patient ID: ").strip())
    except ValueError:
        print("Invalid patient ID.")
        return

    date = input("Enter date (YYYY-MM-DD): ").strip()
    time = input("Enter time (HH:MM): ").strip()
    doctor = input("Enter doctor name: ").strip()

    appt = (date, time, doctor, pid)

    if appt in appointments:
        appointments.remove(appt)
        msg = f"Appointment canceled for ID {pid} on {date} at {time} with {doctor}"
        print(msg)
        log_action("CANCEL", msg, date, time, doctor, str(pid))
    else:
        msg = "Cancel failed: appointment not found."
        print(msg)
        log_action("ERROR", msg, date, time, doctor, str(pid))

#VIEW APPOINTMENTS
def view_appointments(patients, appointments):
    print("\n--- Current Appointments ---")
    if not appointments:
        print("No appointments.")
    else:
        for date, time, doctor, pid in appointments:
            name = patients.get(pid, {}).get("name", "Unknown")
            print(f"{date} {time} | {doctor} | ID {pid} ({name})")

#REPORT
def generate_treatment_report(patients):
    by_diagnosis = {}

    for pid, info in patients.items():
        diag = info.get("diagnosis", "Unknown")
        by_diagnosis.setdefault(diag, []).append((pid, info.get("name", "")))

    print("\n=== Treatment Report (by diagnosis) ===")
    for diag, plist in by_diagnosis.items():
        print(f"\nDiagnosis: {diag}")
        for pid, name in plist:
            print(f"  ID: {pid}, Name: {name}")

#BACKUP
def backup_to_json(patients, appointments):
    filename = input("Enter backup filename (e.g. backup.json): ").strip()
    if not filename:
        print("Filename cannot be empty.")
        return

    data = {
        "patients": patients,
        "appointments": [list(a) for a in appointments]
    }

    try:
        with open(filename, "w") as f:    
            json.dump(data, f, indent=2)
        msg = f"Backup saved to {filename}"
        print(msg)
        log_action("BACKUP", msg)
    except Exception as e:
        msg = f"Backup failed: {e}"
        print(msg)
        log_action("ERROR", msg)

#load Backup
def load_from_backup(patients, appointments):
    filename = input("Enter backup filename to load: ").strip()
    if not filename:
        print("Filename cannot be empty.")
        return

    if not os.path.exists(filename):
        msg = f"Backup file {filename} does not exist."
        print(msg)
        log_action("ERROR", msg)
        return

    try:
        with open(filename, "r") as f:   
            data = json.load(f)
    except json.JSONDecodeError:
        msg = f"Backup file {filename} is corrupted. Data not changed."
        print(msg)
        log_action("ERROR", msg)
        return
    except Exception as e:
        msg = f"Error reading backup {filename}: {e}"
        print(msg)
        log_action("ERROR", msg)
        return

    patients.clear()
    patients.update(data.get("patients", {}))

    appointments.clear()
    for item in data.get("appointments", []):
        if len(item) == 4:
            date, time, doctor, pid = item
            appointments.append((date, time, doctor, pid))

    msg = f"Data loaded from {filename}"
    print(msg)
    log_action("LOAD_BACKUP", msg)

#ROLLBACK
def rollback_last_3_actions(appointments):
    if not os.path.exists(LOG_FILE):
        print("No log file found. Nothing to rollback.")
        return

    try:
        with open(LOG_FILE, "r") as f:   
            lines = f.readlines()
    except Exception as e:
        print("Could not read audit.log:", e)
        return

    actions = []
    for line in reversed(lines):
        parts = line.strip().split("|", 5)
        if len(parts) < 6:
            continue
        action, date, time, doctor, pid, msg = parts
        if action in ("SCHEDULE", "CANCEL"):
            actions.append((action, date, time, doctor, pid))
            if len(actions) == 3:
                break

    if not actions:
        print("No SCHEDULE/CANCEL actions to rollback.")
        return

    print(f"Rolling back last {len(actions)} actions:")

    for action, date, time, doctor, pid in actions:
        try:
            pid_int = int(pid)
        except ValueError:
            continue

        appt = (date, time, doctor, pid_int)

        if action == "SCHEDULE":
            if appt in appointments:
                appointments.remove(appt)
                print("  Rolled back SCHEDULE:", appt)
                log_action("ROLLBACK", "Undo scheduled appointment",
                           date, time, doctor, pid)
        elif action == "CANCEL":
            if appt not in appointments:
                appointments.append(appt)
                print("  Rolled back CANCEL:", appt)
                log_action("ROLLBACK", "Undo canceled appointment",
                           date, time, doctor, pid)
    print("Rollback complete.\n")

#main function
def main():
    patients = load_patients_from_csv()
    appointments = []  

    while True:
        print(" Hospital Patient Management System ")
        print("1. Add new patient")
        print("2. Schedule appointment")
        print("3. Cancel appointment")
        print("4. View appointments")
        print("5. Treatment report (grouped by diagnosis)")
        print("6. Backup to JSON")
        print("7. Load from backup JSON")
        print("8. Rollback last 3 actions")
        print("9. Exit")

        choice = input("Enter choice: ").strip()

        if choice == "1":
            add_new_patient(patients)
        elif choice == "2":
            schedule_appointment(patients, appointments)
        elif choice == "3":
            cancel_appointment(appointments)
        elif choice == "4":
            view_appointments(patients, appointments)
        elif choice == "5":
            generate_treatment_report(patients)
        elif choice == "6":
            backup_to_json(patients, appointments)
        elif choice == "7":
            load_from_backup(patients, appointments)
        elif choice == "8":
            rollback_last_3_actions(appointments)
        elif choice == "9":
            print("Thank you for using the Hospital Patient Management System.")
            break
        else:
            print("Invalid choice.\n")


main()
