import csv
import os
import sys


def main(path):
    rate = float(os.environ.get("INVOICE_TAX_RATE", "0.08"))
    subtotal = 0.0
    with open(path) as f:
        for name, price, qty in csv.reader(f):
            line = float(price) * int(qty)
            subtotal += line
            print(f"{name:20s} {line:8.2f}")
    tax = subtotal * rate
    print(f"{'subtotal':20s} {subtotal:8.2f}")
    print(f"{'tax':20s} {tax:8.2f}")
    print(f"{'total':20s} {subtotal + tax:8.2f}")


if __name__ == "__main__":
    main(sys.argv[1])
