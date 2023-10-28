#!/bin/bash

# if coverage is installed, use it
if command -v coverage >/dev/null; then
echo "Running tests with coverage"
  coverage run -m unittest discover -s $(dirname $0)
  coverage report -m

    # lets fail if coverage is less than 80%
    if [[ $(coverage report -m | tail -n 1 | awk '{print $4}' | tr -d '%') -lt 80 ]]; then
        echo "Coverage is less than 80%. Push aborted."
        exit 1
    fi

else
  echo "Running tests without coverage"
  python -m unittest discover -s $(dirname $0)
fi