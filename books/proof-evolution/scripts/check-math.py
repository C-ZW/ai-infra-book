#!/usr/bin/env python3
"""Recompute the book's nine canonical examples with standard-library arithmetic.

These checks are evidence for the stated calculations, not a proof assistant or
an audit of historical claims. The limit check separates its analytic argument
from finite regression examples. No network access or third-party package is used.
"""

import argparse
import json
from decimal import Decimal, localcontext
from fractions import Fraction
from math import isqrt
from pathlib import Path


def percentage(value, places):
    with localcontext() as context:
        context.prec = 60
        decimal = Decimal(value.numerator) / Decimal(value.denominator) * 100
        return f"{decimal:.{places}f}%"


def polynomial_product(left, right):
    result = [0] * (len(left) + len(right) - 1)
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            result[i + j] += a * b
    return result


def verify(outline_path):
    text = outline_path.read_text(encoding="utf-8")
    start = "<!-- BEGIN BASELINE -->\n"
    end = "<!-- END BASELINE -->"
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError("Canonical baseline markers must occur exactly once.")
    baseline = text.split(start, 1)[1].split(end, 1)[0]
    rows = {}
    for line in baseline.splitlines():
        if line.startswith("| "):
            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            if len(cells) == 3 and cells[0] not in {"ID", "---"}:
                if cells[0] in rows:
                    raise ValueError(f"Duplicate numerical example id: {cells[0]}")
                rows[cells[0]] = cells[1]
    expected_ids = {"ODD", "PRIME", "QUADRATIC", "LIMIT", "BAYES", "MULTIPLE", "INTERACTIVE", "PRIME_TEST", "APPROX"}
    if set(rows) != expected_ids:
        raise ValueError(f"Canonical example ids differ: {sorted(rows)}")
    checks = []

    def record(identifier, condition, result, required_fragments):
        if not condition:
            raise AssertionError(f"Arithmetic check failed: {identifier}")
        for fragment in required_fragments:
            if fragment not in rows[identifier]:
                raise AssertionError(f"Baseline drift for {identifier}: expected {fragment!r}")
        checks.append({"id": identifier, "pass": True, "result": result})

    odd_sum = sum(range(1, 10, 2))
    expanded_square = polynomial_product([1, 1], [1, 1])
    record("ODD", odd_sum == 25 and expanded_square == [1, 2, 1],
           {"first_five_sum": odd_sum, "induction_identity": "n² + (2n + 1) = (n + 1)²; both coefficient lists are [1, 2, 1]"},
           ["1 + 3 + 5 + 7 + 9 = 25", "positive integer n"])

    primes = [2, 3, 5, 7, 11, 13]
    product = 1
    for prime in primes:
        product *= prime
    constructed = product + 1
    record("PRIME", constructed == 30031 == 59 * 509 and all(constructed % prime == 1 for prime in primes),
           {"product_plus_one": constructed, "factors": [59, 509], "remainders_for_listed_primes": [constructed % prime for prime in primes]},
           ["30031 = 59 × 509", "need not produce a prime"])

    completed = polynomial_product([5, 1], [5, 1])
    completed[0] -= 64
    roots = [3, -13]
    record("QUADRATIC", completed == [-39, 10, 1] and all(root * root + 10 * root == 39 for root in roots),
           {"real_roots": roots, "positive_magnitude_root": 3, "polynomial_coefficients": completed},
           ["x² + 10x = 39", "(x + 5)² = 64", "3 and −13"])

    tested = 0
    for epsilon in [Fraction(1, 1000), Fraction(1, 10), Fraction(1), Fraction(5), Fraction(10), Fraction(100000)]:
        delta = min(Fraction(1), epsilon / 5)
        if not (0 < delta <= 1 and 5 * delta <= epsilon):
            raise AssertionError("The selected delta does not meet the analytic bound.")
        for step in range(-19, 20):
            if step == 0:
                continue
            x = 2 + delta * Fraction(step, 20)
            if not (0 < abs(x - 2) < delta and abs(x * x - 4) < epsilon):
                raise AssertionError("Limit regression example failed.")
            tested += 1
    record("LIMIT", tested == 228,
           {"analytic_argument": "δ ≤ 1 and |x − 2| < δ imply 1 < x < 3 and |x + 2| < 5; therefore |x² − 4| = |x − 2||x + 2| < 5δ ≤ ε.",
            "rational_regression_examples": tested, "qualification": "Finite regression examples are not a universal proof; the preceding inequality argument supplies that reasoning."},
           ["δ = min(1, ε/5)", "ε > 0", "0 < ∣x − 2∣ < δ"])

    population = 10000
    prevalence = Fraction(1, 100)
    sensitivity = Fraction(9, 10)
    false_positive_rate = Fraction(1, 20)
    true_positives = population * prevalence * sensitivity
    false_positives = population * (1 - prevalence) * false_positive_rate
    posterior = true_positives / (true_positives + false_positives)
    record("BAYES", true_positives == 90 and false_positives == 495 and posterior == Fraction(2, 13),
           {"expected_true_positives": int(true_positives), "expected_false_positives": int(false_positives), "posterior": str(posterior), "posterior_percent": percentage(posterior, 2)},
           ["10000", "prevalence 1%", "sensitivity 90%", "false-positive rate 5%", "90/585 = 2/13", "15.38%"])

    multiple = 1 - Fraction(19, 20) ** 20
    record("MULTIPLE", percentage(multiple, 2) == "64.15%",
           {"exact_probability": str(multiple), "percent": percentage(multiple, 2), "assumptions": "20 independent true-null tests; each has Type I error probability exactly 0.05."},
           ["20 independent true-null", "exactly 0.05", "1 − 0.95²⁰", "64.15%"])

    interactive = Fraction(1, 2) ** 20
    record("INTERACTIVE", interactive == Fraction(1, 1048576) and percentage(interactive, 8) == "0.00009537%",
           {"upper_bound": str(interactive), "percent": percentage(interactive, 8), "assumptions": "Each round has cheating probability at most 1/2 conditional on the prior transcript; the chain rule gives the repeated bound."},
           ["conditional on prior transcript", "20 times", "1/1048576", "0.00009537%"])

    # Exhaust the explicitly finite domain, without claiming an infinite theorem.
    def is_prime(value):
        return value > 1 and all(value % d for d in range(2, isqrt(value) + 1))

    prime_values = [n * n + n + 41 for n in range(40)]
    record("PRIME_TEST", all(map(is_prime, prime_values)) and 40 * 40 + 40 + 41 == 41 ** 2 == 1681,
           {"checked_inputs": "0 through 39 inclusive", "prime_count": len(prime_values),
            "last_checked_prime": prime_values[-1], "first_failure": {"n": 40, "value": 1681, "factors": [41, 41]}},
           ["n² + n + 41", "0 through 39", "1681 = 41²"])

    lower, upper = Fraction(1414, 1000), Fraction(1415, 1000)
    q = Fraction(30547, 21600)
    width = 2 / q - q
    record("APPROX", lower ** 2 == Fraction(1999396, 1000000) < 2 < Fraction(2002225, 1000000) == upper ** 2
           and upper - lower == Fraction(1, 1000)
           and q ** 2 == 2 - Fraction(791, 466560000)
           and width == Fraction(791, 659815200) < Fraction(12, 10000000)
           and 30 * q == 42 + Fraction(25, 60) + Fraction(35, 3600),
           {"elementary_bracket_width": "0.001", "scaled_by_30_width": "0.03",
            "tablet_fraction": str(q), "exact_squared_gap": str(2-q*q), "exact_bracket_width": str(width),
            "qualification": "Positive squaring is strictly increasing; q is a lower bound and 2/q is an upper bound. These are modern checks, not an inferred ancient procedure."},
           ["1.414² = 1.999396", "2.002225 = 1.415²", "30547/21600", "791/659815200"])

    return {"pass": True, "checks": checks,
            "limitations": ["Checks canonical calculations and required baseline wording; does not prove that every prose occurrence is semantically consistent.",
                            "Does not certify the historical narrative, empirical premises, cryptographic protocol security, or a theorem-prover kernel."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outline", type=Path, default=Path(__file__).resolve().parents[1] / "book-src/_meta/outline.md")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        report = verify(args.outline)
    except (OSError, ValueError, AssertionError) as error:
        report = {"pass": False, "errors": [str(error)]}
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("PASS: nine canonical mathematical checks." if report["pass"] else "FAIL: " + "; ".join(report["errors"]))
        if report["pass"]:
            for check in report["checks"]:
                print(f"  {check['id']}: {json.dumps(check['result'], ensure_ascii=False)}")
    raise SystemExit(0 if report["pass"] else 1)


if __name__ == "__main__":
    main()
