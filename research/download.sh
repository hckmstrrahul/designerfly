#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p research/data research/results
curl --fail --location --retry 3 'https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/body-annotations-male-cns-v1.0-minconf-0.5.feather' --output research/data/annotations.feather
curl --fail --location --retry 3 'https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/connectome-weights-male-cns-v1.0-minconf-0.5.feather' --output research/data/weights.feather
# prepare.py verifies the exact source hashes before processing.
