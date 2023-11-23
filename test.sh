#!/bin/bash
cd tests

if [[ "$1" ]]; then
  if [[ "$1" =~ ^[0-9]+$ ]]; then
    filename=$(ls test_*.py | head -n $1 | tail -n 1)
    echo "Running test: $filename"
  else 
    if [[ "$1" =~ ^test_.*\.py$ ]]; then
      filename=$1
    else
      echo "Invalid argument: $1"
      echo "Usage: $0 [test_number|test_filename]"
      ls test_*.py | nl -s ') '
      exit 1
    fi
  fi
fi

if command -v coverage >/dev/null; then
  echo "Running tests with coverage"
  if [[ "$filename" ]]; then
    coverage run -m unittest $filename
  else
    coverage run -m unittest discover -s $(dirname $0)
  fi
  coverage report -m
  cd ..

  if [[ $(coverage report -m | tail -n 1 | awk '{print $4}' | tr -d '%') -lt 95 ]]; then

      if [[ -z "$filename" ]]; then
        echo "Coverage is less than 95%. Aborting..."
        exit 1
      fi
  fi
else
  echo "Running tests without coverage"
  python -m unittest discover -s $(dirname $0)

  if [[ -z "$filename" ]]; then
    echo "Coverage is not installed. Aborting..."
    exit 1
  fi
fi

