"""
Internship Project: Customer Support Ticket Quality Audit

What this program will do:
1) Load a CSV file of support tickets
2) Inspect the data
3) Clean messy values
4) Classify tickets using keyword rules
5) Flag low-quality tickets
6) Write summary results to files

"""

import pandas as pd


# 1) LOAD DATA
def load_data():
    df = pd.read_csv("tickets.csv")

    print("----- FIRST 10 ROWS -----")
    print(df.head(10))

    print("\n-----DATA SHAPE-----\n")
    print(df.shape)

    print("\n----- MISSING VALUES PER COLUMN -----")
    print(df.isna().sum())

    return df


# 2) REMOVE DUPLICATES
def remove_duplicates(df):
    before = len(df)

    df.drop_duplicates(inplace = True)

    after = len(df)

    print("Duplicates removed:", before - after)

    return df


# 3) CLEAN TEXT COLUMNS
def clean_text_columns(df):
    # Make sure we do not accidentally modify the original reference
    df = df.copy()

    # Clean priority column
    df["priority"] = df["priority"].astype(str).str.strip().str.title()

    # Clean status column
    df["status"] = df["status"].astype(str).str.strip().str.title()

    # Clean subject column
    df["subject"] = df["subject"].astype(str).str.strip()

    # Clean message column
    df["message"] = df["message"].astype(str).str.strip()

    return df


# 4) HANDLE MISSING VALUES
def handle_missing_values(df):
    df = df.copy()

    # Fill missing priority with "Low"
    df["priority"].fillna("Low", inplace=True)

    # Fill missing status with "Open"
    df["status"].fillna("Open", inplace=True)

    # Fill missing resolution time with median
    median_time = df["resolution_time_hours"].median()
    df["resolution_time_hours"].fillna(median_time, inplace=True)

    return df


# 5) CLEAN DATES
def clean_dates(df):
    df = df.copy()

    df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce")

    return df


# 6) ISSUE TYPE CLASSIFICATION
def classify_issues(df):
    """
    Classify each ticket into an issue type using keyword rules.
    """
    df = df.copy()

    billing_words = {"refund", "charge", "invoice", "payment"}
    technical_words = {"error", "bug", "crash", "login", "failed"}
    account_words = {"password", "email", "account", "verify"}
    delivery_words = {"delivery", "shipping", "late", "tracking"}

    issue_types = []

    for i in range(len(df)):
        # Combine subject and message
        text = df.loc[i, "subject"] + " " + df.loc[i, "message"]
        text = text.lower()

        issue = "Other"

        # Check billing
        for word in billing_words:
            if word in text:
                issue = "Billing"
                break

        # Check technical
        if issue == "Other":
            for word in technical_words:
                if word in text:
                    issue = "Technical"
                    break

        # Check account
        if issue == "Other":
            for word in account_words:
                if word in text:
                    issue = "Account"
                    break

        # Check delivery
        if issue == "Other":
            for word in delivery_words:
                if word in text:
                    issue = "Delivery"
                    break

        issue_types.append(issue)

    df["issue_type"] = issue_types

    return df


# 7) FLAG LOW-QUALITY TICKETS
def flag_tickets(df):
    df = df.copy()

    flags = []
    reasons = []

    for i in range(len(df)):
        message = str(df.loc[i, "message"])

        flag = False
        reason = ""

        # Rule 1: message too short
        if len(message) < 20:
            flag = True
            reason = "Message too short"

        # Rule 2: message is ALL CAPS
        elif message.isupper():
            flag = True
            reason = "Message in all caps"

        # Rule 3: excessive punctuation
        elif "!!!" in message or "???" in message:
            flag = True
            reason = "Excessive punctuation"

        flags.append(flag)
        reasons.append(reason)

    df["is_flagged"] = flags
    df["flag_reason"] = reasons

    return df



# 8) SUMMARY STATISTICS
def create_summary(df):
    summary = {}

    # Basic totals
    total_tickets = len(df)
    summary["total_tickets"] = total_tickets

    # Count flagged tickets (loop version)
    flagged_count = 0
    for i in range(len(df)):
        if df.loc[i, "is_flagged"] == True:
            flagged_count += 1
    summary["flagged_tickets"] = flagged_count

    # Flagged percentage
    if total_tickets > 0:
        summary["flagged_percent"] = (flagged_count / total_tickets) * 100
    else:
        summary["flagged_percent"] = 0

    # Average resolution time (simple mean using pandas)
    summary["average_resolution_time_hours"] = df["resolution_time_hours"].mean()

    # Average resolution time for flagged vs not flagged (two counters + sums)
    flagged_sum = 0
    flagged_n = 0
    not_flagged_sum = 0
    not_flagged_n = 0

    for i in range(len(df)):
        time_val = df.loc[i, "resolution_time_hours"]
        if df.loc[i, "is_flagged"] == True:
            flagged_sum += time_val
            flagged_n += 1
        else:
            not_flagged_sum += time_val
            not_flagged_n += 1

    if flagged_n > 0:
        summary["avg_resolution_flagged_hours"] = flagged_sum / flagged_n
    else:
        summary["avg_resolution_flagged_hours"] = "N/A"

    if not_flagged_n > 0:
        summary["avg_resolution_not_flagged_hours"] = not_flagged_sum / not_flagged_n
    else:
        summary["avg_resolution_not_flagged_hours"] = "N/A"

    # Count tickets per issue_type using a dictionary
    issue_counts = {}

    for i in range(len(df)):
        issue = df.loc[i, "issue_type"]

        if issue in issue_counts:
            issue_counts[issue] += 1
        else:
            issue_counts[issue] = 1

    # Put issue counts into summary (as separate lines)
    # This makes report.txt easy to read without needing advanced formatting.
    for issue in issue_counts:
        key = "issue_count_" + str(issue)
        summary[key] = issue_counts[issue]

    return summary


# 9) WRITE REPORT FILE
def write_report(summary):
    """
    Write summary information to outputs/report.txt.
    """
    f = open("outputs/report.txt", "w", encoding="utf-8")

    f.write("Customer Support Ticket Quality Audit Report\n")
    f.write("===========================================\n\n")

    for key in summary:
        f.write(f"{key}: {summary[key]}\n")

    f.close()


# 10) EXPORT CSV FILES
def export_files(df):
    # Export full cleaned dataset
    df.to_csv("outputs/tickets_cleaned.csv", index=False)

    # Export only flagged tickets
    flagged_rows = []

    for i in range(len(df)):
        if df.loc[i, "is_flagged"] == True:
            flagged_rows.append(i)

    flagged_df = df.loc[flagged_rows]

    flagged_df.to_csv("outputs/tickets_flagged.csv", index=False)


# 11) MAIN PROGRAM
def main():
    df = load_data()
    df = remove_duplicates(df)
    df = clean_text_columns(df)
    df = handle_missing_values(df)
    df = clean_dates(df)
    df = classify_issues(df)
    df = flag_tickets(df)

    summary = create_summary(df)

    write_report(summary)
    export_files(df)

    print("Program finished successfully.")


main()