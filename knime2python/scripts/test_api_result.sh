#!/usr/bin/env bash
curl -H "Content-Type: application/json" -X POST -d '@sample_api_request.json' http://localhost:5000/api/v1.0/results
