def process(orders):
    print("starting")
    total = 0
    for o in orders:
        print("processing " + str(o))
        total += o
    print("done")
    return total


if __name__ == "__main__":
    process([1, 2, 3])
