import csv
import json
import random
import argparse

system_instructions = (
    "You are a wind turbine technical support assistant. "
    "Given a Jira ticket summary and description, classify the ticket "
    "into the correct component category."
)


def build_records(input_csv: str, top_n: int) -> list[dict]:
    records = []
    with open(input_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= top_n:
                break
            user_content = f"{row['Summary'].strip()} {row['Description'].strip()}"
            assistant_content = row["component"].strip()
            records.append(
                {
                    "messages": [
                        {"role": "system", "content": system_instructions},
                        {"role": "user", "content": user_content},
                        {"role": "assistant", "content": assistant_content},
                    ]
                }
            )
    return records


def write_jsonl(records: list[dict], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")


def split_and_write(
    input_csv: str, top_n: int, train_pct: float, seed: int | None
) -> None:
    records = build_records(input_csv, top_n)
    random.seed(seed)
    random.shuffle(records)

    split_idx = int(len(records) * train_pct / 100)
    training = records[:split_idx]
    testing = records[split_idx:]

    write_jsonl(training, "training_set.jsonl")
    write_jsonl(testing, "testing_set.jsonl")

    print(
        f"Total: {len(records)} | "
        f"Training: {len(training)} ({train_pct}%) -> training_set.jsonl | "
        f"Testing: {len(testing)} ({100 - train_pct}%) -> testing_set.jsonl"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert top N rows from synthetic.csv to JSONL training/testing sets"
    )
    parser.add_argument(
        "-n", "--top-n", type=int, default=100,
        help="Number of rows to convert (default: 100)",
    )
    parser.add_argument(
        "-s", "--split", type=float, default=80,
        help="Training set percentage, e.g. 80 for 80/20 split (default: 80)",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for reproducible shuffling (default: 42)",
    )
    args = parser.parse_args()

    split_and_write("synthetic.csv", args.top_n, args.split, args.seed)
