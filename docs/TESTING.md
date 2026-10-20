# Testing Guide
Run `python -m unittest discover -s tests -v`. Tests cover the original five v0.1 behaviors plus v0.2 loop control, interpolation, property/index assignment, imports and diagnostic positions. GitHub Actions tests Python 3.9 through 3.13. Add one positive and one negative test for every grammar or runtime behavior change.
