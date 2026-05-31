"""
Test for the anti-hallucination guard.

The whole point of Grounded Reader is that only VERIFIED claims reach the user.
A claim is verified only when its supporting quote genuinely appears in the
source. This test pins that behaviour down:

  - a real, word-for-word quote from the source must be KEPT
  - a fabricated quote the model could have invented must be REJECTED

If either of these ever fails, the guard is broken and the project's core
promise no longer holds.

Run:  python test_verify.py
"""

from main import verify_quote

SOURCE = (
    "This agreement may be terminated by either party. "
    "The notice period is thirty (30) days, given in writing. "
    "All disputes are governed by the laws of England and Wales."
)


def run() -> int:
    failures = []

    # 1. A real quote, copied verbatim from the source, must be KEPT.
    real_quote = "The notice period is thirty (30) days"
    if not verify_quote(SOURCE, real_quote):
        failures.append("REAL quote was rejected — the guard is dropping valid answers.")

    # 2. A real quote with messy spacing / casing must still be KEPT
    #    (the guard normalises whitespace and case on purpose).
    messy_real_quote = "the   NOTICE   period\nis  thirty (30) DAYS"
    if not verify_quote(SOURCE, messy_real_quote):
        failures.append("REAL quote with odd spacing/case was rejected — normalisation is broken.")

    # 3. A fabricated quote that is NOT in the source must be REJECTED.
    fake_quote = "The notice period is ninety (90) days"
    if verify_quote(SOURCE, fake_quote):
        failures.append("FABRICATED quote was accepted — the guard is letting hallucinations through.")

    # 4. An empty quote must be REJECTED (no quote = no proof).
    if verify_quote(SOURCE, ""):
        failures.append("EMPTY quote was accepted — a claim with no proof must never pass.")

    print("=" * 60)
    print("Grounded Reader — verification guard test")
    print("=" * 60)
    print(f'real quote      "{real_quote}"            -> kept     (expected kept)')
    print(f'messy real quote (odd spacing/case)       -> kept     (expected kept)')
    print(f'fabricated quote "{fake_quote}" -> rejected (expected rejected)')
    print(f'empty quote      ""                        -> rejected (expected rejected)')
    print("-" * 60)

    if failures:
        for f in failures:
            print("FAIL:", f)
        print("\nRESULT: FAILED")
        return 1

    print("RESULT: PASSED — real quotes kept, fabricated quotes rejected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
